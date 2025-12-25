"""Caso de uso para deletar desenvolvedor."""
import logging

from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import DeveloperNotFoundException

logger = logging.getLogger(__name__)


class DeleteDeveloperUseCase:
    """
    Caso de uso para remover desenvolvedor do sistema.

    Responsabilidades:
    - Verificar se desenvolvedor existe
    - Remover alocação em histórias
    - Deletar desenvolvedor
    """

    def __init__(self, developer_repository: DeveloperRepository, story_repository: StoryRepository):
        """
        Inicializa caso de uso.

        Args:
            developer_repository: Repositório de desenvolvedores
            story_repository: Repositório de histórias
        """
        self._developer_repository = developer_repository
        self._story_repository = story_repository

    def execute(self, developer_id: str) -> None:
        """
        Remove desenvolvedor do sistema.

        Args:
            developer_id: ID do desenvolvedor a deletar

        Raises:
            DeveloperNotFoundException: Se desenvolvedor não existe
        """
        logger.info(f"Deletando desenvolvedor: id='{developer_id}'")

        # 1. Verificar existência
        if not self._developer_repository.exists(developer_id):
            logger.error(f"Desenvolvedor não encontrado: id='{developer_id}'")
            raise DeveloperNotFoundException(developer_id)

        # 2. Remover alocação em histórias
        all_stories = self._story_repository.find_all()
        deallocated_count = 0
        for story in all_stories:
            if story.developer_id == developer_id:
                logger.debug(f"Desalocando história: id='{story.id}'")
                story.deallocate_developer()
                self._story_repository.save(story)
                deallocated_count += 1

        logger.debug(f"Total de histórias desalocadas: {deallocated_count}")

        # 3. Deletar desenvolvedor
        self._developer_repository.delete(developer_id)
        logger.info(f"Desenvolvedor deletado: id='{developer_id}', histórias desalocadas: {deallocated_count}")
