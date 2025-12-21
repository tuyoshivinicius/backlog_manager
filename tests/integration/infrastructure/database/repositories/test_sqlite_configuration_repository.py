"""Testes de integração para SQLiteConfigurationRepository."""
from datetime import date

import pytest

from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.infrastructure.database.repositories.sqlite_configuration_repository import (
    SQLiteConfigurationRepository,
)
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


@pytest.fixture
def repository(tmp_path):
    """Cria repository com banco temporário."""
    db_path = tmp_path / "test.db"
    # Resetar singleton
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None
    conn = SQLiteConnection(str(db_path))
    return SQLiteConfigurationRepository(conn)


def test_get_default_configuration(repository):
    """Deve retornar configuração padrão."""
    config = repository.get()

    assert config.story_points_per_sprint == 21
    assert config.workdays_per_sprint == 15
    assert config.roadmap_start_date is None  # Padrão é None


def test_save_and_get_configuration(repository):
    """Deve salvar e recuperar configuração."""
    config = Configuration(story_points_per_sprint=30, workdays_per_sprint=20, roadmap_start_date=None)

    repository.save(config)
    retrieved = repository.get()

    assert retrieved.story_points_per_sprint == 30
    assert retrieved.workdays_per_sprint == 20
    assert retrieved.roadmap_start_date is None


def test_save_and_get_configuration_with_roadmap_start_date(repository):
    """Deve salvar e recuperar configuração com data de início."""
    start_date = date(2025, 2, 10)  # Segunda-feira
    config = Configuration(story_points_per_sprint=30, workdays_per_sprint=20, roadmap_start_date=start_date)

    repository.save(config)
    retrieved = repository.get()

    assert retrieved.story_points_per_sprint == 30
    assert retrieved.workdays_per_sprint == 20
    assert retrieved.roadmap_start_date == start_date


def test_save_configuration_with_none_start_date(repository):
    """Deve salvar configuração sem data de início (NULL)."""
    config = Configuration(story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=None)

    repository.save(config)
    retrieved = repository.get()

    assert retrieved.roadmap_start_date is None


def test_update_configuration_roadmap_start_date(repository):
    """Deve atualizar data de início do roadmap."""
    # Salvar configuração inicial sem data
    config1 = Configuration(story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=None)
    repository.save(config1)

    # Atualizar com data
    start_date = date(2025, 3, 17)  # Segunda-feira
    config2 = Configuration(story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=start_date)
    repository.save(config2)

    # Verificar
    retrieved = repository.get()
    assert retrieved.roadmap_start_date == start_date


def test_clear_roadmap_start_date(repository):
    """Deve permitir limpar data de início (voltar para None)."""
    # Salvar com data
    start_date = date(2025, 4, 14)  # Segunda-feira
    config1 = Configuration(story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=start_date)
    repository.save(config1)

    # Limpar data (voltar para None)
    config2 = Configuration(story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=None)
    repository.save(config2)

    # Verificar
    retrieved = repository.get()
    assert retrieved.roadmap_start_date is None
