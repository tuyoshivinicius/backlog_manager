"""Caso de uso para atualizar feature."""
import logging
from typing import List

from backlog_manager.application.dto.converters import feature_to_dto
from backlog_manager.application.dto.feature_dto import FeatureDTO
from backlog_manager.application.interfaces.repositories.feature_repository import FeatureRepository
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import DuplicateWaveException, FeatureNotFoundException
from backlog_manager.domain.services.wave_dependency_validator import WaveDependencyValidator

logger = logging.getLogger(__name__)


class UpdateFeatureUseCase:
    """
    Caso de uso para atualizar feature existente.

    Responsabilidades:
    - Verificar se feature existe
    - Validar nome e onda
    - Se onda mudou, validar contra dependências de todas as histórias da feature
    - Verificar unicidade da nova onda
    - Atualizar e persistir feature
    """

    def __init__(
        self,
        feature_repository: FeatureRepository,
        story_repository: StoryRepository,
        wave_validator: WaveDependencyValidator,
    ):
        """
        Inicializa caso de uso.

        Args:
            feature_repository: Repositório de features
            story_repository: Repositório de histórias
            wave_validator: Validador de dependências de onda
        """
        self._feature_repository = feature_repository
        self._story_repository = story_repository
        self._wave_validator = wave_validator

    def execute(self, feature_id: str, name: str, wave: int) -> FeatureDTO:
        """
        Atualiza feature existente.

        Args:
            feature_id: ID da feature a atualizar
            name: Novo nome
            wave: Nova onda

        Returns:
            FeatureDTO atualizado

        Raises:
            FeatureNotFoundException: Se feature não existe
            ValueError: Se nome ou onda inválidos
            DuplicateWaveException: Se nova onda já existe em outra feature
            InvalidWaveDependencyException: Se mudança de onda violar regras de dependência
        """
        logger.info(f"Atualizando feature: id='{feature_id}', name='{name}', wave={wave}")

        # 1. Verificar existência
        feature = self._feature_repository.find_by_id(feature_id)
        if feature is None:
            logger.error(f"Feature não encontrada: id='{feature_id}'")
            raise FeatureNotFoundException(feature_id)

        logger.debug(f"Feature encontrada: name='{feature.name}', wave={feature.wave}")

        # 2. Validar nome
        if not name or len(name.strip()) < 3:
            logger.error(f"Nome inválido: '{name}' (mínimo 3 caracteres)")
            raise ValueError("Nome da feature deve ter pelo menos 3 caracteres")

        name = name.strip()

        # 3. Validar onda
        if wave <= 0:
            logger.error(f"Onda inválida: {wave} (deve ser > 0)")
            raise ValueError("Onda deve ser um número positivo (> 0)")

        # 4. Se onda mudou, validar
        if wave != feature.wave:
            logger.debug(f"Mudança de onda detectada: {feature.wave} -> {wave}")

            # 4.1. Verificar unicidade da nova onda
            existing_feature = self._feature_repository.find_by_wave(wave)
            if existing_feature and existing_feature.id != feature_id:
                logger.warning(f"Onda {wave} já existe: feature='{existing_feature.name}'")
                raise DuplicateWaveException(wave, existing_feature.name)

            # 4.2. Validar contra dependências de todas as histórias da feature
            stories = self._story_repository.find_by_feature_id(feature_id)
            logger.debug(f"Validando dependências de {len(stories)} histórias da feature")

            for story in stories:
                # Buscar dependências da história
                dependencies: List = []
                for dep_id in story.dependencies:
                    dep = self._story_repository.find_by_id(dep_id)
                    if dep:
                        dependencies.append(dep)

                # Buscar histórias que dependem desta
                all_stories = self._story_repository.find_all()
                dependents = [s for s in all_stories if story.id in s.dependencies]

                logger.debug(
                    f"Validando história '{story.id}': "
                    f"{len(dependencies)} dependências, {len(dependents)} dependentes"
                )

                # Validar mudança de onda
                self._wave_validator.validate_wave_change(story, wave, dependencies, dependents)

            logger.debug("Validação de dependências concluída")

        # 5. Atualizar feature
        old_name, old_wave = feature.name, feature.wave
        feature.name = name
        feature.wave = wave
        logger.debug(f"Atualizando: name '{old_name}' -> '{name}', wave {old_wave} -> {wave}")

        # 6. Persistir
        self._feature_repository.save(feature)
        logger.info(f"Feature atualizada: id='{feature_id}', name='{name}', wave={wave}")

        return feature_to_dto(feature)
