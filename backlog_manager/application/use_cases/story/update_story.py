"""Caso de uso para atualizar história."""
from typing import Tuple

from backlog_manager.application.dto.converters import story_to_dto
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import StoryNotFoundException
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


class UpdateStoryUseCase:
    """
    Caso de uso para atualizar história existente.

    Responsabilidades:
    - Buscar história existente
    - Validar novos dados
    - Detectar mudanças que requerem recálculo de cronograma
    - Atualizar e persistir
    """

    def __init__(self, story_repository: StoryRepository):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
        """
        self._story_repository = story_repository

    def execute(self, story_id: str, updates: dict) -> Tuple[StoryDTO, bool]:
        """
        Atualiza história existente.

        Args:
            story_id: ID da história
            updates: Dicionário com campos a atualizar
                Campos possíveis: component, name, story_point, status,
                priority, developer_id, dependencies

        Returns:
            Tupla (StoryDTO atualizado, requer_recalculo: bool)

        Raises:
            StoryNotFoundException: Se história não existe
            ValueError: Se dados inválidos
        """
        # 1. Buscar história
        story = self._story_repository.find_by_id(story_id)
        if story is None:
            raise StoryNotFoundException(story_id)

        # 2. Verificar mudanças críticas que requerem recálculo
        requires_recalculation = False

        # 3. Atualizar campos
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
                story.dependencies = list(new_dependencies)
            requires_recalculation = True

        # 4. Persistir
        self._story_repository.save(story)

        # 5. Retornar (DTO, flag_recalculo)
        return story_to_dto(story), requires_recalculation
