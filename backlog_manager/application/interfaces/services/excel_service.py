"""Interface do serviço de Excel."""
from abc import ABC, abstractmethod
from typing import List

from backlog_manager.application.dto.story_dto import StoryDTO


class ExcelService(ABC):
    """
    Interface (Port) para serviço de import/export Excel.

    Define o contrato para operações de importação e exportação
    de histórias em arquivos Excel.
    """

    @abstractmethod
    def import_stories(self, filepath: str) -> List[StoryDTO]:
        """
        Importa histórias de arquivo Excel.

        Args:
            filepath: Caminho do arquivo Excel

        Returns:
            Lista de StoryDTO importados

        Raises:
            FileNotFoundError: Se arquivo não existe
            ValueError: Se formato inválido
        """
        pass

    @abstractmethod
    def export_backlog(self, filepath: str, stories: List[StoryDTO]) -> None:
        """
        Exporta backlog para arquivo Excel.

        Args:
            filepath: Caminho do arquivo de destino
            stories: Lista de StoryDTO para exportar

        Raises:
            PermissionError: Se sem permissão de escrita
        """
        pass
