"""Implementação SQLite do repositório de histórias."""
import json
import logging
import sqlite3
from datetime import date
from typing import List, Optional

from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.entities.feature import Feature
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus
from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection

logger = logging.getLogger(__name__)


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
        logger.debug(f"Salvando história: id='{story.id}'")

        try:
            row_data = self._entity_to_row(story)

            cursor = self._conn.cursor()

            # Usar REPLACE (UPDATE ou INSERT)
            cursor.execute(
                """
                REPLACE INTO stories (
                    id, component, name, status, priority, feature_id,
                    developer_id, dependencies, story_point,
                    start_date, end_date, duration, schedule_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    row_data["id"],
                    row_data["component"],
                    row_data["name"],
                    row_data["status"],
                    row_data["priority"],
                    row_data["feature_id"],
                    row_data["developer_id"],
                    row_data["dependencies"],
                    row_data["story_point"],
                    row_data["start_date"],
                    row_data["end_date"],
                    row_data["duration"],
                    row_data["schedule_order"],
                ),
            )
            logger.debug(f"História '{story.id}' salva com sucesso")

            # Commit imediato para evitar "database is locked"
            # TODO: Migrar para UnitOfWork pattern no futuro
            self._conn.commit()
            logger.debug("Commit executado")

        except sqlite3.Error as e:
            logger.error(f"Erro ao salvar história '{story.id}': {e}", exc_info=True)
            self._conn.rollback()
            raise

    def find_by_id(self, story_id: str) -> Optional[Story]:
        """
        Busca história por ID com eager loading da feature.

        Args:
            story_id: ID da história

        Returns:
            Story se encontrada, None caso contrário
        """
        logger.debug(f"Buscando história por ID: '{story_id}'")

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))

            row = cursor.fetchone()

            if row is None:
                logger.debug(f"História não encontrada: id='{story_id}'")
                return None

            story = self._row_to_entity(row)
            self.load_feature(story)  # Usa método público que valida feature_id is None
            logger.debug(f"História encontrada: id='{story_id}'")
            return story

        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar história '{story_id}': {e}", exc_info=True)
            raise

    def find_all(self) -> List[Story]:
        """
        Retorna todas histórias ordenadas por prioridade com eager loading de features.

        Returns:
            Lista de histórias
        """
        logger.debug("Buscando todas as histórias")

        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM stories ORDER BY priority ASC")

            rows = cursor.fetchall()

            stories = [self._row_to_entity(row) for row in rows]
            self._load_features_bulk(stories)
            logger.debug(f"Encontradas {len(stories)} histórias")
            return stories

        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar todas as histórias: {e}", exc_info=True)
            raise

    def delete(self, story_id: str) -> None:
        """
        Remove história do banco.

        Args:
            story_id: ID da história
        """
        logger.debug(f"Deletando história: id='{story_id}'")

        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM stories WHERE id = ?", (story_id,))
            logger.debug(f"História '{story_id}' deletada com sucesso")

            # Commit imediato para evitar "database is locked"
            # TODO: Migrar para UnitOfWork pattern no futuro
            self._conn.commit()
            logger.debug("Commit executado")

        except sqlite3.Error as e:
            logger.error(f"Erro ao deletar história '{story_id}': {e}", exc_info=True)
            self._conn.rollback()
            raise

    def exists(self, story_id: str) -> bool:
        """
        Verifica se história existe.

        Args:
            story_id: ID da história

        Returns:
            True se existe, False caso contrário
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT 1 FROM stories WHERE id = ? LIMIT 1", (story_id,))
            exists = cursor.fetchone() is not None
            logger.debug(f"História '{story_id}' existe: {exists}")
            return exists

        except sqlite3.Error as e:
            logger.error(f"Erro ao verificar existência da história '{story_id}': {e}", exc_info=True)
            raise

    def load_feature(self, story: Story) -> None:
        """
        Carrega a feature associada à história.

        Args:
            story: História para carregar a feature
        """
        if story.feature_id is None:
            logger.debug(f"História '{story.id}' não possui feature associada")
            story.feature = None
            return

        logger.debug(f"Carregando feature para história: id='{story.id}', feature_id='{story.feature_id}'")
        self._load_feature(story)

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
            "component": story.component,
            "name": story.name,
            "status": story.status.value,
            "priority": story.priority,
            "feature_id": story.feature_id,
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
        # Converter string "None" para None (dados corrompidos históricos)
        feature_id = row["feature_id"]
        if feature_id == "None" or feature_id == "" or feature_id == "(Nenhuma)":
            feature_id = None

        return Story(
            id=row["id"],
            component=row["component"],
            name=row["name"],
            status=StoryStatus(row["status"]),
            priority=row["priority"],
            feature_id=feature_id,
            developer_id=row["developer_id"],
            dependencies=json.loads(row["dependencies"]),
            story_point=StoryPoint(row["story_point"]),
            start_date=date.fromisoformat(row["start_date"]) if row["start_date"] else None,
            end_date=date.fromisoformat(row["end_date"]) if row["end_date"] else None,
            duration=row["duration"],
            schedule_order=row["schedule_order"] if "schedule_order" in row.keys() else None,
        )

    def _load_feature(self, story: Story) -> None:
        """
        Carrega feature para uma única história.

        Args:
            story: História para carregar feature
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM features WHERE id = ?", (story.feature_id,))
        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"Feature '{story.feature_id}' não encontrada para história '{story.id}'. "
                "Dados inconsistentes no banco."
            )

        story.feature = Feature(id=row["id"], name=row["name"], wave=row["wave"])

    def _load_features_bulk(self, stories: List[Story]) -> None:
        """
        Carrega features para múltiplas histórias em bulk (evita N+1 queries).

        Args:
            stories: Lista de histórias para carregar features
        """
        if not stories:
            return

        # 1. Coletar feature_ids únicos (excluindo None)
        feature_ids = list(set(story.feature_id for story in stories if story.feature_id is not None))

        # Se não há feature_ids, apenas definir feature=None para todas
        if not feature_ids:
            for story in stories:
                story.feature = None
            return

        # 2. Buscar todas features em uma única query
        cursor = self._conn.cursor()
        placeholders = ",".join("?" * len(feature_ids))
        cursor.execute(f"SELECT * FROM features WHERE id IN ({placeholders})", feature_ids)
        rows = cursor.fetchall()

        # 3. Criar map de features
        feature_map = {row["id"]: Feature(id=row["id"], name=row["name"], wave=row["wave"]) for row in rows}

        # 4. Associar features às histórias
        for story in stories:
            if story.feature_id is None:
                # História sem feature associada
                story.feature = None
            elif story.feature_id in feature_map:
                story.feature = feature_map[story.feature_id]
            else:
                raise ValueError(
                    f"Feature '{story.feature_id}' não encontrada para história '{story.id}'. "
                    "Dados inconsistentes no banco."
                )
