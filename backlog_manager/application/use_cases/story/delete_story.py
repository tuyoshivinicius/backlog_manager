"""Caso de uso para deletar história."""
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import StoryNotFoundException


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
        # 1. Verificar existência
        if not self._story_repository.exists(story_id):
            raise StoryNotFoundException(story_id)

        # 2. Remover de dependências de outras histórias
        all_stories = self._story_repository.find_all()
        for story in all_stories:
            if story.has_dependency(story_id):
                story.remove_dependency(story_id)
                self._story_repository.save(story)

        # 3. Deletar história
        self._story_repository.delete(story_id)
