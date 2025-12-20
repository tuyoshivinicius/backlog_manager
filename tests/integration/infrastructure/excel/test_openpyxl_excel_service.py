"""Testes de integração para OpenpyxlExcelService."""
import pytest
from pathlib import Path

from openpyxl import Workbook, load_workbook

from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus
from backlog_manager.infrastructure.excel.openpyxl_excel_service import OpenpyxlExcelService


@pytest.fixture
def excel_service():
    return OpenpyxlExcelService()


@pytest.fixture
def valid_excel_file(tmp_path):
    """Cria arquivo Excel válido para testes."""
    file_path = tmp_path / "backlog.xlsx"

    wb = Workbook()
    ws = wb.active

    # Cabeçalho
    ws.append(["Feature", "Nome", "StoryPoint"])

    # Dados
    ws.append(["Autenticação", "Login de usuário", 5])
    ws.append(["Autenticação", "Logout", 3])
    ws.append(["Dashboard", "Exibir métricas", 8])

    wb.save(file_path)
    return str(file_path)


def test_import_valid_excel(excel_service, valid_excel_file):
    """Deve importar histórias de Excel válido."""
    stories = excel_service.import_stories(valid_excel_file)

    assert len(stories) == 3
    assert stories[0].id == "US-001"
    assert stories[0].feature == "Autenticação"
    assert stories[0].name == "Login de usuário"
    assert stories[0].story_point.value == 5
    assert stories[1].id == "US-002"
    assert stories[2].id == "US-003"


def test_import_file_not_found(excel_service):
    """Deve lançar erro se arquivo não existe."""
    with pytest.raises(FileNotFoundError, match="Arquivo não encontrado"):
        excel_service.import_stories("arquivo_inexistente.xlsx")


def test_import_invalid_header(excel_service, tmp_path):
    """Deve lançar erro se cabeçalho inválido."""
    file_path = tmp_path / "invalid_header.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.append(["Coluna1", "Coluna2", "Coluna3"])  # Cabeçalho errado
    ws.append(["Feature1", "Story1", 5])
    wb.save(file_path)

    with pytest.raises(ValueError, match="Colunas inválidas"):
        excel_service.import_stories(str(file_path))


def test_import_invalid_story_point_raises_error(excel_service, tmp_path):
    """Deve lançar erro se Story Point inválido."""
    file_path = tmp_path / "invalid.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.append(["Feature", "Nome", "StoryPoint"])
    ws.append(["Feature1", "Story1", 7])  # 7 é inválido
    wb.save(file_path)

    with pytest.raises(ValueError, match="Story Point inválido"):
        excel_service.import_stories(str(file_path))


def test_import_missing_data(excel_service, tmp_path):
    """Deve lançar erro se dados obrigatórios faltando."""
    file_path = tmp_path / "missing_data.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.append(["Feature", "Nome", "StoryPoint"])
    ws.append(["Feature1", None, 5])  # Nome faltando
    wb.save(file_path)

    with pytest.raises(ValueError, match="Dados obrigatórios faltando"):
        excel_service.import_stories(str(file_path))


def test_export_creates_formatted_excel(excel_service, tmp_path):
    """Deve exportar backlog para Excel formatado."""
    file_path = tmp_path / "export.xlsx"

    stories = [
        Story(
            id="US-001",
            feature="F1",
            name="S1",
            status=StoryStatus.BACKLOG,
            priority=0,
            developer_id="DEV-001",
            dependencies=["US-002"],
            story_point=StoryPoint(5),
        )
    ]

    excel_service.export_stories(stories, str(file_path))

    assert Path(file_path).exists()

    # Verificar conteúdo
    wb = load_workbook(file_path)
    ws = wb.active

    # Cabeçalho
    assert ws.cell(1, 1).value == "Prioridade"
    assert ws.cell(1, 2).value == "ID"
    assert ws.cell(1, 3).value == "Feature"

    # Dados
    assert ws.cell(2, 1).value == 0  # priority
    assert ws.cell(2, 2).value == "US-001"  # id
    assert ws.cell(2, 3).value == "F1"  # feature
    assert ws.cell(2, 4).value == "S1"  # name
    assert ws.cell(2, 5).value == "BACKLOG"  # status
    assert ws.cell(2, 6).value == "DEV-001"  # developer_id
    assert ws.cell(2, 7).value == "US-002"  # dependencies
    assert ws.cell(2, 8).value == 5  # story_point


def test_export_multiple_stories(excel_service, tmp_path):
    """Deve exportar múltiplas histórias."""
    file_path = tmp_path / "export_multiple.xlsx"

    stories = [
        Story(
            id="US-001",
            feature="F1",
            name="S1",
            status=StoryStatus.BACKLOG,
            priority=0,
            developer_id=None,
            dependencies=[],
            story_point=StoryPoint(3),
        ),
        Story(
            id="US-002",
            feature="F1",
            name="S2",
            status=StoryStatus.EXECUCAO,
            priority=1,
            developer_id="DEV-001",
            dependencies=["US-001"],
            story_point=StoryPoint(5),
        ),
        Story(
            id="US-003",
            feature="F2",
            name="S3",
            status=StoryStatus.CONCLUIDO,
            priority=2,
            developer_id="DEV-002",
            dependencies=[],
            story_point=StoryPoint(8),
        ),
    ]

    excel_service.export_stories(stories, str(file_path))

    # Verificar
    wb = load_workbook(file_path)
    ws = wb.active

    # Deve ter cabeçalho + 3 linhas de dados
    assert ws.max_row == 4
    assert ws.cell(2, 2).value == "US-001"
    assert ws.cell(3, 2).value == "US-002"
    assert ws.cell(4, 2).value == "US-003"
