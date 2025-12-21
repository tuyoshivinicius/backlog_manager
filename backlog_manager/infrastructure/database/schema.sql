-- ============================================
-- SCHEMA DO BACKLOG MANAGER
-- ============================================

-- Tabela de Histórias (Stories)
CREATE TABLE IF NOT EXISTS stories (
    id TEXT PRIMARY KEY,
    feature TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('BACKLOG', 'EXECUÇÃO', 'TESTES', 'CONCLUÍDO', 'IMPEDIDO')),
    priority INTEGER NOT NULL DEFAULT 0,
    developer_id TEXT,
    dependencies TEXT DEFAULT '[]',  -- JSON array: ["US-001", "US-002"]
    story_point INTEGER NOT NULL CHECK (story_point IN (3, 5, 8, 13)),
    start_date TEXT,  -- ISO format: 2025-01-15
    end_date TEXT,    -- ISO format: 2025-01-20
    duration INTEGER, -- Duração em dias úteis
    schedule_order INTEGER, -- Ordem para alocação de desenvolvedores
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (developer_id) REFERENCES developers(id) ON DELETE SET NULL
);

-- Índices para otimização de queries
CREATE INDEX IF NOT EXISTS idx_stories_priority ON stories(priority);
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);
CREATE INDEX IF NOT EXISTS idx_stories_developer ON stories(developer_id);
CREATE INDEX IF NOT EXISTS idx_stories_feature ON stories(feature);

-- Tabela de Desenvolvedores (Developers)
CREATE TABLE IF NOT EXISTS developers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Tabela de Configuração (Configuration)
-- Singleton: Apenas 1 linha permitida
CREATE TABLE IF NOT EXISTS configuration (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    story_points_per_sprint INTEGER NOT NULL DEFAULT 21,
    workdays_per_sprint INTEGER NOT NULL DEFAULT 15,
    roadmap_start_date TEXT,  -- ISO format: 2025-01-15 (opcional)
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Inserir configuração padrão
INSERT OR IGNORE INTO configuration (id, story_points_per_sprint, workdays_per_sprint)
VALUES (1, 21, 15);

-- ============================================
-- TRIGGERS PARA ATUALIZAÇÃO AUTOMÁTICA
-- ============================================

-- Trigger para atualizar updated_at em stories
CREATE TRIGGER IF NOT EXISTS update_stories_timestamp
AFTER UPDATE ON stories
FOR EACH ROW
BEGIN
    UPDATE stories SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- Trigger para atualizar updated_at em developers
CREATE TRIGGER IF NOT EXISTS update_developers_timestamp
AFTER UPDATE ON developers
FOR EACH ROW
BEGIN
    UPDATE developers SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- Trigger para atualizar updated_at em configuration
CREATE TRIGGER IF NOT EXISTS update_configuration_timestamp
AFTER UPDATE ON configuration
FOR EACH ROW
BEGIN
    UPDATE configuration SET updated_at = datetime('now') WHERE id = OLD.id;
END;
