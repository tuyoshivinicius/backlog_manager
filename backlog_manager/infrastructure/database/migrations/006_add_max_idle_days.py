"""Migration 006: Adiciona coluna max_idle_days à tabela configuration."""
import sqlite3


def upgrade(connection: sqlite3.Connection) -> bool:
    """
    Aplica a migration adicionando a coluna max_idle_days.

    A coluna define o máximo de dias úteis ociosos permitidos
    entre histórias do mesmo desenvolvedor durante a alocação.

    Args:
        connection: Conexão SQLite ativa

    Returns:
        True se migration foi aplicada, False se já existia

    Raises:
        sqlite3.Error: Se houver erro ao executar SQL
    """
    cursor = connection.cursor()
    try:
        cursor.execute("""
            ALTER TABLE configuration
            ADD COLUMN max_idle_days INTEGER NOT NULL DEFAULT 3
        """)
        connection.commit()
        return True
    except sqlite3.OperationalError as e:
        # Coluna já existe (migration já aplicada anteriormente)
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            return False
        raise


def downgrade(connection: sqlite3.Connection) -> None:
    """
    Reverte a migration removendo a coluna max_idle_days.

    Nota: SQLite não suporta DROP COLUMN diretamente.

    Args:
        connection: Conexão SQLite ativa
    """
    raise NotImplementedError("Downgrade não implementado para SQLite")


def apply_if_needed(connection: sqlite3.Connection) -> bool:
    """
    Aplica migration apenas se necessário (idempotente).

    Args:
        connection: Conexão SQLite ativa

    Returns:
        True se migration foi aplicada, False se já existia
    """
    return upgrade(connection)
