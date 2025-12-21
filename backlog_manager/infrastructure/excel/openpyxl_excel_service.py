"""Implementação do Excel Service usando openpyxl."""
from datetime import date
from pathlib import Path
from typing import Any, List, Tuple, Set, Optional

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
    - Importar histórias de planilha Excel (5 colunas: ID, Feature, Nome, StoryPoint, Deps)
    - Exportar backlog para Excel com formatação
    - Validar formato e dados
    - Detectar e ignorar IDs duplicados
    - Processar dependências
    """

    # Colunas esperadas no import (NOVO: 5 colunas)
    IMPORT_COLUMNS = ["ID", "Feature", "Nome", "StoryPoint", "Deps"]

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

    def import_stories(
        self,
        filepath: str,
        existing_ids: Optional[Set[str]] = None
    ) -> Tuple[List[StoryDTO], dict]:
        """
        Importa histórias de arquivo Excel (5 colunas: ID, Feature, Nome, StoryPoint, Deps).

        Args:
            filepath: Caminho do arquivo .xlsx
            existing_ids: IDs de histórias já existentes no banco

        Returns:
            Tupla (stories_dto, stats) onde:
            - stories_dto: Lista de histórias válidas importadas
            - stats: Estatísticas da importação

        Raises:
            FileNotFoundError: Se arquivo não existe
            ValueError: Se formato inválido (cabeçalho incorreto)
        """
        if existing_ids is None:
            existing_ids = set()

        if not Path(filepath).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

        workbook = load_workbook(filepath)
        sheet = workbook.active

        # Validar cabeçalho (deve ter exatamente 5 colunas)
        header = [cell.value for cell in sheet[1]][:5]
        if header != self.IMPORT_COLUMNS:
            raise ValueError(
                f"Layout inválido. Esperado: {self.IMPORT_COLUMNS}, "
                f"Encontrado: {header}"
            )

        # Inicializar estatísticas
        stats: dict[str, Any] = {
            "total_processadas": 0,
            "total_importadas": 0,
            "ignoradas_duplicadas": 0,
            "ignoradas_invalidas": 0,
            "deps_ignoradas": 0,
            "warnings": []
        }

        temp_stories = []  # Lista temporária: (story_id, story_dto, row_num)
        id_counts: dict[str, int] = {}     # Mapear ID → contagem de ocorrências
        generated_id_counter = 1

        # FASE 1: Processar todas as linhas e detectar duplicatas
        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            stats["total_processadas"] += 1

            # Extrair valores das 5 colunas
            id_value, feature, name, sp_value, deps_value = row[:5]

            # Validar campos obrigatórios (Feature e Nome)
            if not feature or str(feature).strip() == "":
                stats["ignoradas_invalidas"] += 1
                stats["warnings"].append(f"Linha {row_num}: Feature vazio - linha ignorada")
                continue

            if not name or str(name).strip() == "":
                stats["ignoradas_invalidas"] += 1
                stats["warnings"].append(f"Linha {row_num}: Nome vazio - linha ignorada")
                continue

            # Gerar ID se vazio
            if id_value and str(id_value).strip():
                story_id = str(id_value).strip()
            else:
                story_id = f"US-{generated_id_counter:03d}"
                generated_id_counter += 1

            # Contar ocorrências de ID (para detectar duplicatas)
            id_counts[story_id] = id_counts.get(story_id, 0) + 1

            # Validar Story Point (opcional)
            sp_validated = None
            if sp_value is not None and str(sp_value).strip() != "":
                try:
                    sp_validated = int(sp_value)
                    if sp_validated not in [3, 5, 8, 13]:
                        stats["ignoradas_invalidas"] += 1
                        stats["warnings"].append(
                            f"Linha {row_num}: Story Point inválido ({sp_value}) - linha ignorada"
                        )
                        continue
                except (ValueError, TypeError):
                    stats["ignoradas_invalidas"] += 1
                    stats["warnings"].append(
                        f"Linha {row_num}: Story Point inválido ({sp_value}) - linha ignorada"
                    )
                    continue

            # Criar DTO temporário (dependências serão processadas depois)
            story_dto = StoryDTO(
                id=story_id,
                feature=str(feature).strip(),
                name=str(name).strip(),
                status="BACKLOG",
                priority=0,  # Será ajustado depois
                developer_id=None,
                dependencies=[],  # Processado na FASE 2
                story_point=sp_validated,
                start_date=None,
                end_date=None,
                duration=None,
            )

            temp_stories.append((story_id, story_dto, row_num, deps_value))

        # FASE 2: Identificar IDs duplicados
        duplicated_ids = {story_id for story_id, count in id_counts.items() if count > 1}

        # Registrar warnings para IDs duplicados
        for story_id in duplicated_ids:
            count = id_counts[story_id]
            stats["ignoradas_duplicadas"] += count
            for i in range(count):
                stats["warnings"].append(
                    f"ID '{story_id}' duplicado na planilha - {count} linhas ignoradas"
                )

        # FASE 3: Filtrar histórias válidas (sem duplicatas) e processar dependências
        valid_stories = []
        all_story_ids = {sid for sid, _, _, _ in temp_stories if sid not in duplicated_ids}

        for story_id, story_dto, row_num, deps_value in temp_stories:
            # Ignorar histórias com ID duplicado
            if story_id in duplicated_ids:
                continue

            # Processar dependências
            valid_deps, invalid_deps = self._process_dependencies(
                deps_value, all_story_ids, existing_ids, story_id
            )

            story_dto.dependencies = valid_deps

            # Registrar dependências inválidas
            for invalid_dep in invalid_deps:
                stats["deps_ignoradas"] += 1
                stats["warnings"].append(
                    f"Linha {row_num}: Dependência '{invalid_dep}' não encontrada - removida da história '{story_id}'"
                )

            valid_stories.append(story_dto)

        # FASE 4: Ajustar prioridades sequencialmente
        for idx, story_dto in enumerate(valid_stories, start=1):
            story_dto.priority = idx

        stats["total_importadas"] = len(valid_stories)

        return valid_stories, stats

    def _process_dependencies(
        self,
        deps_value: Any,
        all_story_ids: Set[str],
        existing_ids: Set[str],
        story_id: str
    ) -> Tuple[List[str], List[str]]:
        """
        Processa campo Deps e valida dependências.

        Args:
            deps_value: Valor do campo Deps (string com vírgulas ou None)
            all_story_ids: IDs de todas as histórias na planilha
            existing_ids: IDs de histórias já existentes no banco
            story_id: ID da história corrente (não pode depender de si mesma)

        Returns:
            Tupla (valid_deps, invalid_deps)
        """
        if not deps_value or str(deps_value).strip() == "":
            return [], []

        # Split por vírgula e limpar espaços
        deps = [dep.strip() for dep in str(deps_value).split(',') if dep.strip()]

        valid_deps = []
        invalid_deps = []

        for dep_id in deps:
            # Não pode depender de si mesma
            if dep_id == story_id:
                invalid_deps.append(dep_id)
                continue

            # Validar se dependência existe (na planilha ou no banco)
            if dep_id in all_story_ids or dep_id in existing_ids:
                valid_deps.append(dep_id)
            else:
                invalid_deps.append(dep_id)

        return valid_deps, invalid_deps

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
