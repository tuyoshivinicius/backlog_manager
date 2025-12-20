"""Interface do repositório de desenvolvedores."""
from abc import ABC, abstractmethod
from typing import List, Optional

from backlog_manager.domain.entities.developer import Developer


class DeveloperRepository(ABC):
    """
    Interface (Port) para repositório de desenvolvedores.

    Define o contrato que a camada de infraestrutura deve implementar
    para persistência de desenvolvedores.
    """

    @abstractmethod
    def save(self, developer: Developer) -> None:
        """
        Salva ou atualiza um desenvolvedor.

        Args:
            developer: Desenvolvedor a ser salvo
        """
        pass

    @abstractmethod
    def find_by_id(self, developer_id: str) -> Optional[Developer]:
        """
        Busca desenvolvedor por ID.

        Args:
            developer_id: ID do desenvolvedor

        Returns:
            Desenvolvedor encontrado ou None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[Developer]:
        """
        Retorna todos os desenvolvedores.

        Returns:
            Lista de todos os desenvolvedores
        """
        pass

    @abstractmethod
    def delete(self, developer_id: str) -> None:
        """
        Remove um desenvolvedor.

        Args:
            developer_id: ID do desenvolvedor a deletar
        """
        pass

    @abstractmethod
    def exists(self, developer_id: str) -> bool:
        """
        Verifica se desenvolvedor existe.

        Args:
            developer_id: ID do desenvolvedor

        Returns:
            True se existe, False caso contrário
        """
        pass

    @abstractmethod
    def id_is_available(self, developer_id: str) -> bool:
        """
        Verifica se ID está disponível para uso.

        Args:
            developer_id: ID a verificar

        Returns:
            True se disponível, False caso contrário
        """
        pass
