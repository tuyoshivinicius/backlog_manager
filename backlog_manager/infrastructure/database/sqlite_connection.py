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
        """Executa migrações se banco for novo."""
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

    def _execute_schema(self) -> None:
        """Executa script de criação de schema."""
        schema_path = Path(__file__).parent / "schema.sql"

        with open(schema_path, "r", encoding="utf-8") as f:
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
