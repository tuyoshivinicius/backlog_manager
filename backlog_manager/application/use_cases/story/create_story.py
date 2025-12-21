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
    - Gerar ID automático baseado na feature (ex: S1, S2 para "Solicitação")
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
        # 1. Gerar ID baseado na feature (primeira letra + número incremental)
        all_stories = self._story_repository.find_all()

        # Obter primeira letra da feature (maiúscula)
        feature = story_data["feature"].strip()
        if not feature:
            raise ValueError("Feature não pode ser vazia")

        prefix = feature[0].upper()

        # Encontrar maior número com o mesmo prefixo
        max_number = 0
        for story in all_stories:
            if story.id.startswith(prefix) and len(story.id) > 1:
                try:
                    # Extrair número do ID (ex: S1 -> 1, S10 -> 10)
                    number_part = story.id[1:]
                    number = int(number_part)
                    if number > max_number:
                        max_number = number
                except ValueError:
                    # Ignorar IDs que não seguem o padrão
                    continue

        # Gerar próximo ID
        next_number = max_number + 1
        story_id = f"{prefix}{next_number}"

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
