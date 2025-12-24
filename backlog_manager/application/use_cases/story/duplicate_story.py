"""Caso de uso para duplicar história."""
from backlog_manager.application.dto.converters import story_to_dto
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.exceptions.domain_exceptions import StoryNotFoundException
from backlog_manager.domain.value_objects.story_status import StoryStatus


class DuplicateStoryUseCase:
    """
    Caso de uso para duplicar história existente.

    Responsabilidades:
    - Buscar história original
    - Copiar dados (exceto ID)
    - Gerar novo ID
    - Resetar campos (status, desenvolvedor, datas)
    - Persistir nova história
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
        Duplica história existente.

        Args:
            story_id: ID da história a duplicar

        Returns:
            StoryDTO da nova história criada

        Raises:
            StoryNotFoundException: Se história original não existe
        """
        # 1. Buscar original
        original = self._story_repository.find_by_id(story_id)
        if original is None:
            raise StoryNotFoundException(story_id)

        # 2. Gerar novo ID
        all_stories = self._story_repository.find_all()
        next_number = len(all_stories) + 1
        new_id = f"US-{next_number:03d}"

        # 3. Copiar dados e resetar campos
        new_story = Story(
            id=new_id,
            component=original.component,
            name=f"{original.name} (Cópia)",
            story_point=original.story_point,
            status=StoryStatus.BACKLOG,  # Resetar para BACKLOG
            priority=len(all_stories),  # Última posição
            developer_id=None,  # Remover desenvolvedor
            dependencies=original.dependencies.copy(),
            start_date=None,  # Limpar datas
            end_date=None,
            duration=None,
        )

        # 4. Persistir
        self._story_repository.save(new_story)

        # 5. Retornar DTO
        return story_to_dto(new_story)
