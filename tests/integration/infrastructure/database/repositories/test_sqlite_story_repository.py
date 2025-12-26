"""Testes de integração para SQLiteStoryRepository."""
import pytest
from datetime import date

from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection
from backlog_manager.infrastructure.database.repositories.sqlite_story_repository import SQLiteStoryRepository


@pytest.fixture
def repository(tmp_path):
    """Cria repository com banco temporário."""
    db_path = tmp_path / "test.db"
    # Resetar singleton
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None
    conn = SQLiteConnection(str(db_path))
    return SQLiteStoryRepository(conn)


@pytest.fixture
def sample_story():
    """História de exemplo."""
    return Story(
        id="US-001",
        component="Autenticação",
        name="Login de usuário",
        feature_id="feature_default",
        status=StoryStatus.BACKLOG,
        priority=0,
        developer_id=None,
        dependencies=[],
        story_point=StoryPoint(5),
        start_date=None,
        end_date=None,
        duration=None,
    )


def test_save_and_find_by_id(repository, sample_story):
    """Deve salvar e recuperar história por ID."""
    # Save
    repository.save(sample_story)
    repository._conn.commit()  # Commit explícito para teste

    # Find
    found = repository.find_by_id("US-001")

    assert found is not None
    assert found.id == "US-001"
    assert found.component == "Autenticação"
    assert found.name == "Login de usuário"
    assert found.story_point.value == 5


def test_find_all_returns_ordered_by_priority(repository):
    """Deve retornar histórias ordenadas por prioridade."""
    story1 = Story(
        id="US-001",
        component="F1",
        name="S1",
        feature_id="feature_default",
        status=StoryStatus.BACKLOG,
        priority=2,
        developer_id=None,
        dependencies=[],
        story_point=StoryPoint(3),
    )
    story2 = Story(
        id="US-002",
        component="F1",
        name="S2",
        feature_id="feature_default",
        status=StoryStatus.BACKLOG,
        priority=0,
        developer_id=None,
        dependencies=[],
        story_point=StoryPoint(5),
    )
    story3 = Story(
        id="US-003",
        component="F1",
        name="S3",
        feature_id="feature_default",
        status=StoryStatus.BACKLOG,
        priority=1,
        developer_id=None,
        dependencies=[],
        story_point=StoryPoint(8),
    )

    repository.save(story1)
    repository.save(story2)
    repository.save(story3)

    stories = repository.find_all()

    assert len(stories) == 3
    assert stories[0].id == "US-002"  # priority 0
    assert stories[1].id == "US-003"  # priority 1
    assert stories[2].id == "US-001"  # priority 2


def test_update_existing_story(repository, sample_story):
    """Deve atualizar história existente."""
    # Save inicial
    repository.save(sample_story)

    # Update
    sample_story.name = "Login ATUALIZADO"
    sample_story.status = StoryStatus.EXECUCAO
    repository.save(sample_story)

    # Verificar
    found = repository.find_by_id("US-001")
    assert found.name == "Login ATUALIZADO"
    assert found.status == StoryStatus.EXECUCAO


def test_delete_story(repository, sample_story):
    """Deve deletar história."""
    repository.save(sample_story)

    # Verificar que existe
    found = repository.find_by_id("US-001")
    assert found is not None

    # Deletar
    repository.delete("US-001")

    # Verificar que foi deletada
    found = repository.find_by_id("US-001")
    assert found is None


def test_saves_dependencies_as_json(repository):
    """Deve serializar dependências como JSON."""
    story = Story(
        id="US-002",
        component="F1",
        name="S2",
        feature_id="feature_default",
        status=StoryStatus.BACKLOG,
        priority=0,
        developer_id=None,
        dependencies=["US-001", "US-003"],  # Lista de dependências
        story_point=StoryPoint(5),
    )

    repository.save(story)

    found = repository.find_by_id("US-002")
    assert found.dependencies == ["US-001", "US-003"]


def test_saves_dates_correctly(repository):
    """Deve salvar e recuperar datas corretamente."""
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
        start_date=date(2025, 1, 15),
        end_date=date(2025, 1, 20),
        duration=4,
    )

    repository.save(story)

    found = repository.find_by_id("US-001")
    assert found.start_date == date(2025, 1, 15)
    assert found.end_date == date(2025, 1, 20)
    assert found.duration == 4


def test_save_batch_saves_multiple_stories(repository):
    """Deve salvar múltiplas histórias em batch."""
    stories = [
        Story(
            id="US-001",
            component="F1",
            name="S1",
            feature_id="feature_default",
            status=StoryStatus.BACKLOG,
            priority=0,
            developer_id=None,
            dependencies=[],
            story_point=StoryPoint(3),
        ),
        Story(
            id="US-002",
            component="F1",
            name="S2",
            feature_id="feature_default",
            status=StoryStatus.EXECUCAO,
            priority=1,
            developer_id=None,  # None para evitar FK constraint
            dependencies=["US-001"],
            story_point=StoryPoint(5),
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 20),
        ),
        Story(
            id="US-003",
            component="F2",
            name="S3",
            feature_id="feature_default",
            status=StoryStatus.BACKLOG,
            priority=2,
            developer_id=None,
            dependencies=[],
            story_point=StoryPoint(8),
        ),
    ]

    # Salvar em batch
    repository.save_batch(stories)

    # Verificar que todas foram salvas
    all_stories = repository.find_all()
    assert len(all_stories) == 3

    # Verificar dados de cada história
    found1 = repository.find_by_id("US-001")
    assert found1.name == "S1"
    assert found1.story_point.value == 3

    found2 = repository.find_by_id("US-002")
    assert found2.name == "S2"
    assert found2.dependencies == ["US-001"]
    assert found2.start_date == date(2025, 1, 15)

    found3 = repository.find_by_id("US-003")
    assert found3.component == "F2"
    assert found3.story_point.value == 8


def test_save_batch_empty_list(repository):
    """Deve lidar com lista vazia sem erro."""
    # Não deve lançar exceção
    repository.save_batch([])

    # Deve retornar lista vazia
    all_stories = repository.find_all()
    assert len(all_stories) == 0


def test_save_batch_updates_existing_stories(repository, sample_story):
    """Deve atualizar histórias existentes via save_batch."""
    # Salvar história inicial
    repository.save(sample_story)

    # Atualizar via batch
    sample_story.name = "Nome Atualizado via Batch"
    sample_story.status = StoryStatus.CONCLUIDO
    repository.save_batch([sample_story])

    # Verificar atualização
    found = repository.find_by_id("US-001")
    assert found.name == "Nome Atualizado via Batch"
    assert found.status == StoryStatus.CONCLUIDO
