"""Migration 002: Adiciona coluna schedule_order à tabela stories."""
import sqlite3


def upgrade(connection: sqlite3.Connection) -> bool:
    """
    Aplica a migration adicionando a coluna schedule_order.

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
            ALTER TABLE stories
            ADD COLUMN schedule_order INTEGER
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
    Reverte a migration removendo a coluna schedule_order.

    Nota: SQLite não suporta DROP COLUMN diretamente. Para reverter,
    seria necessário recriar a tabela sem a coluna.

    Args:
        connection: Conexão SQLite ativa
    """
    # SQLite não suporta DROP COLUMN facilmente
    # Seria necessário: CREATE TABLE temp, COPY data, DROP TABLE, RENAME
    # Como a coluna é nullable, não há problema mantê-la
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
