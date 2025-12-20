"""Caso de uso para criar história."""
from backlog_manager.application.dto.converters import story_to_dto
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


class CreateStoryUseCase:
    """
    Caso de uso para criar nova história.

    Responsabilidades:
    - Gerar ID automático sequencial (US-001, US-002, etc)
    - Definir prioridade inicial (última posição)
    - Criar e persistir história
    """

    def __init__(self, story_repository: StoryRepository):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
        """
        self._story_repository = story_repository

    def execute(self, story_data: dict) -> StoryDTO:
        """
        Cria nova história.

        Args:
            story_data: Dicionário com dados da história
                - feature: str (obrigatório)
                - name: str (obrigatório)
                - story_point: int (3, 5, 8 ou 13)
                - dependencies: List[str] (opcional)

        Returns:
            StoryDTO da história criada

        Raises:
            ValueError: Se dados inválidos ou story point inválido
        """
        # 1. Gerar ID sequencial
        all_stories = self._story_repository.find_all()
        next_number = len(all_stories) + 1
        story_id = f"US-{next_number:03d}"

        # 2. Determinar prioridade (última posição)
        priority = len(all_stories)

        # 3. Criar entidade Story
        story = Story(
            id=story_id,
            feature=story_data["feature"],
            name=story_data["name"],
            story_point=StoryPoint(story_data["story_point"]),
            status=StoryStatus.BACKLOG,
            priority=priority,
            dependencies=story_data.get("dependencies", []),
        )

        # 4. Persistir
        self._story_repository.save(story)

        # 5. Retornar DTO
        return story_to_dto(story)
