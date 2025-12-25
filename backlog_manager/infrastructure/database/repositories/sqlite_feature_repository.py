"""Implementação SQLite do repositório de features."""
import logging
import sqlite3
from typing import List, Optional

from backlog_manager.application.interfaces.repositories.feature_repository import FeatureRepository
from backlog_manager.domain.entities.feature import Feature
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection

logger = logging.getLogger(__name__)


class SQLiteFeatureRepository(FeatureRepository):
    """
    Implementação SQLite do repositório de features.

    Responsabilidades:
    - Persistir e recuperar features do banco SQLite
    - Converter entre Feature entity e rows do banco
    """

    def __init__(self, connection: SQLiteConnection):
        """
        Inicializa repositório.

        Args:
            connection: Conexão SQLite singleton
        """
        self._conn = connection.get_connection()

    def save(self, feature: Feature) -> None:
        """
        Salva ou atualiza feature no banco.

        Args:
            feature: Feature a ser salva
        """
        logger.debug(f"Salvando feature: id='{feature.id}', wave={feature.wave}")

        try:
            cursor = self._conn.cursor()

            # Verificar se feature já existe
            cursor.execute("SELECT 1 FROM features WHERE id = ?", (feature.id,))
            exists = cursor.fetchone() is not None

            if exists:
                # UPDATE para feature existente (evita DELETE que viola ON DELETE RESTRICT)
                logger.debug(f"Feature '{feature.id}' existe, usando UPDATE")
                cursor.execute(
                    """
                    UPDATE features
                    SET name = ?, wave = ?
                    WHERE id = ?
                    """,
                    (feature.name, feature.wave, feature.id),
                )
            else:
                # INSERT para nova feature
                logger.debug(f"Feature '{feature.id}' é nova, usando INSERT")
                cursor.execute(
                    """
                    INSERT INTO features (id, name, wave)
                    VALUES (?, ?, ?)
                    """,
                    (feature.id, feature.name, feature.wave),
                )

            logger.debug(f"Feature '{feature.id}' salva com sucesso")

            # Commit imediato para evitar "database is locked"
            # TODO: Migrar para UnitOfWork pattern no futuro
            self._conn.commit()
            logger.debug("Commit executado")

        except sqlite3.Error as e:
            logger.error(f"Erro ao salvar feature '{feature.id}': {e}", exc_info=True)
            self._conn.rollback()
            raise

    def find_by_id(self, feature_id: str) -> Optional[Feature]:
        """
        Busca feature por ID.

        Args:
            feature_id: ID da feature

        Returns:
            Feature se encontrada, None caso contrário
        """
        logger.debug(f"Buscando feature por ID: '{feature_id}'")

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM features WHERE id = ?", (feature_id,))
            row = cursor.fetchone()

            if row is None:
                logger.debug(f"Feature não encontrada: id='{feature_id}'")
                return None

            logger.debug(f"Feature encontrada: id='{feature_id}', wave={row['wave']}")
            return Feature(id=row["id"], name=row["name"], wave=row["wave"])

        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar feature '{feature_id}': {e}", exc_info=True)
            raise

    def find_by_wave(self, wave: int) -> Optional[Feature]:
        """
        Busca feature por número de onda.

        Args:
            wave: Número da onda

        Returns:
            Feature se encontrada, None caso contrário
        """
        logger.debug(f"Buscando feature por wave: {wave}")

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM features WHERE wave = ?", (wave,))
            row = cursor.fetchone()

            if row is None:
                logger.debug(f"Feature não encontrada para wave: {wave}")
                return None

            logger.debug(f"Feature encontrada para wave {wave}: id='{row['id']}'")
            return Feature(id=row["id"], name=row["name"], wave=row["wave"])

        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar feature por wave {wave}: {e}", exc_info=True)
            raise

    def find_all(self) -> List[Feature]:
        """
        Retorna todas features ordenadas por onda (ASC).

        Returns:
            Lista de features
        """
        logger.debug("Buscando todas as features")

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM features ORDER BY wave ASC")
            rows = cursor.fetchall()

            features = [Feature(id=row["id"], name=row["name"], wave=row["wave"]) for row in rows]
            logger.debug(f"Encontradas {len(features)} features")
            return features

        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar todas as features: {e}", exc_info=True)
            raise

    def delete(self, feature_id: str) -> None:
        """
        Remove feature do banco.

        Args:
            feature_id: ID da feature
        """
        logger.debug(f"Deletando feature: id='{feature_id}'")

        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM features WHERE id = ?", (feature_id,))
            logger.debug(f"Feature '{feature_id}' deletada com sucesso")

            # Commit imediato para evitar "database is locked"
            # TODO: Migrar para UnitOfWork pattern no futuro
            self._conn.commit()
            logger.debug("Commit executado")

        except sqlite3.Error as e:
            logger.error(f"Erro ao deletar feature '{feature_id}': {e}", exc_info=True)
            self._conn.rollback()
            raise

    def exists(self, feature_id: str) -> bool:
        """
        Verifica se feature existe.

        Args:
            feature_id: ID da feature

        Returns:
            True se existe, False caso contrário
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM features WHERE id = ? LIMIT 1", (feature_id,))
        return cursor.fetchone() is not None

    def wave_exists(self, wave: int) -> bool:
        """
        Verifica se já existe feature com determinada onda.

        Args:
            wave: Número da onda

        Returns:
            True se existe, False caso contrário
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM features WHERE wave = ? LIMIT 1", (wave,))
        return cursor.fetchone() is not None

    def count_stories_by_feature(self, feature_id: str) -> int:
        """
        Conta quantas histórias estão associadas a uma feature.

        Args:
            feature_id: ID da feature

        Returns:
            Número de histórias associadas
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM stories WHERE feature_id = ?", (feature_id,))
        row = cursor.fetchone()
        return row["count"] if row else 0
