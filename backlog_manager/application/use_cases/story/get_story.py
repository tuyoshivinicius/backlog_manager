"""Caso de uso para buscar história por ID."""
import logging

from backlog_manager.application.dto.converters import story_to_dto
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import StoryNotFoundException

logger = logging.getLogger(__name__)


class GetStoryUseCase:
    """
    Caso de uso para buscar história específica por ID.

    Responsabilidades:
    - Buscar história por ID
    - Converter para DTO
    """

    def __init__(self, story_repository: StoryRepository):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
        """
        self._story_repository = story_repository

    def execute(self, story_id: str) -> StoryDTO:
        """
        Busca história por ID.

        Args:
            story_id: ID da história

        Returns:
            StoryDTO da história encontrada

        Raises:
            StoryNotFoundException: Se história não existe
        """
        logger.debug(f"Buscando história: id='{story_id}'")
        story = self._story_repository.find_by_id(story_id)

        if story is None:
            logger.error(f"História não encontrada: id='{story_id}'")
            raise StoryNotFoundException(story_id)

        logger.debug(f"História encontrada: id='{story_id}', name='{story.name}'")
        return story_to_dto(story)
