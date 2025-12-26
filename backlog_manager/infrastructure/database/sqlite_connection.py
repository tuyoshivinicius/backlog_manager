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

    _instance: Optional["SQLiteConnection"] = None
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
            str(self._db_path), check_same_thread=False  # Permite uso em múltiplas threads
        )
        # Configurar para retornar Rows (acesso por nome de coluna)
        self._connection.row_factory = sqlite3.Row
        # Habilitar foreign keys
        self._connection.execute("PRAGMA foreign_keys = ON")

    def _run_migrations(self) -> None:
        """Executa migrações se banco for novo ou aplica migrations pendentes."""
        cursor = self._connection.cursor()

        # Verificar se tabelas existem
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='stories'
        """
        )

        if cursor.fetchone() is None:
            # Banco novo - executar schema
            self._execute_schema()

        # Sempre executar migrations pendentes (idempotentes)
        self._apply_pending_migrations()

    def _execute_schema(self) -> None:
        """Executa script de criação de schema."""
        schema_path = Path(__file__).parent / "schema.sql"

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        self._connection.executescript(schema_sql)
        self._connection.commit()

    def _apply_pending_migrations(self) -> None:
        """Aplica todas as migrations pendentes (idempotentes)."""
        migrations_path = Path(__file__).parent / "migrations"

        # Migration 001: Adicionar coluna roadmap_start_date
        try:
            migration_001_path = migrations_path / "001_add_roadmap_start_date.py"
            if migration_001_path.exists():
                import importlib.util

                spec = importlib.util.spec_from_file_location("migration_001", migration_001_path)
                if spec and spec.loader:
                    migration_001 = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(migration_001)

                    # Executar migration (idempotente)
                    applied = migration_001.apply_if_needed(self._connection)
                    if applied:
                        print("[OK] Migration 001 aplicada: coluna roadmap_start_date adicionada")
        except Exception as e:
            # Migration já aplicada ou erro - não falhar
            print(f"[INFO] Migration 001: {e}")
            pass

        # Migration 002: Adicionar coluna schedule_order
        try:
            migration_002_path = migrations_path / "002_add_schedule_order.py"
            if migration_002_path.exists():
                import importlib.util

                spec = importlib.util.spec_from_file_location("migration_002", migration_002_path)
                if spec and spec.loader:
                    migration_002 = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(migration_002)

                    # Executar migration (idempotente)
                    applied = migration_002.apply_if_needed(self._connection)
                    if applied:
                        print("[OK] Migration 002 aplicada: coluna schedule_order adicionada")
        except Exception as e:
            # Migration já aplicada ou erro - não falhar
            print(f"[INFO] Migration 002: {e}")
            pass

        # Migration 003: Adicionar features e relacionamento com stories
        try:
            migration_003_path = migrations_path / "003_add_features.py"
            if migration_003_path.exists():
                import importlib.util

                spec = importlib.util.spec_from_file_location("migration_003", migration_003_path)
                if spec and spec.loader:
                    migration_003 = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(migration_003)

                    # Executar migration (idempotente)
                    applied = migration_003.apply_if_needed(self._connection)
                    if applied:
                        print("[OK] Migration 003 aplicada: tabela features criada e stories atualizadas")
        except Exception as e:
            # Migration já aplicada ou erro - não falhar
            print(f"[INFO] Migration 003: {e}")
            pass

        # Migration 004: Tornar feature_id nullable
        try:
            migration_004_path = migrations_path / "004_make_feature_id_nullable.py"
            if migration_004_path.exists():
                import importlib.util

                spec = importlib.util.spec_from_file_location("migration_004", migration_004_path)
                if spec and spec.loader:
                    migration_004 = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(migration_004)

                    # Executar migration (idempotente)
                    applied = migration_004.apply_if_needed(self._connection)
                    if applied:
                        print("[OK] Migration 004 aplicada: feature_id agora permite NULL")
        except Exception as e:
            # Migration já aplicada ou erro - não falhar
            print(f"[INFO] Migration 004: {e}")
            pass

        # Migration 005: Adicionar coluna allocation_criteria
        try:
            migration_005_path = migrations_path / "005_add_allocation_criteria.py"
            if migration_005_path.exists():
                import importlib.util

                spec = importlib.util.spec_from_file_location("migration_005", migration_005_path)
                if spec and spec.loader:
                    migration_005 = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(migration_005)

                    # Executar migration (idempotente)
                    applied = migration_005.apply_if_needed(self._connection)
                    if applied:
                        print("[OK] Migration 005 aplicada: coluna allocation_criteria adicionada")
        except Exception as e:
            # Migration já aplicada ou erro - não falhar
            print(f"[INFO] Migration 005: {e}")
            pass

        # Migration 006: Adicionar coluna max_idle_days
        try:
            migration_006_path = migrations_path / "006_add_max_idle_days.py"
            if migration_006_path.exists():
                import importlib.util

                spec = importlib.util.spec_from_file_location("migration_006", migration_006_path)
                if spec and spec.loader:
                    migration_006 = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(migration_006)

                    # Executar migration (idempotente)
                    applied = migration_006.apply_if_needed(self._connection)
                    if applied:
                        print("[OK] Migration 006 aplicada: coluna max_idle_days adicionada")
        except Exception as e:
            # Migration já aplicada ou erro - não falhar
            print(f"[INFO] Migration 006: {e}")
            pass

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
