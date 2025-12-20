"""Caso de uso para remover dependência."""
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import StoryNotFoundException


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
        # 1. Buscar história
        story = self._story_repository.find_by_id(story_id)

        if story is None:
            raise StoryNotFoundException(story_id)

        # 2. Remover dependência (não falha se não existe)
        story.remove_dependency(dependency_id)

        # 3. Persistir
        self._story_repository.save(story)
