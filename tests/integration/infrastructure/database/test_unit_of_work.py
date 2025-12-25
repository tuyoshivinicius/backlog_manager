"""Testes de integração para Unit of Work."""
import pytest

from backlog_manager.domain.entities.developer import Developer
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection
from backlog_manager.infrastructure.database.unit_of_work import UnitOfWork


@pytest.fixture
def uow(tmp_path):
    """Cria UnitOfWork com banco temporário."""
    db_path = tmp_path / "test.db"
    # Resetar singleton
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None
    return UnitOfWork(str(db_path))


def test_commit_persists_changes(tmp_path):
    """Deve persistir mudanças após commit."""
    db_path = tmp_path / "test.db"
    # Resetar singleton
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None

    story = Story(
        id="US-001",
        component="F1",
        name="S1",
        feature_id="feature_default",
        status=StoryStatus.BACKLOG,
        priority=0,
        developer_id=None,
        dependencies=[],
        story_point=StoryPoint(5),
    )

    # Salvar com commit
    with UnitOfWork(str(db_path)) as uow:
        uow.stories.save(story)
        uow.commit()

    # Resetar singleton para nova conexão
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None

    # Verificar que foi persistido
    with UnitOfWork(str(db_path)) as uow:
        found = uow.stories.find_by_id("US-001")
        assert found is not None


def test_rollback_discards_changes(tmp_path):
    """Deve descartar mudanças após rollback."""
    db_path = tmp_path / "test.db"
    # Resetar singleton
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None

    story = Story(
        id="US-001",
        component="F1",
        name="S1",
        feature_id="feature_default",
        status=StoryStatus.BACKLOG,
        priority=0,
        developer_id=None,
        dependencies=[],
        story_point=StoryPoint(5),
    )

    # Salvar mas fazer rollback
    with UnitOfWork(str(db_path)) as uow:
        uow.stories.save(story)
        uow.rollback()

    # Resetar singleton
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None

    # Verificar que NÃO foi persistido
    with UnitOfWork(str(db_path)) as uow:
        found = uow.stories.find_by_id("US-001")
        assert found is None


def test_exception_triggers_automatic_rollback(tmp_path):
    """Deve fazer rollback automático em caso de exceção."""
    db_path = tmp_path / "test.db"
    # Resetar singleton
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None

    story = Story(
        id="US-001",
        component="F1",
        name="S1",
        feature_id="feature_default",
        status=StoryStatus.BACKLOG,
        priority=0,
        developer_id=None,
        dependencies=[],
        story_point=StoryPoint(5),
    )

    # Simular exceção dentro do contexto
    try:
        with UnitOfWork(str(db_path)) as uow:
            uow.stories.save(story)
            raise ValueError("Erro simulado")
    except ValueError:
        pass

    # Resetar singleton
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None

    # Verificar que rollback foi feito
    with UnitOfWork(str(db_path)) as uow:
        found = uow.stories.find_by_id("US-001")
        assert found is None


def test_all_repositories_available(uow):
    """Deve fornecer acesso a todos os repositories."""
    assert uow.stories is not None
    assert uow.developers is not None
    assert uow.configuration is not None


def test_configuration_repository_works(uow):
    """Deve conseguir ler e atualizar configuração."""
    # Ler configuração padrão
    config = uow.configuration.get()
    assert config.story_points_per_sprint == 21
    assert config.workdays_per_sprint == 15

    # Atualizar
    config.story_points_per_sprint = 30
    uow.configuration.save(config)
    uow.commit()

    # Verificar mudança
    updated_config = uow.configuration.get()
    assert updated_config.story_points_per_sprint == 30
