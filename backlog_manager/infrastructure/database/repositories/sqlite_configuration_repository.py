"""Implementação SQLite do repositório de configuração."""
from backlog_manager.application.interfaces.repositories.configuration_repository import ConfigurationRepository
from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


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
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM configuration WHERE id = 1")
        row = cursor.fetchone()

        # Garantido existir (criado no schema)
        return Configuration(
            story_points_per_sprint=row["story_points_per_sprint"], workdays_per_sprint=row["workdays_per_sprint"]
        )

    def save(self, config: Configuration) -> None:
        """
        Atualiza configuração.

        Args:
            config: Configuração a salvar
        """
        cursor = self._conn.cursor()
        cursor.execute(
            """
            UPDATE configuration
            SET story_points_per_sprint = ?,
                workdays_per_sprint = ?
            WHERE id = 1
        """,
            (config.story_points_per_sprint, config.workdays_per_sprint),
        )
        # IMPORTANTE: Fazer commit imediatamente para evitar deadlocks
        self._conn.commit()
