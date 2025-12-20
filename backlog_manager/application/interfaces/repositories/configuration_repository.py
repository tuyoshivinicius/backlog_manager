"""Interface do repositório de configuração."""
from abc import ABC, abstractmethod

from backlog_manager.domain.entities.configuration import Configuration


class ConfigurationRepository(ABC):
    """
    Interface (Port) para repositório de configuração.

    Define o contrato para persistência da configuração global do sistema.
    Implementa padrão Singleton - apenas uma configuração existe.
    """

    @abstractmethod
    def get(self) -> Configuration:
        """
        Retorna configuração única do sistema.

        Se não existe, deve retornar configuração com valores padrão.

        Returns:
            Configuração do sistema
        """
        pass

    @abstractmethod
    def save(self, configuration: Configuration) -> None:
        """
        Salva configuração.

        Args:
            configuration: Configuração a ser salva
        """
        pass
