"""Interface do repositório de features."""
from abc import ABC, abstractmethod
from typing import List, Optional

from backlog_manager.domain.entities.feature import Feature


class FeatureRepository(ABC):
    """
    Interface (Port) para repositório de features.

    Define o contrato que a camada de infraestrutura deve implementar
    para persistência de features.
    """

    @abstractmethod
    def save(self, feature: Feature) -> None:
        """
        Salva ou atualiza uma feature.

        Args:
            feature: Feature a ser salva
        """
        pass

    @abstractmethod
    def find_by_id(self, feature_id: str) -> Optional[Feature]:
        """
        Busca feature por ID.

        Args:
            feature_id: ID da feature

        Returns:
            Feature encontrada ou None
        """
        pass

    @abstractmethod
    def find_by_wave(self, wave: int) -> Optional[Feature]:
        """
        Busca feature por número de onda.

        Args:
            wave: Número da onda

        Returns:
            Feature encontrada ou None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[Feature]:
        """
        Retorna todas as features ordenadas por onda (ASC).

        Returns:
            Lista de todas as features
        """
        pass

    @abstractmethod
    def delete(self, feature_id: str) -> None:
        """
        Remove uma feature.

        Args:
            feature_id: ID da feature a deletar
        """
        pass

    @abstractmethod
    def exists(self, feature_id: str) -> bool:
        """
        Verifica se feature existe.

        Args:
            feature_id: ID da feature

        Returns:
            True se existe, False caso contrário
        """
        pass

    @abstractmethod
    def wave_exists(self, wave: int) -> bool:
        """
        Verifica se já existe feature com determinada onda.

        Args:
            wave: Número da onda

        Returns:
            True se existe, False caso contrário
        """
        pass

    @abstractmethod
    def count_stories_by_feature(self, feature_id: str) -> int:
        """
        Conta quantas histórias estão associadas a uma feature.

        Args:
            feature_id: ID da feature

        Returns:
            Número de histórias associadas
        """
        pass
