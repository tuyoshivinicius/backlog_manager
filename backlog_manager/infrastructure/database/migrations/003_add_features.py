"""Migration 003: Adiciona tabela features e relacionamento com stories."""
import sqlite3


def upgrade(connection: sqlite3.Connection) -> bool:
    """
    Aplica a migration adicionando features e relacionamento.

    Esta migration:
    1. Cria tabela features
    2. Insere feature padrão "Backlog Inicial" (onda 1)
    3. Adiciona coluna feature_id em stories
    4. Associa todas histórias existentes à feature padrão
    5. Recria tabela stories com feature_id NOT NULL

    Args:
        connection: Conexão SQLite ativa

    Returns:
        True se migration foi aplicada, False se já existia

    Raises:
        sqlite3.Error: Se houver erro ao executar SQL
    """
    cursor = connection.cursor()

    # Verificar se migration já foi aplicada
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='features'")
    if cursor.fetchone() is not None:
        return False

    try:
        # PASSO 1: Criar tabela features
        cursor.execute("""
            CREATE TABLE features (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                wave INTEGER NOT NULL UNIQUE CHECK (wave > 0),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        # PASSO 2: Criar índice
        cursor.execute("CREATE INDEX idx_features_wave ON features(wave)")

        # PASSO 3: Criar trigger de updated_at
        cursor.execute("""
            CREATE TRIGGER update_features_timestamp
            AFTER UPDATE ON features
            FOR EACH ROW
            BEGIN
                UPDATE features SET updated_at = datetime('now') WHERE id = OLD.id;
            END
        """)

        # PASSO 4: Inserir feature padrão (para histórias existentes)
        cursor.execute(
            "INSERT INTO features (id, name, wave) VALUES (?, ?, ?)",
            ("feature_default", "Backlog Inicial", 1),
        )

        # PASSO 5: Adicionar coluna feature_id em stories (NULLABLE temporariamente)
        cursor.execute("ALTER TABLE stories ADD COLUMN feature_id TEXT")

        # PASSO 6: Associar todas histórias existentes à feature padrão
        cursor.execute("UPDATE stories SET feature_id = 'feature_default' WHERE feature_id IS NULL")

        # PASSO 7: Validar que todas histórias foram associadas
        cursor.execute("SELECT COUNT(*) as count FROM stories WHERE feature_id IS NULL")
        row = cursor.fetchone()
        if row and row[0] > 0:
            raise sqlite3.IntegrityError("Migration falhou: histórias sem feature_id")

        # PASSO 8: Recriar tabela stories com feature_id NOT NULL
        # 8.1. Criar tabela temporária com novo schema
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

        # 8.2. Copiar dados
        cursor.execute("""
            INSERT INTO stories_new
            SELECT id, component, name, status, priority, feature_id, developer_id,
                   dependencies, story_point, start_date, end_date, duration,
                   schedule_order, created_at, updated_at
            FROM stories
        """)

        # 8.3. Dropar tabela antiga
        cursor.execute("DROP TABLE stories")

        # 8.4. Renomear tabela nova
        cursor.execute("ALTER TABLE stories_new RENAME TO stories")

        # 8.5. Recriar índices
        cursor.execute("CREATE INDEX idx_stories_priority ON stories(priority)")
        cursor.execute("CREATE INDEX idx_stories_status ON stories(status)")
        cursor.execute("CREATE INDEX idx_stories_developer ON stories(developer_id)")
        cursor.execute("CREATE INDEX idx_stories_component ON stories(component)")
        cursor.execute("CREATE INDEX idx_stories_feature ON stories(feature_id)")

        # 8.6. Recriar trigger
        cursor.execute("""
            CREATE TRIGGER update_stories_timestamp
            AFTER UPDATE ON stories
            FOR EACH ROW
            BEGIN
                UPDATE stories SET updated_at = datetime('now') WHERE id = OLD.id;
            END
        """)

        # PASSO 9: Validar integridade referencial
        cursor.execute("""
            SELECT COUNT(*) as count FROM stories s
            LEFT JOIN features f ON s.feature_id = f.id
            WHERE f.id IS NULL
        """)
        row = cursor.fetchone()
        if row and row[0] > 0:
            raise sqlite3.IntegrityError("Migration falhou: referências inválidas")

        connection.commit()
        return True

    except Exception as e:
        connection.rollback()
        raise


def downgrade(connection: sqlite3.Connection) -> None:
    """
    Reverte a migration removendo features e relacionamento.

    ATENÇÃO: Este rollback resultará em perda da informação de features.
    Todas as histórias voltarão ao estado anterior sem feature_id.

    Args:
        connection: Conexão SQLite ativa
    """
    cursor = connection.cursor()

    try:
        # 1. Recriar tabela stories sem feature_id
        cursor.execute("""
            CREATE TABLE stories_old (
                id TEXT PRIMARY KEY,
                component TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('BACKLOG', 'EXECUÇÃO', 'TESTES', 'CONCLUÍDO', 'IMPEDIDO')),
                priority INTEGER NOT NULL DEFAULT 0,
                developer_id TEXT,
                dependencies TEXT DEFAULT '[]',
                story_point INTEGER NOT NULL CHECK (story_point IN (3, 5, 8, 13)),
                start_date TEXT,
                end_date TEXT,
                duration INTEGER,
                schedule_order INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (developer_id) REFERENCES developers(id) ON DELETE SET NULL
            )
        """)

        # 2. Copiar dados (excluindo feature_id)
        cursor.execute("""
            INSERT INTO stories_old
            SELECT id, component, name, status, priority, developer_id,
                   dependencies, story_point, start_date, end_date, duration,
                   schedule_order, created_at, updated_at
            FROM stories
        """)

        # 3. Dropar tabela atual
        cursor.execute("DROP TABLE stories")

        # 4. Renomear
        cursor.execute("ALTER TABLE stories_old RENAME TO stories")

        # 5. Recriar índices originais
        cursor.execute("CREATE INDEX idx_stories_priority ON stories(priority)")
        cursor.execute("CREATE INDEX idx_stories_status ON stories(status)")
        cursor.execute("CREATE INDEX idx_stories_developer ON stories(developer_id)")
        cursor.execute("CREATE INDEX idx_stories_component ON stories(component)")

        # 6. Recriar trigger
        cursor.execute("""
            CREATE TRIGGER update_stories_timestamp
            AFTER UPDATE ON stories
            FOR EACH ROW
            BEGIN
                UPDATE stories SET updated_at = datetime('now') WHERE id = OLD.id;
            END
        """)

        # 7. Dropar tabela features
        cursor.execute("DROP TABLE IF EXISTS features")

        connection.commit()

    except Exception as e:
        connection.rollback()
        raise


def apply_if_needed(connection: sqlite3.Connection) -> bool:
    """
    Aplica migration apenas se necessário (idempotente).

    Args:
        connection: Conexão SQLite ativa

    Returns:
        True se migration foi aplicada, False se já existia
    """
    return upgrade(connection)
