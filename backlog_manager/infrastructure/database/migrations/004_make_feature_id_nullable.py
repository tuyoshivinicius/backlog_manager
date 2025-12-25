"""Migration 004: Torna feature_id nullable para permitir histórias sem feature."""
import logging
import sqlite3

logger = logging.getLogger(__name__)


def apply_if_needed(connection: sqlite3.Connection) -> bool:
    """
    Aplica a migration se necessário.

    Args:
        connection: Conexão SQLite ativa

    Returns:
        True se migration foi aplicada, False se já existia
    """
    return upgrade(connection)


def upgrade(connection: sqlite3.Connection) -> bool:
    """
    Aplica a migration tornando feature_id nullable.

    Esta migration:
    1. Cria nova tabela stories com feature_id nullable
    2. Copia dados da tabela antiga
    3. Remove tabela antiga
    4. Renomeia tabela nova
    5. Recria índices e triggers

    Args:
        connection: Conexão SQLite ativa

    Returns:
        True se migration foi aplicada, False se já existia

    Raises:
        sqlite3.Error: Se houver erro ao executar SQL
    """
    cursor = connection.cursor()

    # Verificar se migration já foi aplicada
    # (checando se feature_id já é nullable)
    cursor.execute("PRAGMA table_info(stories)")
    columns = cursor.fetchall()
    for col in columns:
        col_name = col[1]
        col_notnull = col[3]  # 0 = nullable, 1 = not null
        if col_name == "feature_id" and col_notnull == 0:
            logger.debug("Migration 004 já aplicada (feature_id já é nullable)")
            return False

    try:
        logger.info("Aplicando migration 004: Tornando feature_id nullable")

        # PASSO 1: Criar nova tabela com feature_id nullable
        cursor.execute("""
            CREATE TABLE stories_new (
                id TEXT PRIMARY KEY,
                component TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('BACKLOG', 'EXECUÇÃO', 'TESTES', 'CONCLUÍDO', 'IMPEDIDO')),
                priority INTEGER NOT NULL DEFAULT 0,
                feature_id TEXT,
                developer_id TEXT,
                dependencies TEXT DEFAULT '[]',
                story_point INTEGER NOT NULL CHECK (story_point IN (3, 5, 8, 13)),
                start_date TEXT,
                end_date TEXT,
                duration INTEGER,
                schedule_order INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (feature_id) REFERENCES features(id) ON DELETE SET NULL,
                FOREIGN KEY (developer_id) REFERENCES developers(id) ON DELETE SET NULL
            )
        """)
        logger.debug("Tabela stories_new criada com feature_id nullable")

        # PASSO 2: Copiar dados
        cursor.execute("""
            INSERT INTO stories_new
            SELECT id, component, name, status, priority, feature_id, developer_id,
                   dependencies, story_point, start_date, end_date, duration,
                   schedule_order, created_at, updated_at
            FROM stories
        """)
        logger.debug("Dados copiados para stories_new")

        # PASSO 3: Dropar tabela antiga
        cursor.execute("DROP TABLE stories")
        logger.debug("Tabela stories antiga removida")

        # PASSO 4: Renomear tabela nova
        cursor.execute("ALTER TABLE stories_new RENAME TO stories")
        logger.debug("Tabela stories_new renomeada para stories")

        # PASSO 5: Recriar índices
        cursor.execute("CREATE INDEX idx_stories_priority ON stories(priority)")
        cursor.execute("CREATE INDEX idx_stories_status ON stories(status)")
        cursor.execute("CREATE INDEX idx_stories_developer ON stories(developer_id)")
        cursor.execute("CREATE INDEX idx_stories_component ON stories(component)")
        cursor.execute("CREATE INDEX idx_stories_feature ON stories(feature_id)")
        logger.debug("Índices recriados")

        # PASSO 6: Recriar trigger
        cursor.execute("""
            CREATE TRIGGER update_stories_timestamp
            AFTER UPDATE ON stories
            FOR EACH ROW
            BEGIN
                UPDATE stories SET updated_at = datetime('now') WHERE id = OLD.id;
            END
        """)
        logger.debug("Trigger update_stories_timestamp recriado")

        connection.commit()
        logger.info("Migration 004 aplicada com sucesso")
        return True

    except Exception as e:
        logger.error(f"Erro ao aplicar migration 004: {e}", exc_info=True)
        connection.rollback()
        raise


def downgrade(connection: sqlite3.Connection) -> None:
    """
    Reverte a migration tornando feature_id obrigatório novamente.

    ATENÇÃO: Este rollback falhará se existirem histórias com feature_id NULL.

    Args:
        connection: Conexão SQLite ativa

    Raises:
        sqlite3.Error: Se houver erro ao executar SQL
    """
    cursor = connection.cursor()

    try:
        logger.info("Revertendo migration 004: Tornando feature_id NOT NULL novamente")

        # Validar que não há histórias com feature_id NULL
        cursor.execute("SELECT COUNT(*) FROM stories WHERE feature_id IS NULL")
        count = cursor.fetchone()[0]
        if count > 0:
            raise sqlite3.IntegrityError(
                f"Não é possível reverter migration 004: {count} histórias têm feature_id NULL"
            )

        # Criar tabela com feature_id NOT NULL
        cursor.execute("""
            CREATE TABLE stories_new (
                id TEXT PRIMARY KEY,
                component TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('BACKLOG', 'EXECUÇÃO', 'TESTES', 'CONCLUÍDO', 'IMPEDIDO')),
                priority INTEGER NOT NULL DEFAULT 0,
                feature_id TEXT NOT NULL,
                developer_id TEXT,
                dependencies TEXT DEFAULT '[]',
                story_point INTEGER NOT NULL CHECK (story_point IN (3, 5, 8, 13)),
                start_date TEXT,
                end_date TEXT,
                duration INTEGER,
                schedule_order INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (feature_id) REFERENCES features(id) ON DELETE RESTRICT,
                FOREIGN KEY (developer_id) REFERENCES developers(id) ON DELETE SET NULL
            )
        """)

        # Copiar dados
        cursor.execute("""
            INSERT INTO stories_new
            SELECT id, component, name, status, priority, feature_id, developer_id,
                   dependencies, story_point, start_date, end_date, duration,
                   schedule_order, created_at, updated_at
            FROM stories
        """)

        # Dropar tabela antiga
        cursor.execute("DROP TABLE stories")

        # Renomear tabela nova
        cursor.execute("ALTER TABLE stories_new RENAME TO stories")

        # Recriar índices
        cursor.execute("CREATE INDEX idx_stories_priority ON stories(priority)")
        cursor.execute("CREATE INDEX idx_stories_status ON stories(status)")
        cursor.execute("CREATE INDEX idx_stories_developer ON stories(developer_id)")
        cursor.execute("CREATE INDEX idx_stories_component ON stories(component)")
        cursor.execute("CREATE INDEX idx_stories_feature ON stories(feature_id)")

        # Recriar trigger
        cursor.execute("""
            CREATE TRIGGER update_stories_timestamp
            AFTER UPDATE ON stories
            FOR EACH ROW
            BEGIN
                UPDATE stories SET updated_at = datetime('now') WHERE id = OLD.id;
            END
        """)

        connection.commit()
        logger.info("Migration 004 revertida com sucesso")

    except Exception as e:
        logger.error(f"Erro ao reverter migration 004: {e}", exc_info=True)
        connection.rollback()
        raise
