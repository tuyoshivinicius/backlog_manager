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
        cursor.execute(
            """
            REPLACE INTO stories (
                id, feature, name, status, priority,
                developer_id, dependencies, story_point,
                start_date, end_date, duration, schedule_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                row_data["id"],
                row_data["feature"],
                row_data["name"],
                row_data["status"],
                row_data["priority"],
                row_data["developer_id"],
                row_data["dependencies"],
                row_data["story_point"],
                row_data["start_date"],
                row_data["end_date"],
                row_data["duration"],
                row_data["schedule_order"],
            ),
        )
        # IMPORTANTE: Fazer commit imediatamente para evitar deadlocks
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
        # IMPORTANTE: Fazer commit imediatamente para evitar deadlocks
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
            "id": story.id,
            "feature": story.feature,
            "name": story.name,
            "status": story.status.value,
            "priority": story.priority,
            "developer_id": story.developer_id,
            "dependencies": json.dumps(story.dependencies),
            "story_point": story.story_point.value,
            "start_date": story.start_date.isoformat() if story.start_date else None,
            "end_date": story.end_date.isoformat() if story.end_date else None,
            "duration": story.duration,
            "schedule_order": story.schedule_order,
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
            id=row["id"],
            feature=row["feature"],
            name=row["name"],
            status=StoryStatus(row["status"]),
            priority=row["priority"],
            developer_id=row["developer_id"],
            dependencies=json.loads(row["dependencies"]),
            story_point=StoryPoint(row["story_point"]),
            start_date=date.fromisoformat(row["start_date"]) if row["start_date"] else None,
            end_date=date.fromisoformat(row["end_date"]) if row["end_date"] else None,
            duration=row["duration"],
            schedule_order=row["schedule_order"] if "schedule_order" in row.keys() else None,
        )
