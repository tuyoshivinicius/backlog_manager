"""Migration 005: Adiciona coluna allocation_criteria à tabela configuration."""
import sqlite3


def upgrade(connection: sqlite3.Connection) -> bool:
    """
    Aplica a migration adicionando a coluna allocation_criteria.

    A coluna armazena o critério de alocação de desenvolvedores:
    - LOAD_BALANCING: Balanceamento de carga (padrão)
    - DEPENDENCY_OWNER: Prioriza proprietário de dependência

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
            ADD COLUMN allocation_criteria TEXT NOT NULL DEFAULT 'LOAD_BALANCING'
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
    Reverte a migration removendo a coluna allocation_criteria.

    Nota: SQLite não suporta DROP COLUMN diretamente. Para reverter,
    seria necessário recriar a tabela sem a coluna.

    Args:
        connection: Conexão SQLite ativa
    """
    # SQLite não suporta DROP COLUMN facilmente
    # Seria necessário: CREATE TABLE temp, COPY data, DROP TABLE, RENAME
    # Como a coluna tem valor default, não há problema mantê-la
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
