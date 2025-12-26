"""Interface do repositório de histórias."""
from abc import ABC, abstractmethod
from typing import List, Optional

from backlog_manager.domain.entities.story import Story


class StoryRepository(ABC):
    """
    Interface (Port) para repositório de histórias.

    Define o contrato que a camada de infraestrutura deve implementar
    para persistência de histórias.
    """

    @abstractmethod
    def save(self, story: Story) -> None:
        """
        Salva ou atualiza uma história.

        Args:
            story: História a ser salva
        """
        pass

    @abstractmethod
    def find_by_id(self, story_id: str) -> Optional[Story]:
        """
        Busca história por ID.

        Args:
            story_id: ID da história

        Returns:
            História encontrada ou None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[Story]:
        """
        Retorna todas as histórias.

        Returns:
            Lista de todas as histórias
        """
        pass

    @abstractmethod
    def delete(self, story_id: str) -> None:
        """
        Remove uma história.

        Args:
            story_id: ID da história a deletar
        """
        pass

    @abstractmethod
    def exists(self, story_id: str) -> bool:
        """
        Verifica se história existe.

        Args:
            story_id: ID da história

        Returns:
            True se existe, False caso contrário
        """
        pass

    @abstractmethod
    def load_feature(self, story: Story) -> None:
        """
        Carrega a feature associada à história.

        Args:
            story: História para carregar a feature
        """
        pass

    @abstractmethod
    def save_batch(self, stories: List[Story]) -> None:
        """
        Salva múltiplas histórias em uma única transação.

        Mais eficiente que chamar save() repetidamente.

        Args:
            stories: Lista de histórias a serem salvas
        """
        pass
