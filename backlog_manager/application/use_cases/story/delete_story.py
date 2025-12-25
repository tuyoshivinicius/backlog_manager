"""Caso de uso para deletar história."""
import logging

from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import StoryNotFoundException

logger = logging.getLogger(__name__)


class DeleteStoryUseCase:
    """
    Caso de uso para remover história do sistema.

    Responsabilidades:
    - Verificar se história existe
    - Remover referências de dependências em outras histórias
    - Deletar história
    """

    def __init__(self, story_repository: StoryRepository):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
        """
        self._story_repository = story_repository

    def execute(self, story_id: str) -> None:
        """
        Remove história do sistema.

        Args:
            story_id: ID da história a deletar

        Raises:
            StoryNotFoundException: Se história não existe
        """
        logger.info(f"Iniciando deleção de história: id='{story_id}'")

        # 1. Verificar existência
        if not self._story_repository.exists(story_id):
            logger.error(f"História não encontrada para deleção: id='{story_id}'")
            raise StoryNotFoundException(story_id)

        # 2. Remover de dependências de outras histórias
        logger.debug("Removendo referências de dependências em outras histórias")
        all_stories = self._story_repository.find_all()
        cleaned_count = 0
        for story in all_stories:
            if story.has_dependency(story_id):
                logger.debug(f"Removendo dependência de '{story_id}' em '{story.id}'")
                story.remove_dependency(story_id)
                self._story_repository.save(story)
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Removidas {cleaned_count} referências de dependência")

        # 3. Deletar história
        logger.debug(f"Deletando história: id='{story_id}'")
        self._story_repository.delete(story_id)
        logger.info(f"História deletada com sucesso: id='{story_id}'")
