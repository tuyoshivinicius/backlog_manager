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
