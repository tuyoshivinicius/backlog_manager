"""Testes de integração para SQLiteConnection."""
import sqlite3
from pathlib import Path

import pytest

from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


@pytest.fixture
def temp_db(tmp_path):
    """Cria banco temporário para testes."""
    db_path = tmp_path / "test.db"
    # Resetar singleton para cada teste
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None
    yield str(db_path)
    # Cleanup: fechar conexão antes de deletar
    if SQLiteConnection._connection is not None:
        SQLiteConnection._connection.close()
        SQLiteConnection._connection = None
        SQLiteConnection._instance = None


def test_singleton_pattern(temp_db):
    """Deve retornar mesma instância (singleton)."""
    conn1 = SQLiteConnection(temp_db)
    conn2 = SQLiteConnection(temp_db)

    assert conn1 is conn2


def test_creates_database_file(temp_db):
    """Deve criar arquivo de banco se não existir."""
    SQLiteConnection(temp_db)

    assert Path(temp_db).exists()


def test_creates_tables_automatically(temp_db):
    """Deve criar tabelas automaticamente."""
    conn = SQLiteConnection(temp_db)
    cursor = conn.get_connection().cursor()

    # Verificar que tabelas existem
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """
    )

    tables = [row[0] for row in cursor.fetchall()]

    assert "stories" in tables
    assert "developers" in tables
    assert "configuration" in tables


def test_inserts_default_configuration(temp_db):
    """Deve inserir configuração padrão."""
    conn = SQLiteConnection(temp_db)
    cursor = conn.get_connection().cursor()

    cursor.execute("SELECT * FROM configuration WHERE id = 1")
    row = cursor.fetchone()

    assert row is not None
    assert row["story_points_per_sprint"] == 21
    assert row["workdays_per_sprint"] == 15


def test_foreign_keys_enabled(temp_db):
    """Deve ter foreign keys habilitadas."""
    conn = SQLiteConnection(temp_db)
    cursor = conn.get_connection().cursor()

    cursor.execute("PRAGMA foreign_keys")
    result = cursor.fetchone()

    assert result[0] == 1  # 1 = enabled


def test_creates_indexes(temp_db):
    """Deve criar índices para otimização."""
    conn = SQLiteConnection(temp_db)
    cursor = conn.get_connection().cursor()

    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='index'
        ORDER BY name
    """
    )

    indexes = [row[0] for row in cursor.fetchall()]

    assert "idx_stories_priority" in indexes
    assert "idx_stories_status" in indexes
    assert "idx_stories_developer" in indexes
    assert "idx_stories_component" in indexes
