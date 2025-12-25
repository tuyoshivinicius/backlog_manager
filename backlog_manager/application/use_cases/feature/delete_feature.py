"""Caso de uso para deletar feature."""
import logging

from backlog_manager.application.interfaces.repositories.feature_repository import FeatureRepository
from backlog_manager.domain.exceptions.domain_exceptions import FeatureHasStoriesException, FeatureNotFoundException

logger = logging.getLogger(__name__)


class DeleteFeatureUseCase:
    """
    Caso de uso para remover feature do sistema.

    Responsabilidades:
    - Verificar se feature existe
    - Verificar se feature não possui histórias associadas
    - Deletar feature
    """

    def __init__(self, feature_repository: FeatureRepository):
        """
        Inicializa caso de uso.

        Args:
            feature_repository: Repositório de features
        """
        self._feature_repository = feature_repository

    def execute(self, feature_id: str) -> None:
        """
        Remove feature do sistema.

        Args:
            feature_id: ID da feature a deletar

        Raises:
            FeatureNotFoundException: Se feature não existe
            FeatureHasStoriesException: Se feature possui histórias associadas
        """
        logger.info(f"Deletando feature: id='{feature_id}'")

        # 1. Verificar existência
        feature = self._feature_repository.find_by_id(feature_id)
        if feature is None:
            logger.error(f"Feature não encontrada: id='{feature_id}'")
            raise FeatureNotFoundException(feature_id)

        logger.debug(f"Feature encontrada: name='{feature.name}', wave={feature.wave}")

        # 2. Verificar se feature tem histórias
        story_count = self._feature_repository.count_stories_by_feature(feature_id)
        logger.debug(f"Feature possui {story_count} história(s)")

        if story_count > 0:
            logger.warning(
                f"Não é possível deletar feature '{feature.name}': "
                f"possui {story_count} história(s) associada(s)"
            )
            raise FeatureHasStoriesException(feature_id, feature.name, story_count)

        # 3. Deletar feature
        self._feature_repository.delete(feature_id)
        logger.info(f"Feature deletada: id='{feature_id}', name='{feature.name}'")
