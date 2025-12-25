"""Caso de uso para criar história."""
import logging

from backlog_manager.application.dto.converters import story_to_dto
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.application.interfaces.repositories.feature_repository import FeatureRepository
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.exceptions.domain_exceptions import FeatureNotFoundException
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus

logger = logging.getLogger(__name__)


class CreateStoryUseCase:
    """
    Caso de uso para criar nova história.

    Responsabilidades:
    - Validar que feature existe
    - Gerar ID automático baseado na component (ex: S1, S2 para "Solicitação")
    - Definir prioridade inicial (última posição)
    - Criar e persistir história
    """

    def __init__(self, story_repository: StoryRepository, feature_repository: FeatureRepository):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            feature_repository: Repositório de features
        """
        self._story_repository = story_repository
        self._feature_repository = feature_repository

    def execute(self, story_data: dict) -> StoryDTO:
        """
        Cria nova história.

        Args:
            story_data: Dicionário com dados da história
                - component: str (obrigatório)
                - name: str (obrigatório)
                - story_point: int (3, 5, 8 ou 13)
                - feature_id: str (obrigatório)
                - dependencies: List[str] (opcional)

        Returns:
            StoryDTO da história criada

        Raises:
            ValueError: Se dados inválidos ou story point inválido
            FeatureNotFoundException: Se feature não existe
        """
        logger.info(f"Iniciando criação de história: component='{story_data.get('component')}', name='{story_data.get('name')}'")
        logger.debug(f"Parâmetros: {story_data}")

        # 1. Validar que feature existe (se fornecido)
        feature_id = story_data.get("feature_id")
        if feature_id:
            logger.debug(f"Validando feature: id='{feature_id}'")
            feature = self._feature_repository.find_by_id(feature_id)
            if feature is None:
                logger.error(f"Feature não encontrada: id='{feature_id}'")
                raise FeatureNotFoundException(feature_id)
            logger.debug(f"Feature validada: '{feature.name}'")

        # 2. Gerar ID baseado na component (primeira letra + número incremental)
        all_stories = self._story_repository.find_all()
        logger.debug(f"Total de histórias existentes: {len(all_stories)}")

        # Obter primeira letra da component (maiúscula)
        component = story_data["component"].strip()
        if not component:
            logger.error("Component vazia fornecida")
            raise ValueError("Component não pode ser vazia")

        prefix = component[0].upper()
        logger.debug(f"Prefixo do ID: '{prefix}'")

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
        logger.debug(f"ID gerado: '{story_id}' (próximo número: {next_number})")

        # 3. Determinar prioridade (última posição)
        priority = len(all_stories)
        logger.debug(f"Prioridade definida: {priority} (última posição)")

        # 4. Criar entidade Story
        story = Story(
            id=story_id,
            component=story_data["component"],
            name=story_data["name"],
            story_point=StoryPoint(story_data["story_point"]),
            feature_id=feature_id,
            status=StoryStatus.BACKLOG,
            priority=priority,
            dependencies=story_data.get("dependencies", []),
        )

        # 5. Persistir
        logger.debug(f"Persistindo história: id='{story_id}'")
        self._story_repository.save(story)

        # 6. Carregar feature para DTO
        self._story_repository.load_feature(story)

        # 7. Retornar DTO
        logger.info(f"História criada: id='{story_id}', priority={priority}, story_points={story.story_point.value}")
        return story_to_dto(story)
