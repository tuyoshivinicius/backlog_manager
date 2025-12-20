"""Caso de uso para importar backlog de Excel."""
from backlog_manager.application.dto.backlog_dto import BacklogDTO
from backlog_manager.application.dto.converters import story_to_dto
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.application.interfaces.services.excel_service import ExcelService


class ImportFromExcelUseCase:
    """
    Caso de uso para importar histórias de arquivo Excel.

    Responsabilidades:
    - Delegar leitura para ExcelService
    - Validar dados (feito pela entidade Story)
    - Gerar IDs sequenciais (US-001, US-002, ...)
    - Persistir histórias
    - Retornar BacklogDTO com histórias importadas
    """

    def __init__(self, story_repository: StoryRepository, excel_service: ExcelService):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            excel_service: Serviço de Excel (adaptor)
        """
        self._story_repository = story_repository
        self._excel_service = excel_service

    def execute(self, file_path: str, clear_existing: bool = False) -> BacklogDTO:
        """
        Importa histórias de arquivo Excel.

        Args:
            file_path: Caminho do arquivo Excel
            clear_existing: Se True, limpa backlog existente antes de importar

        Returns:
            BacklogDTO com histórias importadas

        Raises:
            FileNotFoundError: Se arquivo não existe
            ValueError: Se dados inválidos no Excel
        """
        # 1. Limpar backlog se solicitado
        if clear_existing:
            all_stories = self._story_repository.find_all()
            for story in all_stories:
                self._story_repository.delete(story.id)

        # 2. Delegar leitura para ExcelService
        # ExcelService retorna lista de Story já validadas
        imported_stories = self._excel_service.import_stories(file_path)

        # 3. Persistir todas histórias
        for story in imported_stories:
            self._story_repository.save(story)

        # 4. Calcular metadados
        total_sp = sum(s.story_point.value for s in imported_stories)

        # Calcular duração total (se datas preenchidas)
        if imported_stories and imported_stories[0].start_date and imported_stories[-1].end_date:
            first_start = imported_stories[0].start_date
            last_end = imported_stories[-1].end_date
            duration_days = (last_end - first_start).days + 1
        else:
            duration_days = 0

        # 5. Retornar BacklogDTO
        return BacklogDTO(
            stories=[story_to_dto(s) for s in imported_stories],
            total_count=len(imported_stories),
            total_story_points=total_sp,
            estimated_duration_days=duration_days,
        )
