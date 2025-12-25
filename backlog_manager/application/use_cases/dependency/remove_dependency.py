"""Caso de uso para remover dependência."""
import logging

from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import StoryNotFoundException

logger = logging.getLogger(__name__)


class RemoveDependencyUseCase:
    """
    Caso de uso para remover dependência entre histórias.

    Responsabilidades:
    - Verificar que história existe
    - Remover dependência
    """

    def __init__(self, story_repository: StoryRepository):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
        """
        self._story_repository = story_repository

    def execute(self, story_id: str, dependency_id: str) -> None:
        """
        Remove dependência entre histórias.

        Args:
            story_id: ID da história
            dependency_id: ID da dependência a remover

        Raises:
            StoryNotFoundException: Se história não existe
        """
        logger.info(f"Removendo dependência: story_id='{story_id}', dependency_id='{dependency_id}'")

        # 1. Buscar história
        story = self._story_repository.find_by_id(story_id)

        if story is None:
            logger.error(f"História não encontrada: id='{story_id}'")
            raise StoryNotFoundException(story_id)

        logger.debug(f"História encontrada: id='{story_id}', dependências atuais: {story.dependencies}")

        # 2. Remover dependência (não falha se não existe)
        story.remove_dependency(dependency_id)
        logger.debug(f"Dependências após remoção: {story.dependencies}")

        # 3. Persistir
        self._story_repository.save(story)
        logger.info(f"Dependência removida: '{story_id}' não mais depende de '{dependency_id}'")
