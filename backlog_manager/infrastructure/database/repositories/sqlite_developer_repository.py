"""Implementação SQLite do repositório de desenvolvedores."""
import sqlite3
from typing import List, Optional

from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.domain.entities.developer import Developer
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


class SQLiteDeveloperRepository(DeveloperRepository):
    """
    Implementação SQLite do repositório de desenvolvedores.

    Responsabilidades:
    - Persistir e recuperar desenvolvedores do banco SQLite
    - Converter entre Developer entity e rows do banco
    """

    def __init__(self, connection: SQLiteConnection):
        """
        Inicializa repositório.

        Args:
            connection: Conexão SQLite singleton
        """
        self._conn = connection.get_connection()

    def save(self, developer: Developer) -> None:
        """
        Salva ou atualiza desenvolvedor no banco.

        Args:
            developer: Desenvolvedor a ser salvo
        """
        cursor = self._conn.cursor()
        cursor.execute(
            """
            REPLACE INTO developers (id, name)
            VALUES (?, ?)
        """,
            (developer.id, developer.name),
        )
        # IMPORTANTE: Fazer commit imediatamente para evitar deadlocks
        self._conn.commit()

    def find_by_id(self, developer_id: str) -> Optional[Developer]:
        """
        Busca desenvolvedor por ID.

        Args:
            developer_id: ID do desenvolvedor

        Returns:
            Developer se encontrado, None caso contrário
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM developers WHERE id = ?", (developer_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return Developer(id=row["id"], name=row["name"])

    def find_all(self) -> List[Developer]:
        """
        Retorna todos desenvolvedores ordenados por nome.

        Returns:
            Lista de desenvolvedores
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM developers ORDER BY name ASC")
        rows = cursor.fetchall()

        return [Developer(id=row["id"], name=row["name"]) for row in rows]

    def delete(self, developer_id: str) -> None:
        """
        Remove desenvolvedor do banco.

        Args:
            developer_id: ID do desenvolvedor
        """
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM developers WHERE id = ?", (developer_id,))
        # IMPORTANTE: Fazer commit imediatamente para evitar deadlocks
        self._conn.commit()

    def exists(self, developer_id: str) -> bool:
        """
        Verifica se desenvolvedor existe.

        Args:
            developer_id: ID do desenvolvedor

        Returns:
            True se existe, False caso contrário
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM developers WHERE id = ? LIMIT 1", (developer_id,))
        return cursor.fetchone() is not None

    def id_is_available(self, developer_id: str) -> bool:
        """
        Verifica se ID está disponível (não existe).

        Args:
            developer_id: ID a verificar

        Returns:
            True se ID disponível, False se já existe
        """
        return not self.exists(developer_id)
