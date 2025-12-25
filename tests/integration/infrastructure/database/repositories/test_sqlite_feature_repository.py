"""Testes de integração para SQLiteFeatureRepository."""
import pytest

from backlog_manager.domain.entities.feature import Feature
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection
from backlog_manager.infrastructure.database.repositories.sqlite_feature_repository import SQLiteFeatureRepository


@pytest.fixture
def repository(tmp_path):
    """Cria repository com banco temporário e tabela features."""
    db_path = tmp_path / "test.db"
    # Resetar singleton
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None
    conn = SQLiteConnection(str(db_path))

    # A tabela features é criada automaticamente pela migration 003
    # Não precisa criar manualmente

    return SQLiteFeatureRepository(conn)


@pytest.fixture
def sample_feature():
    """Feature de exemplo."""
    return Feature(id="feature_001", name="MVP Core", wave=2)


def test_save_and_find_by_id(repository, sample_feature):
    """Deve salvar e recuperar feature por ID."""
    # Save
    repository.save(sample_feature)

    # Find
    found = repository.find_by_id("feature_001")

    assert found is not None
    assert found.id == "feature_001"
    assert found.name == "MVP Core"
    assert found.wave == 2


def test_find_by_wave(repository, sample_feature):
    """Deve buscar feature por número de onda."""
    repository.save(sample_feature)

    found = repository.find_by_wave(2)

    assert found is not None
    assert found.id == "feature_001"
    assert found.wave == 2


def test_find_by_wave_not_found(repository):
    """Deve retornar None se onda não existe."""
    found = repository.find_by_wave(999)
    assert found is None


def test_find_all_returns_ordered_by_wave(repository):
    """Deve retornar features ordenadas por onda (ASC)."""
    # Migration cria feature_default com wave=1, então usamos waves 2, 3, 4
    feature1 = Feature(id="feature_001", name="Onda 4", wave=4)
    feature2 = Feature(id="feature_002", name="Onda 2", wave=2)
    feature3 = Feature(id="feature_003", name="Onda 3", wave=3)

    repository.save(feature1)
    repository.save(feature2)
    repository.save(feature3)

    features = repository.find_all()

    assert len(features) == 4  # Inclui feature_default
    assert features[0].wave == 1  # feature_default
    assert features[1].wave == 2  # feature_002
    assert features[2].wave == 3  # feature_003
    assert features[3].wave == 4  # feature_001


def test_delete_feature(repository, sample_feature):
    """Deve deletar feature."""
    repository.save(sample_feature)
    assert repository.exists("feature_001") is True

    repository.delete("feature_001")

    assert repository.exists("feature_001") is False
    assert repository.find_by_id("feature_001") is None


def test_exists_returns_true_when_feature_exists(repository, sample_feature):
    """Deve retornar True se feature existe."""
    repository.save(sample_feature)
    assert repository.exists("feature_001") is True


def test_exists_returns_false_when_feature_not_exists(repository):
    """Deve retornar False se feature não existe."""
    assert repository.exists("feature_999") is False


def test_wave_exists_returns_true_when_wave_exists(repository, sample_feature):
    """Deve retornar True se onda existe."""
    repository.save(sample_feature)
    assert repository.wave_exists(2) is True


def test_wave_exists_returns_false_when_wave_not_exists(repository):
    """Deve retornar False se onda não existe."""
    assert repository.wave_exists(999) is False


def test_update_feature(repository, sample_feature):
    """Deve atualizar feature existente."""
    # Salvar inicial
    repository.save(sample_feature)

    # Modificar e salvar novamente
    sample_feature.name = "MVP Core Atualizado"
    sample_feature.wave = 3  # Mudar de 2 para 3
    repository.save(sample_feature)

    # Verificar atualização
    found = repository.find_by_id("feature_001")
    assert found.name == "MVP Core Atualizado"
    assert found.wave == 3


def test_find_all_returns_default_feature(repository):
    """Deve retornar a feature padrão criada pela migration."""
    features = repository.find_all()
    # A migration 003 cria uma feature padrão
    assert len(features) == 1
    assert features[0].id == "feature_default"
    assert features[0].name == "Backlog Inicial"
    assert features[0].wave == 1


def test_find_by_id_returns_none_when_not_found(repository):
    """Deve retornar None quando feature não existe."""
    found = repository.find_by_id("feature_999")
    assert found is None


def test_features_with_gaps_in_wave_numbers(repository):
    """Deve suportar gaps nos números de onda."""
    # Migration cria feature_default com wave=1, então usamos outras waves
    feature1 = Feature(id="feature_001", name="Onda 5", wave=5)
    feature2 = Feature(id="feature_002", name="Onda 10", wave=10)
    feature3 = Feature(id="feature_003", name="Onda 100", wave=100)

    repository.save(feature1)
    repository.save(feature2)
    repository.save(feature3)

    features = repository.find_all()

    assert len(features) == 4  # Inclui feature_default
    assert features[0].wave == 1   # feature_default
    assert features[1].wave == 5   # feature_001
    assert features[2].wave == 10  # feature_002
    assert features[3].wave == 100 # feature_003
