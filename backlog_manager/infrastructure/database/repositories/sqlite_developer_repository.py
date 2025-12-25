"""Implementação SQLite do repositório de desenvolvedores."""
import logging
import sqlite3
from typing import List, Optional

from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.domain.entities.developer import Developer
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection

logger = logging.getLogger(__name__)


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
        logger.debug(f"Salvando desenvolvedor: id='{developer.id}'")

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                REPLACE INTO developers (id, name)
                VALUES (?, ?)
            """,
                (developer.id, developer.name),
            )
            logger.debug(f"Desenvolvedor '{developer.id}' salvo com sucesso")

            # Commit imediato para evitar "database is locked"
            # TODO: Migrar para UnitOfWork pattern no futuro
            self._conn.commit()
            logger.debug("Commit executado")

        except sqlite3.Error as e:
            logger.error(f"Erro ao salvar desenvolvedor '{developer.id}': {e}", exc_info=True)
            self._conn.rollback()
            raise

    def find_by_id(self, developer_id: str) -> Optional[Developer]:
        """
        Busca desenvolvedor por ID.

        Args:
            developer_id: ID do desenvolvedor

        Returns:
            Developer se encontrado, None caso contrário
        """
        logger.debug(f"Buscando desenvolvedor por ID: '{developer_id}'")

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM developers WHERE id = ?", (developer_id,))
            row = cursor.fetchone()

            if row is None:
                logger.debug(f"Desenvolvedor não encontrado: id='{developer_id}'")
                return None

            logger.debug(f"Desenvolvedor encontrado: id='{developer_id}'")
            return Developer(id=row["id"], name=row["name"])

        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar desenvolvedor '{developer_id}': {e}", exc_info=True)
            raise

    def find_all(self) -> List[Developer]:
        """
        Retorna todos desenvolvedores ordenados por nome.

        Returns:
            Lista de desenvolvedores
        """
        logger.debug("Buscando todos os desenvolvedores")

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM developers ORDER BY name ASC")
            rows = cursor.fetchall()

            developers = [Developer(id=row["id"], name=row["name"]) for row in rows]
            logger.debug(f"Encontrados {len(developers)} desenvolvedores")
            return developers

        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar todos os desenvolvedores: {e}", exc_info=True)
            raise

    def delete(self, developer_id: str) -> None:
        """
        Remove desenvolvedor do banco.

        Args:
            developer_id: ID do desenvolvedor
        """
        logger.debug(f"Deletando desenvolvedor: id='{developer_id}'")

        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM developers WHERE id = ?", (developer_id,))
            logger.debug(f"Desenvolvedor '{developer_id}' deletado com sucesso")

            # Commit imediato para evitar "database is locked"
            # TODO: Migrar para UnitOfWork pattern no futuro
            self._conn.commit()
            logger.debug("Commit executado")

        except sqlite3.Error as e:
            logger.error(f"Erro ao deletar desenvolvedor '{developer_id}': {e}", exc_info=True)
            self._conn.rollback()
            raise

    def exists(self, developer_id: str) -> bool:
        """
        Verifica se desenvolvedor existe.

        Args:
            developer_id: ID do desenvolvedor

        Returns:
            True se existe, False caso contrário
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT 1 FROM developers WHERE id = ? LIMIT 1", (developer_id,))
            exists = cursor.fetchone() is not None
            logger.debug(f"Desenvolvedor '{developer_id}' existe: {exists}")
            return exists

        except sqlite3.Error as e:
            logger.error(f"Erro ao verificar existência do desenvolvedor '{developer_id}': {e}", exc_info=True)
            raise

    def id_is_available(self, developer_id: str) -> bool:
        """
        Verifica se ID está disponível (não existe).

        Args:
            developer_id: ID a verificar

        Returns:
            True se ID disponível, False se já existe
        """
        return not self.exists(developer_id)
