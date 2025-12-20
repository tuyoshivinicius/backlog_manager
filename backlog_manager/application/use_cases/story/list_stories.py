"""Caso de uso para listar histórias."""
from typing import List

from backlog_manager.application.dto.converters import story_to_dto
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository


class ListStoriesUseCase:
    """
    Caso de uso para listar todas as histórias.

    Responsabilidades:
    - Buscar todas histórias
    - Ordenar por prioridade
    - Converter para DTOs
    """

    def __init__(self, story_repository: StoryRepository):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
        """
        self._story_repository = story_repository

    def execute(self) -> List[StoryDTO]:
        """
        Retorna todas as histórias ordenadas por prioridade.

        Returns:
            Lista de StoryDTO ordenada por prioridade (menor = mais prioritário)
        """
        # 1. Buscar todas histórias
        stories = self._story_repository.find_all()

        # 2. Ordenar por prioridade
        stories.sort(key=lambda s: s.priority)

        # 3. Converter para DTOs
        return [story_to_dto(story) for story in stories]
