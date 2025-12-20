# PLANO FASE 3: Camada de Infraestrutura (Persistência)

**Status**: 🚧 Próxima Fase
**Story Points**: 21 SP
**Duração Estimada**: 1.5-2 semanas
**Pré-requisitos**: ✅ Fase 1 e Fase 2 concluídas

---

## 📋 SUMÁRIO EXECUTIVO

### Objetivo Principal
Implementar a **Camada de Infraestrutura**, fornecendo implementações concretas das interfaces (Ports) definidas na Fase 2. Esta fase conecta a aplicação ao mundo externo através de:
- **Persistência em SQLite** (banco de dados local)
- **Importação/Exportação Excel** (integração com arquivos)
- **Gerenciamento de transações** (Unit of Work)

### Entregas Principais
1. ✅ Banco de dados SQLite configurado com migrações automáticas
2. ✅ 3 Repositories implementados (Story, Developer, Configuration)
3. ✅ Excel Service implementado (import/export com openpyxl)
4. ✅ Unit of Work para transações
5. ✅ Testes de integração completos (>85% cobertura)

### Arquitetura
```
infrastructure/
├── database/
│   ├── __init__.py
│   ├── sqlite_connection.py           # Singleton de conexão
│   ├── schema.sql                     # Schema do banco
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── migration_manager.py       # Gerenciador de migrações
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── sqlite_story_repository.py
│   │   ├── sqlite_developer_repository.py
│   │   └── sqlite_configuration_repository.py
│   └── unit_of_work.py                # Padrão Unit of Work
├── excel/
│   ├── __init__.py
│   └── openpyxl_excel_service.py      # Implementação Excel
└── __init__.py
```

---

## 🎯 OBJETIVOS DETALHADOS

### O que NÃO fazer
- ❌ **NÃO usar ORMs** (SQLAlchemy, Peewee) - Manter controle total do SQL
- ❌ **NÃO adicionar lógica de negócio** - Apenas persistência e recuperação
- ❌ **NÃO violar Clean Architecture** - Infrastructure depende de Application, nunca o contrário
- ❌ **NÃO criar dependências circulares** - Sempre respeitar a regra de dependência

### O que fazer
- ✅ **Implementar interfaces** definidas em `application/interfaces/`
- ✅ **SQL puro e otimizado** - Queries eficientes e sem abstrações pesadas
- ✅ **Migrações automáticas** - Banco criado automaticamente na primeira execução
- ✅ **Testes de integração** - Validar persistência e recuperação de dados
- ✅ **Tratamento de erros** - Exceções claras para problemas de I/O
- ✅ **Transações** - Garantir atomicidade em operações complexas

---

## 📦 TAREFA 3.1: Setup do Banco de Dados SQLite

**Story Points**: 3 SP
**Objetivo**: Configurar conexão SQLite com schema e migrações automáticas

### 3.1.1 Criar SQLiteConnection Singleton

**Arquivo**: `infrastructure/database/sqlite_connection.py`

**Responsabilidades**:
- Gerenciar conexão única (singleton) com banco SQLite
- Criar banco automaticamente se não existir
- Fornecer conexão para repositories
- Executar migrações na primeira inicialização

**Implementação**:
```python
"""Gerenciador de conexão SQLite singleton."""
import sqlite3
from pathlib import Path
from typing import Optional


class SQLiteConnection:
    """
    Singleton para gerenciar conexão com banco SQLite.

    Responsabilidades:
    - Criar banco se não existir
    - Manter conexão única
    - Executar migrações na primeira inicialização
    """

    _instance: Optional['SQLiteConnection'] = None
    _connection: Optional[sqlite3.Connection] = None

    def __new__(cls, db_path: str = "backlog.db"):
        """Garante que apenas uma instância existe."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: str = "backlog.db"):
        """
        Inicializa conexão com banco.

        Args:
            db_path: Caminho do arquivo SQLite
        """
        if self._connection is None:
            self._db_path = Path(db_path)
            self._connect()
            self._run_migrations()

    def _connect(self) -> None:
        """Estabelece conexão com banco SQLite."""
        self._connection = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False  # Permite uso em múltiplas threads
        )
        # Configurar para retornar Rows (acesso por nome de coluna)
        self._connection.row_factory = sqlite3.Row
        # Habilitar foreign keys
        self._connection.execute("PRAGMA foreign_keys = ON")

    def _run_migrations(self) -> None:
        """Executa migrações se banco for novo."""
        cursor = self._connection.cursor()

        # Verificar se tabelas existem
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='stories'
        """)

        if cursor.fetchone() is None:
            # Banco novo - executar schema
            self._execute_schema()

    def _execute_schema(self) -> None:
        """Executa script de criação de schema."""
        schema_path = Path(__file__).parent / "schema.sql"

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        self._connection.executescript(schema_sql)
        self._connection.commit()

    def get_connection(self) -> sqlite3.Connection:
        """
        Retorna conexão ativa.

        Returns:
            Conexão SQLite
        """
        if self._connection is None:
            self._connect()
        return self._connection

    def close(self) -> None:
        """Fecha conexão com banco."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
```

### 3.1.2 Criar Schema do Banco

**Arquivo**: `infrastructure/database/schema.sql`

**Schema Completo**:
```sql
-- ============================================
-- SCHEMA DO BACKLOG MANAGER
-- ============================================

-- Tabela de Histórias (Stories)
CREATE TABLE IF NOT EXISTS stories (
    id TEXT PRIMARY KEY,
    feature TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('BACKLOG', 'EXECUCAO', 'TESTES', 'CONCLUIDO', 'IMPEDIDO')),
    priority INTEGER NOT NULL DEFAULT 0,
    developer_id TEXT,
    dependencies TEXT DEFAULT '[]',  -- JSON array: ["US-001", "US-002"]
    story_point INTEGER NOT NULL CHECK (story_point IN (3, 5, 8, 13)),
    start_date TEXT,  -- ISO format: 2025-01-15
    end_date TEXT,    -- ISO format: 2025-01-20
    duration INTEGER, -- Duração em dias úteis
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
```

### 3.1.3 Testes de Conexão

**Arquivo**: `tests/integration/infrastructure/test_sqlite_connection.py`

```python
"""Testes de integração para SQLiteConnection."""
import sqlite3
from pathlib import Path

import pytest

from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


@pytest.fixture
def temp_db(tmp_path):
    """Cria banco temporário para testes."""
    db_path = tmp_path / "test.db"
    yield str(db_path)
    # Cleanup
    if db_path.exists():
        db_path.unlink()


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
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)

    tables = [row[0] for row in cursor.fetchall()]

    assert 'stories' in tables
    assert 'developers' in tables
    assert 'configuration' in tables


def test_inserts_default_configuration(temp_db):
    """Deve inserir configuração padrão."""
    conn = SQLiteConnection(temp_db)
    cursor = conn.get_connection().cursor()

    cursor.execute("SELECT * FROM configuration WHERE id = 1")
    row = cursor.fetchone()

    assert row is not None
    assert row['story_points_per_sprint'] == 21
    assert row['workdays_per_sprint'] == 15


def test_foreign_keys_enabled(temp_db):
    """Deve ter foreign keys habilitadas."""
    conn = SQLiteConnection(temp_db)
    cursor = conn.get_connection().cursor()

    cursor.execute("PRAGMA foreign_keys")
    result = cursor.fetchone()

    assert result[0] == 1  # 1 = enabled
```

### Critérios de Aceitação (3.1)
- [ ] SQLiteConnection implementado como singleton
- [ ] Banco criado automaticamente na primeira execução
- [ ] Schema completo com todas as tabelas
- [ ] Índices criados para otimização
- [ ] Triggers de updated_at funcionando
- [ ] Testes de conexão passando

---

## 📦 TAREFA 3.2: Implementar Repositories

**Story Points**: 8 SP
**Objetivo**: Implementar os 3 repositories (Story, Developer, Configuration)

### 3.2.1 SQLiteStoryRepository

**Arquivo**: `infrastructure/database/repositories/sqlite_story_repository.py`

**Responsabilidades**:
- Implementar interface `StoryRepository`
- Converter Entity Story ↔ Database Row
- Serializar dependências como JSON
- Queries otimizadas com índices

**Métodos**:
```python
class SQLiteStoryRepository(StoryRepository):
    """Implementação SQLite do repositório de histórias."""

    def save(self, story: Story) -> None:
        """Salva ou atualiza história."""

    def find_by_id(self, story_id: str) -> Optional[Story]:
        """Busca história por ID."""

    def find_all(self) -> List[Story]:
        """Retorna todas histórias ordenadas por prioridade."""

    def delete(self, story_id: str) -> None:
        """Remove história do banco."""

    def exists(self, story_id: str) -> bool:
        """Verifica se história existe."""

    # Métodos auxiliares privados
    def _entity_to_row(self, story: Story) -> dict:
        """Converte Story entity para dict de banco."""

    def _row_to_entity(self, row: sqlite3.Row) -> Story:
        """Converte row de banco para Story entity."""
```

**Implementação Completa**:
```python
"""Implementação SQLite do repositório de histórias."""
import json
import sqlite3
from datetime import date
from typing import List, Optional

from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


class SQLiteStoryRepository(StoryRepository):
    """
    Implementação SQLite do repositório de histórias.

    Responsabilidades:
    - Persistir e recuperar histórias do banco SQLite
    - Converter entre Story entity e rows do banco
    - Serializar dependências como JSON
    """

    def __init__(self, connection: SQLiteConnection):
        """
        Inicializa repositório.

        Args:
            connection: Conexão SQLite singleton
        """
        self._conn = connection.get_connection()

    def save(self, story: Story) -> None:
        """
        Salva ou atualiza história no banco.

        Args:
            story: História a ser salva
        """
        row_data = self._entity_to_row(story)

        cursor = self._conn.cursor()

        # Usar REPLACE (UPDATE ou INSERT)
        cursor.execute("""
            REPLACE INTO stories (
                id, feature, name, status, priority,
                developer_id, dependencies, story_point,
                start_date, end_date, duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row_data['id'],
            row_data['feature'],
            row_data['name'],
            row_data['status'],
            row_data['priority'],
            row_data['developer_id'],
            row_data['dependencies'],
            row_data['story_point'],
            row_data['start_date'],
            row_data['end_date'],
            row_data['duration']
        ))

        self._conn.commit()

    def find_by_id(self, story_id: str) -> Optional[Story]:
        """
        Busca história por ID.

        Args:
            story_id: ID da história

        Returns:
            Story se encontrada, None caso contrário
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_entity(row)

    def find_all(self) -> List[Story]:
        """
        Retorna todas histórias ordenadas por prioridade.

        Returns:
            Lista de histórias
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM stories ORDER BY priority ASC")

        rows = cursor.fetchall()

        return [self._row_to_entity(row) for row in rows]

    def delete(self, story_id: str) -> None:
        """
        Remove história do banco.

        Args:
            story_id: ID da história
        """
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM stories WHERE id = ?", (story_id,))
        self._conn.commit()

    def exists(self, story_id: str) -> bool:
        """
        Verifica se história existe.

        Args:
            story_id: ID da história

        Returns:
            True se existe, False caso contrário
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM stories WHERE id = ? LIMIT 1", (story_id,))
        return cursor.fetchone() is not None

    # Métodos auxiliares privados

    def _entity_to_row(self, story: Story) -> dict:
        """
        Converte Story entity para dict de banco.

        Args:
            story: Entity Story

        Returns:
            Dict com dados para banco
        """
        return {
            'id': story.id,
            'feature': story.feature,
            'name': story.name,
            'status': story.status.value,
            'priority': story.priority,
            'developer_id': story.developer_id,
            'dependencies': json.dumps(story.dependencies),
            'story_point': story.story_point.value,
            'start_date': story.start_date.isoformat() if story.start_date else None,
            'end_date': story.end_date.isoformat() if story.end_date else None,
            'duration': story.duration
        }

    def _row_to_entity(self, row: sqlite3.Row) -> Story:
        """
        Converte row de banco para Story entity.

        Args:
            row: Row do SQLite

        Returns:
            Story entity
        """
        return Story(
            id=row['id'],
            feature=row['feature'],
            name=row['name'],
            status=StoryStatus(row['status']),
            priority=row['priority'],
            developer_id=row['developer_id'],
            dependencies=json.loads(row['dependencies']),
            story_point=StoryPoint(row['story_point']),
            start_date=date.fromisoformat(row['start_date']) if row['start_date'] else None,
            end_date=date.fromisoformat(row['end_date']) if row['end_date'] else None,
            duration=row['duration']
        )
```

### 3.2.2 SQLiteDeveloperRepository

**Arquivo**: `infrastructure/database/repositories/sqlite_developer_repository.py`

**Implementação** (Similar ao Story, mas mais simples):
```python
"""Implementação SQLite do repositório de desenvolvedores."""
import sqlite3
from typing import List, Optional

from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.domain.entities.developer import Developer
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


class SQLiteDeveloperRepository(DeveloperRepository):
    """Implementação SQLite do repositório de desenvolvedores."""

    def __init__(self, connection: SQLiteConnection):
        self._conn = connection.get_connection()

    def save(self, developer: Developer) -> None:
        """Salva ou atualiza desenvolvedor."""
        cursor = self._conn.cursor()
        cursor.execute("""
            REPLACE INTO developers (id, name)
            VALUES (?, ?)
        """, (developer.id, developer.name))
        self._conn.commit()

    def find_by_id(self, developer_id: str) -> Optional[Developer]:
        """Busca desenvolvedor por ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM developers WHERE id = ?", (developer_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return Developer(id=row['id'], name=row['name'])

    def find_all(self) -> List[Developer]:
        """Retorna todos desenvolvedores ordenados por nome."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM developers ORDER BY name ASC")
        rows = cursor.fetchall()

        return [Developer(id=row['id'], name=row['name']) for row in rows]

    def delete(self, developer_id: str) -> None:
        """Remove desenvolvedor do banco."""
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM developers WHERE id = ?", (developer_id,))
        self._conn.commit()

    def exists(self, developer_id: str) -> bool:
        """Verifica se desenvolvedor existe."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM developers WHERE id = ? LIMIT 1", (developer_id,))
        return cursor.fetchone() is not None
```

### 3.2.3 SQLiteConfigurationRepository

**Arquivo**: `infrastructure/database/repositories/sqlite_configuration_repository.py`

**Implementação** (Singleton - sempre ID=1):
```python
"""Implementação SQLite do repositório de configuração."""
from backlog_manager.application.interfaces.repositories.configuration_repository import ConfigurationRepository
from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


class SQLiteConfigurationRepository(ConfigurationRepository):
    """Implementação SQLite do repositório de configuração."""

    def __init__(self, connection: SQLiteConnection):
        self._conn = connection.get_connection()

    def get(self) -> Configuration:
        """
        Retorna configuração (sempre existe ID=1).

        Returns:
            Configuration entity
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM configuration WHERE id = 1")
        row = cursor.fetchone()

        # Garantido existir (criado no schema)
        return Configuration(
            story_points_per_sprint=row['story_points_per_sprint'],
            workdays_per_sprint=row['workdays_per_sprint']
        )

    def save(self, config: Configuration) -> None:
        """
        Atualiza configuração.

        Args:
            config: Configuração a salvar
        """
        cursor = self._conn.cursor()
        cursor.execute("""
            UPDATE configuration
            SET story_points_per_sprint = ?,
                workdays_per_sprint = ?
            WHERE id = 1
        """, (config.story_points_per_sprint, config.workdays_per_sprint))
        self._conn.commit()
```

### 3.2.4 Testes de Repositories

**Exemplo**: `tests/integration/infrastructure/repositories/test_sqlite_story_repository.py`

```python
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
    conn = SQLiteConnection(str(db_path))
    return SQLiteStoryRepository(conn)


@pytest.fixture
def sample_story():
    """História de exemplo."""
    return Story(
        id="US-001",
        feature="Autenticação",
        name="Login de usuário",
        status=StoryStatus.BACKLOG,
        priority=0,
        developer_id=None,
        dependencies=[],
        story_point=StoryPoint(5),
        start_date=None,
        end_date=None,
        duration=None
    )


def test_save_and_find_by_id(repository, sample_story):
    """Deve salvar e recuperar história por ID."""
    # Save
    repository.save(sample_story)

    # Find
    found = repository.find_by_id("US-001")

    assert found is not None
    assert found.id == "US-001"
    assert found.feature == "Autenticação"
    assert found.name == "Login de usuário"
    assert found.story_point.value == 5


def test_find_all_returns_ordered_by_priority(repository):
    """Deve retornar histórias ordenadas por prioridade."""
    story1 = Story(
        id="US-001", feature="F1", name="S1",
        status=StoryStatus.BACKLOG, priority=2,
        developer_id=None, dependencies=[], story_point=StoryPoint(3)
    )
    story2 = Story(
        id="US-002", feature="F1", name="S2",
        status=StoryStatus.BACKLOG, priority=0,
        developer_id=None, dependencies=[], story_point=StoryPoint(5)
    )
    story3 = Story(
        id="US-003", feature="F1", name="S3",
        status=StoryStatus.BACKLOG, priority=1,
        developer_id=None, dependencies=[], story_point=StoryPoint(8)
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

    assert repository.exists("US-001") is True

    repository.delete("US-001")

    assert repository.exists("US-001") is False
    assert repository.find_by_id("US-001") is None


def test_saves_dependencies_as_json(repository):
    """Deve serializar dependências como JSON."""
    story = Story(
        id="US-002", feature="F1", name="S2",
        status=StoryStatus.BACKLOG, priority=0,
        developer_id=None,
        dependencies=["US-001", "US-003"],  # Lista de dependências
        story_point=StoryPoint(5)
    )

    repository.save(story)

    found = repository.find_by_id("US-002")
    assert found.dependencies == ["US-001", "US-003"]
```

### Critérios de Aceitação (3.2)
- [ ] SQLiteStoryRepository implementado e testado
- [ ] SQLiteDeveloperRepository implementado e testado
- [ ] SQLiteConfigurationRepository implementado e testado
- [ ] Conversão Entity ↔ Database funciona corretamente
- [ ] Dependências serializadas como JSON
- [ ] Testes de CRUD passando para todos repositories
- [ ] Queries otimizadas com índices

---

## 📦 TAREFA 3.3: Unit of Work Pattern

**Story Points**: 3 SP
**Objetivo**: Implementar padrão Unit of Work para gerenciar transações

### 3.3.1 Implementar UnitOfWork

**Arquivo**: `infrastructure/database/unit_of_work.py`

**Responsabilidades**:
- Gerenciar transações (begin, commit, rollback)
- Fornecer repositories dentro do contexto transacional
- Context manager para uso com `with`

**Implementação**:
```python
"""Implementação do padrão Unit of Work."""
from typing import Optional

from backlog_manager.application.interfaces.repositories.configuration_repository import ConfigurationRepository
from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.infrastructure.database.repositories.sqlite_configuration_repository import (
    SQLiteConfigurationRepository,
)
from backlog_manager.infrastructure.database.repositories.sqlite_developer_repository import SQLiteDeveloperRepository
from backlog_manager.infrastructure.database.repositories.sqlite_story_repository import SQLiteStoryRepository
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


class UnitOfWork:
    """
    Padrão Unit of Work para gerenciar transações.

    Uso:
        with UnitOfWork() as uow:
            story = uow.stories.find_by_id("US-001")
            story.name = "Novo nome"
            uow.stories.save(story)
            uow.commit()  # Commit explícito
    """

    def __init__(self, db_path: str = "backlog.db"):
        """
        Inicializa Unit of Work.

        Args:
            db_path: Caminho do banco SQLite
        """
        self._connection = SQLiteConnection(db_path)
        self._conn = self._connection.get_connection()

        # Repositories
        self.stories: StoryRepository = SQLiteStoryRepository(self._connection)
        self.developers: DeveloperRepository = SQLiteDeveloperRepository(self._connection)
        self.configuration: ConfigurationRepository = SQLiteConfigurationRepository(self._connection)

    def __enter__(self):
        """Inicia transação."""
        self._conn.execute("BEGIN TRANSACTION")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza transação (rollback em caso de exceção)."""
        if exc_type is not None:
            self.rollback()
        # Não fazer commit automático - deve ser explícito

    def commit(self) -> None:
        """Confirma transação."""
        self._conn.commit()

    def rollback(self) -> None:
        """Desfaz transação."""
        self._conn.rollback()
```

### 3.3.2 Testes de UnitOfWork

```python
"""Testes para Unit of Work."""
import pytest

from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus
from backlog_manager.infrastructure.database.unit_of_work import UnitOfWork


def test_commit_persists_changes(tmp_path):
    """Deve persistir mudanças após commit."""
    db_path = tmp_path / "test.db"

    story = Story(
        id="US-001", feature="F1", name="S1",
        status=StoryStatus.BACKLOG, priority=0,
        developer_id=None, dependencies=[], story_point=StoryPoint(5)
    )

    # Salvar com commit
    with UnitOfWork(str(db_path)) as uow:
        uow.stories.save(story)
        uow.commit()

    # Verificar que foi persistido
    with UnitOfWork(str(db_path)) as uow:
        found = uow.stories.find_by_id("US-001")
        assert found is not None


def test_rollback_discards_changes(tmp_path):
    """Deve descartar mudanças após rollback."""
    db_path = tmp_path / "test.db"

    story = Story(
        id="US-001", feature="F1", name="S1",
        status=StoryStatus.BACKLOG, priority=0,
        developer_id=None, dependencies=[], story_point=StoryPoint(5)
    )

    # Salvar mas fazer rollback
    with UnitOfWork(str(db_path)) as uow:
        uow.stories.save(story)
        uow.rollback()

    # Verificar que NÃO foi persistido
    with UnitOfWork(str(db_path)) as uow:
        found = uow.stories.find_by_id("US-001")
        assert found is None


def test_exception_triggers_automatic_rollback(tmp_path):
    """Deve fazer rollback automático em caso de exceção."""
    db_path = tmp_path / "test.db"

    story = Story(
        id="US-001", feature="F1", name="S1",
        status=StoryStatus.BACKLOG, priority=0,
        developer_id=None, dependencies=[], story_point=StoryPoint(5)
    )

    # Simular exceção dentro do contexto
    try:
        with UnitOfWork(str(db_path)) as uow:
            uow.stories.save(story)
            raise ValueError("Erro simulado")
    except ValueError:
        pass

    # Verificar que rollback foi feito
    with UnitOfWork(str(db_path)) as uow:
        found = uow.stories.find_by_id("US-001")
        assert found is None
```

### Critérios de Aceitação (3.3)
- [ ] UnitOfWork implementado como context manager
- [ ] Commit persiste mudanças
- [ ] Rollback descarta mudanças
- [ ] Exceções disparam rollback automático
- [ ] Repositories acessíveis via UnitOfWork
- [ ] Testes de transações passando

---

## 📦 TAREFA 3.4: Excel Service

**Story Points**: 5 SP
**Objetivo**: Implementar importação e exportação de Excel com openpyxl

### 3.4.1 Implementar OpenpyxlExcelService

**Arquivo**: `infrastructure/excel/openpyxl_excel_service.py`

**Responsabilidades**:
- Importar histórias de arquivo Excel (.xlsx)
- Exportar backlog para Excel com formatação
- Validar formato e dados do Excel
- Retornar erros claros em caso de problemas

**Formato Excel - Import** (3 colunas obrigatórias):
```
| Feature       | Nome                  | StoryPoint |
|---------------|-----------------------|------------|
| Autenticação  | Login de usuário      | 5          |
| Autenticação  | Logout                | 3          |
| Dashboard     | Exibir métricas       | 8          |
```

**Formato Excel - Export** (11 colunas):
```
| Prioridade | ID     | Feature | Nome | Status | Desenvolvedor | Dependências | SP | Início     | Fim        | Duração |
|------------|--------|---------|------|--------|---------------|--------------|----|-----------|-----------|---------|
| 0          | US-001 | Auth    | ...  | BACKLOG| Alice         | []           | 5  | 2025-01-15| 2025-01-18| 4       |
```

**Implementação**:
```python
"""Implementação do Excel Service usando openpyxl."""
from datetime import date
from pathlib import Path
from typing import List

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from backlog_manager.application.interfaces.services.excel_service import ExcelService
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


class OpenpyxlExcelService(ExcelService):
    """
    Implementação do serviço de Excel usando openpyxl.

    Responsabilidades:
    - Importar histórias de planilha Excel
    - Exportar backlog para Excel com formatação
    - Validar formato e dados
    """

    # Colunas esperadas no import
    IMPORT_COLUMNS = ["Feature", "Nome", "StoryPoint"]

    # Colunas do export
    EXPORT_COLUMNS = [
        "Prioridade", "ID", "Feature", "Nome", "Status",
        "Desenvolvedor", "Dependências", "SP",
        "Início", "Fim", "Duração"
    ]

    def import_stories(self, file_path: str) -> List[Story]:
        """
        Importa histórias de arquivo Excel.

        Args:
            file_path: Caminho do arquivo .xlsx

        Returns:
            Lista de histórias importadas

        Raises:
            FileNotFoundError: Se arquivo não existe
            ValueError: Se formato inválido ou dados inválidos
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        workbook = load_workbook(file_path)
        sheet = workbook.active

        # Validar cabeçalho
        header = [cell.value for cell in sheet[1]]
        if header[:3] != self.IMPORT_COLUMNS:
            raise ValueError(
                f"Colunas inválidas. Esperado: {self.IMPORT_COLUMNS}, "
                f"Encontrado: {header[:3]}"
            )

        stories = []
        errors = []

        # Processar linhas (pular cabeçalho)
        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            feature, name, story_point_value = row[:3]

            # Validar dados obrigatórios
            if not feature or not name or story_point_value is None:
                errors.append(f"Linha {row_num}: Dados obrigatórios faltando")
                continue

            # Validar Story Point
            try:
                story_point = StoryPoint(int(story_point_value))
            except (ValueError, TypeError) as e:
                errors.append(f"Linha {row_num}: Story Point inválido ({story_point_value})")
                continue

            # Gerar ID sequencial
            story_id = f"US-{len(stories) + 1:03d}"

            # Criar história
            story = Story(
                id=story_id,
                feature=str(feature).strip(),
                name=str(name).strip(),
                status=StoryStatus.BACKLOG,
                priority=len(stories),  # Ordem de importação
                developer_id=None,
                dependencies=[],
                story_point=story_point,
                start_date=None,
                end_date=None,
                duration=None
            )

            stories.append(story)

        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Erros na importação:\n{error_msg}")

        return stories

    def export_stories(self, stories: List[Story], file_path: str) -> None:
        """
        Exporta histórias para arquivo Excel.

        Args:
            stories: Lista de histórias a exportar
            file_path: Caminho do arquivo .xlsx a criar
        """
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Backlog"

        # Escrever cabeçalho
        for col_num, column_name in enumerate(self.EXPORT_COLUMNS, start=1):
            cell = sheet.cell(row=1, column=col_num)
            cell.value = column_name
            cell.font = Font(bold=True, size=11)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Escrever dados
        for row_num, story in enumerate(stories, start=2):
            sheet.cell(row=row_num, column=1).value = story.priority
            sheet.cell(row=row_num, column=2).value = story.id
            sheet.cell(row=row_num, column=3).value = story.feature
            sheet.cell(row=row_num, column=4).value = story.name
            sheet.cell(row=row_num, column=5).value = story.status.value
            sheet.cell(row=row_num, column=6).value = story.developer_id or ""
            sheet.cell(row=row_num, column=7).value = ", ".join(story.dependencies)
            sheet.cell(row=row_num, column=8).value = story.story_point.value
            sheet.cell(row=row_num, column=9).value = story.start_date.isoformat() if story.start_date else ""
            sheet.cell(row=row_num, column=10).value = story.end_date.isoformat() if story.end_date else ""
            sheet.cell(row=row_num, column=11).value = story.duration or ""

        # Auto-ajustar largura das colunas
        for col_num in range(1, len(self.EXPORT_COLUMNS) + 1):
            column_letter = get_column_letter(col_num)
            max_length = 0

            for cell in sheet[column_letter]:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))

            sheet.column_dimensions[column_letter].width = min(max_length + 2, 50)

        # Adicionar bordas
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        for row in sheet.iter_rows(min_row=1, max_row=len(stories) + 1):
            for cell in row:
                cell.border = thin_border

        # Salvar arquivo
        workbook.save(file_path)
```

### 3.4.2 Testes de Excel Service

```python
"""Testes para OpenpyxlExcelService."""
import pytest
from pathlib import Path

from openpyxl import Workbook

from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus
from backlog_manager.infrastructure.excel.openpyxl_excel_service import OpenpyxlExcelService


@pytest.fixture
def excel_service():
    return OpenpyxlExcelService()


@pytest.fixture
def valid_excel_file(tmp_path):
    """Cria arquivo Excel válido para testes."""
    file_path = tmp_path / "backlog.xlsx"

    wb = Workbook()
    ws = wb.active

    # Cabeçalho
    ws.append(["Feature", "Nome", "StoryPoint"])

    # Dados
    ws.append(["Autenticação", "Login de usuário", 5])
    ws.append(["Autenticação", "Logout", 3])
    ws.append(["Dashboard", "Exibir métricas", 8])

    wb.save(file_path)
    return str(file_path)


def test_import_valid_excel(excel_service, valid_excel_file):
    """Deve importar histórias de Excel válido."""
    stories = excel_service.import_stories(valid_excel_file)

    assert len(stories) == 3
    assert stories[0].id == "US-001"
    assert stories[0].feature == "Autenticação"
    assert stories[0].name == "Login de usuário"
    assert stories[0].story_point.value == 5


def test_import_invalid_story_point_raises_error(excel_service, tmp_path):
    """Deve lançar erro se Story Point inválido."""
    file_path = tmp_path / "invalid.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.append(["Feature", "Nome", "StoryPoint"])
    ws.append(["Feature1", "Story1", 7])  # 7 é inválido
    wb.save(file_path)

    with pytest.raises(ValueError, match="Story Point inválido"):
        excel_service.import_stories(str(file_path))


def test_export_creates_formatted_excel(excel_service, tmp_path):
    """Deve exportar backlog para Excel formatado."""
    file_path = tmp_path / "export.xlsx"

    stories = [
        Story(
            id="US-001", feature="F1", name="S1",
            status=StoryStatus.BACKLOG, priority=0,
            developer_id="DEV-001", dependencies=["US-002"],
            story_point=StoryPoint(5)
        )
    ]

    excel_service.export_stories(stories, str(file_path))

    assert Path(file_path).exists()

    # Verificar conteúdo
    from openpyxl import load_workbook
    wb = load_workbook(file_path)
    ws = wb.active

    # Cabeçalho
    assert ws.cell(1, 1).value == "Prioridade"
    assert ws.cell(1, 2).value == "ID"

    # Dados
    assert ws.cell(2, 1).value == 0  # priority
    assert ws.cell(2, 2).value == "US-001"  # id
    assert ws.cell(2, 3).value == "F1"  # feature
```

### Critérios de Aceitação (3.4)
- [ ] OpenpyxlExcelService implementado
- [ ] Import de Excel funciona com validação
- [ ] Export cria Excel formatado (cabeçalho em negrito, bordas, auto-width)
- [ ] Erros de importação retornam mensagens claras
- [ ] Testes de import/export passando

---

## 📦 TAREFA 3.5: Testes de Integração Completos

**Story Points**: 2 SP
**Objetivo**: Validar fluxos end-to-end da infraestrutura

### 3.5.1 Testes de Fluxo Completo

```python
"""Testes de integração completos da infraestrutura."""
import pytest
from datetime import date

from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus
from backlog_manager.infrastructure.database.unit_of_work import UnitOfWork
from backlog_manager.infrastructure.excel.openpyxl_excel_service import OpenpyxlExcelService


def test_full_flow_excel_import_to_database(tmp_path):
    """
    Teste E2E: Import Excel → Salvar DB → Recuperar DB → Export Excel
    """
    db_path = tmp_path / "test.db"
    import_file = tmp_path / "import.xlsx"
    export_file = tmp_path / "export.xlsx"

    # 1. Criar Excel de importação
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Feature", "Nome", "StoryPoint"])
    ws.append(["Auth", "Login", 5])
    ws.append(["Auth", "Logout", 3])
    wb.save(import_file)

    # 2. Importar histórias
    excel_service = OpenpyxlExcelService()
    stories = excel_service.import_stories(str(import_file))

    assert len(stories) == 2

    # 3. Salvar no banco
    with UnitOfWork(str(db_path)) as uow:
        for story in stories:
            uow.stories.save(story)
        uow.commit()

    # 4. Recuperar do banco
    with UnitOfWork(str(db_path)) as uow:
        recovered_stories = uow.stories.find_all()

    assert len(recovered_stories) == 2
    assert recovered_stories[0].id == "US-001"

    # 5. Exportar para Excel
    excel_service.export_stories(recovered_stories, str(export_file))

    assert export_file.exists()


def test_transaction_rollback_on_error(tmp_path):
    """Deve fazer rollback se erro ocorrer durante transação."""
    db_path = tmp_path / "test.db"

    story1 = Story(
        id="US-001", feature="F1", name="S1",
        status=StoryStatus.BACKLOG, priority=0,
        developer_id=None, dependencies=[], story_point=StoryPoint(5)
    )

    # Tentar salvar mas simular erro
    try:
        with UnitOfWork(str(db_path)) as uow:
            uow.stories.save(story1)
            # Simular erro antes do commit
            raise RuntimeError("Erro simulado")
    except RuntimeError:
        pass

    # Verificar que rollback foi feito
    with UnitOfWork(str(db_path)) as uow:
        stories = uow.stories.find_all()

    assert len(stories) == 0  # Rollback descartou a história
```

### Critérios de Aceitação (3.5)
- [ ] Teste E2E completo (Excel → DB → Excel) passa
- [ ] Testes de erro e rollback funcionam
- [ ] Performance aceitável (100 histórias < 1s)
- [ ] Cobertura de testes da infraestrutura >85%

---

## ✅ CRITÉRIOS DE ACEITAÇÃO GERAIS DA FASE 3

### Funcionalidades
- [ ] Banco SQLite criado automaticamente na primeira execução
- [ ] Todas as tabelas criadas com schema correto
- [ ] 3 Repositories implementados e funcionando (Story, Developer, Configuration)
- [ ] Excel Service importa e exporta corretamente
- [ ] Unit of Work gerencia transações (commit/rollback)
- [ ] Foreign keys e triggers funcionando

### Qualidade
- [ ] Cobertura de testes >85% na camada de infraestrutura
- [ ] Todos os testes de integração passando
- [ ] Performance: 100 histórias < 1s para CRUD
- [ ] Sem warnings de SQLite

### Arquitetura
- [ ] Infrastructure implementa interfaces de Application
- [ ] Nenhuma lógica de negócio na infraestrutura
- [ ] Regra de dependência respeitada (Infrastructure → Application → Domain)
- [ ] Conversões Entity ↔ Database corretas

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Objetivo | Como Medir |
|---------|----------|------------|
| **Cobertura de Testes** | >85% | `pytest --cov=backlog_manager/infrastructure` |
| **Performance CRUD** | <1s para 100 histórias | Testes de performance |
| **Sucesso Import** | 100% para arquivos válidos | Testes com Excel válidos |
| **Atomicidade** | 100% rollback em erros | Testes de transações |

---

## 🚀 PRÓXIMOS PASSOS (Fase 4)

Após concluir a Fase 3, seguir para **Fase 4: Interface Gráfica**:
1. Setup PyQt6/PySide6
2. Janela principal com menu e toolbar
3. Tabela editável de backlog
4. Formulários de CRUD
5. Controllers conectando UI aos use cases

---

## 📚 REFERÊNCIAS

- **SQLite Documentation**: https://www.sqlite.org/docs.html
- **openpyxl Documentation**: https://openpyxl.readthedocs.io/
- **Unit of Work Pattern**: Martin Fowler - Patterns of Enterprise Application Architecture
- **Repository Pattern**: Eric Evans - Domain-Driven Design

---

**Boa implementação! A infraestrutura é a ponte entre o domínio e o mundo real.** 🏗️
