"""Caso de uso para criar feature."""
import logging

from backlog_manager.application.dto.converters import feature_to_dto
from backlog_manager.application.dto.feature_dto import FeatureDTO
from backlog_manager.application.interfaces.repositories.feature_repository import FeatureRepository
from backlog_manager.domain.entities.feature import Feature
from backlog_manager.domain.exceptions.domain_exceptions import DuplicateWaveException

logger = logging.getLogger(__name__)


class CreateFeatureUseCase:
    """
    Caso de uso para criar nova feature.

    Responsabilidades:
    - Validar nome
    - Gerar ID automático (3 primeiras letras maiúsculas)
    - Resolver conflitos de ID (FEA → FEA2 → FEA3)
    - Validar unicidade da onda
    - Criar e persistir feature
    """

    def __init__(self, feature_repository: FeatureRepository):
        """
        Inicializa caso de uso.

        Args:
            feature_repository: Repositório de features
        """
        self._feature_repository = feature_repository

    def execute(self, name: str, wave: int) -> FeatureDTO:
        """
        Cria nova feature.

        Args:
            name: Nome da feature (min 3 caracteres)
            wave: Número da onda (deve ser único e > 0)

        Returns:
            FeatureDTO criado

        Raises:
            ValueError: Se nome ou onda inválidos
            DuplicateWaveException: Se onda já existe
        """
        logger.info(f"Iniciando criação de feature: name='{name}', wave={wave}")

        # 1. Validar nome
        if not name or len(name.strip()) < 3:
            logger.error(f"Nome inválido: '{name}' (mínimo 3 caracteres)")
            raise ValueError("Nome da feature deve ter pelo menos 3 caracteres")

        name = name.strip()
        logger.debug(f"Nome validado: '{name}'")

        # 2. Validar onda
        if wave <= 0:
            logger.error(f"Onda inválida: {wave} (deve ser > 0)")
            raise ValueError("Onda deve ser um número positivo (> 0)")

        # 3. Verificar unicidade da onda
        existing_feature = self._feature_repository.find_by_wave(wave)
        if existing_feature:
            logger.warning(f"Onda {wave} já existe: feature='{existing_feature.name}'")
            raise DuplicateWaveException(wave, existing_feature.name)

        # 4. Gerar ID base (3 primeiras letras maiúsculas)
        base_id = name[:3].upper()
        logger.debug(f"ID base gerado: '{base_id}'")

        # 5. Resolver conflitos
        feature_id = base_id
        counter = 2

        while self._feature_repository.exists(feature_id):
            logger.debug(f"ID '{feature_id}' já existe, tentando próximo")
            feature_id = f"{base_id}{counter}"
            counter += 1

        logger.debug(f"ID final: '{feature_id}'")

        # 6. Criar entidade
        feature = Feature(id=feature_id, name=name, wave=wave)

        # 7. Persistir
        self._feature_repository.save(feature)
        logger.info(f"Feature criada: id='{feature_id}', name='{name}', wave={wave}")

        return feature_to_dto(feature)
