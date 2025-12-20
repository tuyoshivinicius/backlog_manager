"""Implementação do Excel Service usando openpyxl."""
from datetime import date
from pathlib import Path
from typing import List

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from backlog_manager.application.interfaces.services.excel_service import ExcelService
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


class OpenpyxlExcelService(ExcelService):
    """
    Implementação do serviço de Excel usando openpyxl.

    Responsabilidades:
    - Importar histórias de planilha Excel
    - Exportar backlog para Excel com formatação
    - Validar formato e dados
    """

    # Colunas esperadas no import
    IMPORT_COLUMNS = ["Feature", "Nome", "StoryPoint"]

    # Colunas do export
    EXPORT_COLUMNS = [
        "Prioridade",
        "ID",
        "Feature",
        "Nome",
        "Status",
        "Desenvolvedor",
        "Dependências",
        "SP",
        "Início",
        "Fim",
        "Duração",
    ]

    def import_stories(self, filepath: str) -> List[StoryDTO]:
        """
        Importa histórias de arquivo Excel.

        Args:
            filepath: Caminho do arquivo .xlsx

        Returns:
            Lista de histórias importadas como DTOs

        Raises:
            FileNotFoundError: Se arquivo não existe
            ValueError: Se formato inválido ou dados inválidos
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

        workbook = load_workbook(filepath)
        sheet = workbook.active

        # Validar cabeçalho
        header = [cell.value for cell in sheet[1]]
        if header[:3] != self.IMPORT_COLUMNS:
            raise ValueError(
                f"Colunas inválidas. Esperado: {self.IMPORT_COLUMNS}, " f"Encontrado: {header[:3]}"
            )

        stories_dto = []
        errors = []

        # Processar linhas (pular cabeçalho)
        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            feature, name, story_point_value = row[:3]

            # Validar dados obrigatórios
            if not feature or not name or story_point_value is None:
                errors.append(f"Linha {row_num}: Dados obrigatórios faltando")
                continue

            # Validar Story Point
            try:
                sp_value = int(story_point_value)
                if sp_value not in [3, 5, 8, 13]:
                    raise ValueError("Story Point deve ser 3, 5, 8 ou 13")
            except (ValueError, TypeError) as e:
                errors.append(f"Linha {row_num}: Story Point inválido ({story_point_value})")
                continue

            # Gerar ID sequencial
            story_id = f"US-{len(stories_dto) + 1:03d}"

            # Criar DTO
            story_dto = StoryDTO(
                id=story_id,
                feature=str(feature).strip(),
                name=str(name).strip(),
                status="BACKLOG",
                priority=len(stories_dto) + 1,  # Prioridade sequencial
                developer_id=None,
                dependencies=[],
                story_point=sp_value,
                start_date=None,
                end_date=None,
                duration=None,
            )

            stories_dto.append(story_dto)

        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Erros na importação:\n{error_msg}")

        return stories_dto

    def export_backlog(self, filepath: str, stories: List[StoryDTO]) -> None:
        """
        Exporta histórias para arquivo Excel.

        Args:
            filepath: Caminho do arquivo .xlsx a criar
            stories: Lista de histórias a exportar (DTOs)
        """
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Backlog"

        # Escrever cabeçalho
        for col_num, column_name in enumerate(self.EXPORT_COLUMNS, start=1):
            cell = sheet.cell(row=1, column=col_num)
            cell.value = column_name
            cell.font = Font(bold=True, size=11)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Escrever dados
        for row_num, story in enumerate(stories, start=2):
            sheet.cell(row=row_num, column=1).value = story.priority
            sheet.cell(row=row_num, column=2).value = story.id
            sheet.cell(row=row_num, column=3).value = story.feature
            sheet.cell(row=row_num, column=4).value = story.name
            sheet.cell(row=row_num, column=5).value = story.status
            sheet.cell(row=row_num, column=6).value = story.developer_id or ""
            sheet.cell(row=row_num, column=7).value = ", ".join(story.dependencies) if story.dependencies else ""
            sheet.cell(row=row_num, column=8).value = story.story_point
            sheet.cell(row=row_num, column=9).value = story.start_date.strftime("%d/%m/%Y") if story.start_date else ""
            sheet.cell(row=row_num, column=10).value = story.end_date.strftime("%d/%m/%Y") if story.end_date else ""
            sheet.cell(row=row_num, column=11).value = story.duration or ""

        # Auto-ajustar largura das colunas
        for col_num in range(1, len(self.EXPORT_COLUMNS) + 1):
            column_letter = get_column_letter(col_num)
            max_length = 0

            for cell in sheet[column_letter]:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))

            sheet.column_dimensions[column_letter].width = min(max_length + 2, 50)

        # Adicionar bordas
        thin_border = Border(
            left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin")
        )

        for row in sheet.iter_rows(min_row=1, max_row=len(stories) + 1):
            for cell in row:
                cell.border = thin_border

        # Salvar arquivo
        workbook.save(filepath)
