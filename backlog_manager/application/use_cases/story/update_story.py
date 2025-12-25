"""Caso de uso para atualizar história."""
import logging
from typing import List, Tuple

from backlog_manager.application.dto.converters import story_to_dto
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.application.interfaces.repositories.feature_repository import FeatureRepository
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import FeatureNotFoundException, StoryNotFoundException
from backlog_manager.domain.services.wave_dependency_validator import WaveDependencyValidator
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus

logger = logging.getLogger(__name__)


class UpdateStoryUseCase:
    """
    Caso de uso para atualizar história existente.

    Responsabilidades:
    - Buscar história existente
    - Validar novos dados
    - Se feature_id mudar, validar regras de dependência de onda
    - Detectar mudanças que requerem recálculo de cronograma
    - Atualizar e persistir
    """

    def __init__(
        self,
        story_repository: StoryRepository,
        feature_repository: FeatureRepository,
        wave_validator: WaveDependencyValidator,
    ):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            feature_repository: Repositório de features
            wave_validator: Validador de dependências de onda
        """
        self._story_repository = story_repository
        self._feature_repository = feature_repository
        self._wave_validator = wave_validator

    def execute(self, story_id: str, updates: dict) -> Tuple[StoryDTO, bool]:
        """
        Atualiza história existente.

        Args:
            story_id: ID da história
            updates: Dicionário com campos a atualizar
                Campos possíveis: component, name, story_point, status,
                priority, developer_id, dependencies, feature_id

        Returns:
            Tupla (StoryDTO atualizado, requer_recalculo: bool)

        Raises:
            StoryNotFoundException: Se história não existe
            FeatureNotFoundException: Se nova feature não existe
            InvalidWaveDependencyException: Se mudança de feature violar regras de onda
            ValueError: Se dados inválidos
        """
        logger.info(f"Iniciando atualização de história: id='{story_id}'")
        logger.debug(f"Campos a atualizar: {list(updates.keys())}")

        # 1. Buscar história
        story = self._story_repository.find_by_id(story_id)
        if story is None:
            logger.error(f"História não encontrada: id='{story_id}'")
            raise StoryNotFoundException(story_id)

        # Carregar feature atual
        self._story_repository.load_feature(story)
        logger.debug(f"História encontrada: name='{story.name}', feature='{story.feature_id}'")

        # 2. Verificar mudanças críticas que requerem recálculo
        requires_recalculation = False

        # 3. Se feature_id mudou, validar wave
        if "feature_id" in updates:
            new_feature_id = updates["feature_id"]

            # Converter "(Nenhuma)" ou string vazia em None
            if new_feature_id == "(Nenhuma)" or not new_feature_id or new_feature_id.strip() == "":
                new_feature_id = None

            logger.debug(f"Mudança de feature detectada: '{story.feature_id}' -> '{new_feature_id}'")

            # Se new_feature_id é None, permitir (história sem feature)
            if new_feature_id is None:
                logger.debug("Removendo associação com feature")
                story.feature_id = None
                requires_recalculation = True
            else:
                # Validar que nova feature existe
                new_feature = self._feature_repository.find_by_id(new_feature_id)
                if new_feature is None:
                    logger.error(f"Nova feature não encontrada: id='{new_feature_id}'")
                    raise FeatureNotFoundException(new_feature_id)

                # Se feature mudou, validar onda
                if new_feature_id != story.feature_id:
                    old_wave = story.wave
                    new_wave = new_feature.wave
                    logger.debug(f"Mudança de onda: {old_wave} -> {new_wave}")

                    # Se onda mudou, validar dependências
                    if new_wave != old_wave:
                        logger.debug("Validando regras de dependência de onda")

                        # Buscar dependências da história
                        # IMPORTANTE: Ignorar dependências sem feature (wave 0)
                        dependencies: List = []
                        for dep_id in story.dependencies:
                            dep = self._story_repository.find_by_id(dep_id)
                            if dep:
                                self._story_repository.load_feature(dep)
                                # Ignorar histórias sem feature associada
                                if dep.feature_id is not None:
                                    dependencies.append(dep)
                                else:
                                    logger.debug(f"Ignorando dependência '{dep_id}' sem feature na validação")

                        # Buscar histórias que dependem desta
                        # IMPORTANTE: Ignorar dependentes sem feature (wave 0)
                        all_stories = self._story_repository.find_all()
                        dependents = []
                        for s in all_stories:
                            if story_id in s.dependencies:
                                self._story_repository.load_feature(s)
                                # Ignorar histórias sem feature associada
                                if s.feature_id is not None:
                                    dependents.append(s)
                                else:
                                    logger.debug(f"Ignorando dependente '{s.id}' sem feature na validação")

                        logger.debug(f"Validando com {len(dependencies)} dependências e {len(dependents)} dependentes")

                        # Validar mudança de onda
                        self._wave_validator.validate_wave_change(story, new_wave, dependencies, dependents)
                        logger.debug("Validação de onda bem-sucedida")

                    # Atualizar feature_id
                    story.feature_id = new_feature_id
                    requires_recalculation = True

        # 4. Atualizar campos
        if "component" in updates:
            story.component = updates["component"]

        if "name" in updates:
            story.name = updates["name"]

        if "story_point" in updates:
            story.story_point = StoryPoint(updates["story_point"])
            requires_recalculation = True

        if "status" in updates:
            story.status = StoryStatus.from_string(updates["status"])

        if "priority" in updates:
            story.priority = updates["priority"]
            requires_recalculation = True

        if "developer_id" in updates:
            if updates["developer_id"] is None:
                story.deallocate_developer()
            else:
                story.allocate_developer(updates["developer_id"])
            requires_recalculation = True

        if "dependencies" in updates:
            # Atualizar dependências da história
            new_dependencies = updates["dependencies"]
            if isinstance(new_dependencies, list):
                # Substituir lista completa de dependências
                logger.debug(f"Atualizando dependências: {new_dependencies}")
                story.dependencies = list(new_dependencies)
            requires_recalculation = True

        # 5. Persistir
        logger.debug(f"Persistindo história atualizada: id='{story_id}'")
        self._story_repository.save(story)

        # 6. Carregar feature para DTO
        self._story_repository.load_feature(story)

        # 7. Retornar (DTO, flag_recalculo)
        logger.info(f"História atualizada: id='{story_id}', requer_recalculo={requires_recalculation}")
        return story_to_dto(story), requires_recalculation
