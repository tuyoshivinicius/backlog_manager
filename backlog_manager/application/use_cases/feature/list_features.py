"""Caso de uso para listar features."""
import logging
from typing import List

from backlog_manager.application.dto.converters import feature_to_dto
from backlog_manager.application.dto.feature_dto import FeatureDTO
from backlog_manager.application.interfaces.repositories.feature_repository import FeatureRepository

logger = logging.getLogger(__name__)


class ListFeaturesUseCase:
    """
    Caso de uso para listar todas as features.

    Responsabilidades:
    - Buscar todas features
    - Ordenar por onda (wave)
    - Converter para DTOs
    """

    def __init__(self, feature_repository: FeatureRepository):
        """
        Inicializa caso de uso.

        Args:
            feature_repository: Repositório de features
        """
        self._feature_repository = feature_repository

    def execute(self) -> List[FeatureDTO]:
        """
        Retorna todas as features ordenadas por onda.

        Returns:
            Lista de FeatureDTO ordenada por wave (crescente)
        """
        logger.debug("Listando todas as features")

        # 1. Buscar todas
        features = self._feature_repository.find_all()
        logger.debug(f"Encontradas {len(features)} features")

        # 2. Ordenar por wave
        features.sort(key=lambda f: f.wave)

        # 3. Converter para DTOs
        return [feature_to_dto(feature) for feature in features]
