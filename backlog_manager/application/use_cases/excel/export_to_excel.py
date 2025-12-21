"""Caso de uso para exportar backlog para Excel."""
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.application.interfaces.services.excel_service import ExcelService


class ExportToExcelUseCase:
    """
    Caso de uso para exportar backlog para arquivo Excel.

    Responsabilidades:
    - Buscar histórias ordenadas por prioridade
    - Delegar exportação para ExcelService
    - Retornar caminho do arquivo gerado
    """

    def __init__(self, excel_service: ExcelService, story_repository: StoryRepository):
        """
        Inicializa caso de uso.

        Args:
            excel_service: Serviço de Excel (adaptor)
            story_repository: Repositório de histórias
        """
        self._excel_service = excel_service
        self._story_repository = story_repository

    def execute(self, file_path: str) -> str:
        """
        Exporta backlog para arquivo Excel.

        Args:
            file_path: Caminho do arquivo Excel a ser criado

        Returns:
            Caminho do arquivo Excel gerado

        Raises:
            IOError: Se erro ao escrever arquivo
        """
        # 1. Buscar histórias ordenadas por prioridade
        all_stories = self._story_repository.find_all()
        sorted_stories = sorted(all_stories, key=lambda s: s.priority)

        # 2. Converter para DTOs
        from backlog_manager.application.dto.converters import story_to_dto
        stories_dto = [story_to_dto(story) for story in sorted_stories]

        # 3. Delegar exportação para ExcelService
        self._excel_service.export_backlog(file_path, stories_dto)

        # 4. Retornar caminho
        return file_path
