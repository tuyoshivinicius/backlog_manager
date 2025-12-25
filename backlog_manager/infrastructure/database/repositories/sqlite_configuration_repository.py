"""Implementação SQLite do repositório de configuração."""
import logging
from datetime import date

from backlog_manager.application.interfaces.repositories.configuration_repository import ConfigurationRepository
from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection

logger = logging.getLogger(__name__)


class SQLiteConfigurationRepository(ConfigurationRepository):
    """
    Implementação SQLite do repositório de configuração.

    Responsabilidades:
    - Persistir e recuperar configuração do banco SQLite
    - Singleton: Sempre ID=1
    """

    def __init__(self, connection: SQLiteConnection):
        """
        Inicializa repositório.

        Args:
            connection: Conexão SQLite singleton
        """
        self._conn = connection.get_connection()

    def get(self) -> Configuration:
        """
        Retorna configuração (sempre existe ID=1).

        Returns:
            Configuration entity
        """
        logger.debug("Buscando configuração")

        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT
                    story_points_per_sprint,
                    workdays_per_sprint,
                    roadmap_start_date
                FROM configuration
                WHERE id = 1
            """)
            row = cursor.fetchone()

            # Garantido existir (criado no schema)
            config = Configuration(
                story_points_per_sprint=row["story_points_per_sprint"],
                workdays_per_sprint=row["workdays_per_sprint"],
                roadmap_start_date=date.fromisoformat(row["roadmap_start_date"]) if row["roadmap_start_date"] else None,
            )
            logger.debug(
                f"Configuração carregada: story_points_per_sprint={config.story_points_per_sprint}, "
                f"workdays_per_sprint={config.workdays_per_sprint}"
            )
            return config

        except Exception as e:
            logger.error(f"Erro ao buscar configuração: {e}", exc_info=True)
            raise

    def save(self, config: Configuration) -> None:
        """
        Atualiza configuração.

        Args:
            config: Configuração a salvar
        """
        logger.debug(
            f"Salvando configuração: story_points_per_sprint={config.story_points_per_sprint}, "
            f"workdays_per_sprint={config.workdays_per_sprint}"
        )

        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                UPDATE configuration
                SET story_points_per_sprint = ?,
                    workdays_per_sprint = ?,
                    roadmap_start_date = ?
                WHERE id = 1
            """,
                (
                    config.story_points_per_sprint,
                    config.workdays_per_sprint,
                    config.roadmap_start_date.isoformat() if config.roadmap_start_date else None,
                ),
            )
            logger.debug("Configuração salva com sucesso")

            # Commit imediato para evitar "database is locked"
            # TODO: Migrar para UnitOfWork pattern no futuro
            self._conn.commit()
            logger.debug("Commit executado")

        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}", exc_info=True)
            self._conn.rollback()
            raise
