"""Interface do serviço de Excel."""
from abc import ABC, abstractmethod
from typing import List, Tuple, Set, Optional

from backlog_manager.application.dto.story_dto import StoryDTO


class ExcelService(ABC):
    """
    Interface (Port) para serviço de import/export Excel.

    Define o contrato para operações de importação e exportação
    de histórias em arquivos Excel.
    """

    @abstractmethod
    def import_stories(
        self,
        filepath: str,
        existing_ids: Optional[Set[str]] = None
    ) -> Tuple[List[StoryDTO], dict]:
        """
        Importa histórias de arquivo Excel.

        Args:
            filepath: Caminho do arquivo Excel
            existing_ids: IDs de histórias já existentes no banco (para validação)

        Returns:
            Tupla contendo:
            - Lista de StoryDTO importados (válidos)
            - Dicionário com estatísticas da importação:
                {
                    "total_processadas": int,       # Total de linhas processadas
                    "total_importadas": int,        # Histórias válidas importadas
                    "ignoradas_duplicadas": int,    # IDs duplicados na planilha
                    "ignoradas_existentes": int,    # IDs já existem no banco
                    "ignoradas_invalidas": int,     # Dados inválidos
                    "deps_ignoradas": int,          # Dependências inválidas removidas
                    "warnings": List[str]           # Lista de avisos/erros
                }

        Raises:
            FileNotFoundError: Se arquivo não existe
            ValueError: Se formato inválido (cabeçalho incorreto)
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
