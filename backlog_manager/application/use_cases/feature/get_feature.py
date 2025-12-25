"""Caso de uso para obter feature por ID."""
import logging

from backlog_manager.application.dto.converters import feature_to_dto
from backlog_manager.application.dto.feature_dto import FeatureDTO
from backlog_manager.application.interfaces.repositories.feature_repository import FeatureRepository
from backlog_manager.domain.exceptions.domain_exceptions import FeatureNotFoundException

logger = logging.getLogger(__name__)


class GetFeatureUseCase:
    """
    Caso de uso para buscar feature por ID.

    Responsabilidades:
    - Buscar feature por ID
    - Converter para DTO
    """

    def __init__(self, feature_repository: FeatureRepository):
        """
        Inicializa caso de uso.

        Args:
            feature_repository: Repositório de features
        """
        self._feature_repository = feature_repository

    def execute(self, feature_id: str) -> FeatureDTO:
        """
        Busca feature por ID.

        Args:
            feature_id: ID da feature

        Returns:
            FeatureDTO encontrado

        Raises:
            FeatureNotFoundException: Se feature não existe
        """
        logger.debug(f"Buscando feature: id='{feature_id}'")

        feature = self._feature_repository.find_by_id(feature_id)

        if feature is None:
            logger.error(f"Feature não encontrada: id='{feature_id}'")
            raise FeatureNotFoundException(feature_id)

        logger.debug(f"Feature encontrada: id='{feature_id}', name='{feature.name}', wave={feature.wave}")

        return feature_to_dto(feature)
