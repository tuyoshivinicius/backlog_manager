"""Caso de uso para alterar prioridade de história."""
import logging
from enum import Enum

from backlog_manager.application.dto.backlog_dto import BacklogDTO
from backlog_manager.application.dto.converters import story_to_dto
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import StoryNotFoundException

logger = logging.getLogger(__name__)


class Direction(Enum):
    """Direção do movimento de prioridade."""

    UP = "up"
    DOWN = "down"


class ChangePriorityUseCase:
    """
    Caso de uso para alterar prioridade de uma história.

    Move história para cima ou para baixo na lista de prioridades,
    ajustando prioridades das histórias afetadas.

    Responsabilidades:
    - Buscar história
    - Verificar limites (não pode mover topo para cima, etc)
    - Trocar prioridades com história adjacente
    - Persistir ambas
    - Retornar backlog atualizado ordenado por prioridade
    """

    def __init__(self, story_repository: StoryRepository):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
        """
        self._story_repository = story_repository

    def execute(self, story_id: str, direction: Direction) -> BacklogDTO:
        """
        Move história para cima ou para baixo na prioridade.

        Args:
            story_id: ID da história
            direction: Direção (UP ou DOWN)

        Returns:
            BacklogDTO com histórias ordenadas por prioridade

        Raises:
            StoryNotFoundException: Se história não existe
            ValueError: Se movimento inválido (já está no topo/fundo)
        """
        logger.info(f"Alterando prioridade: story_id='{story_id}', direction='{direction.value}'")

        # 1. Buscar história
        story = self._story_repository.find_by_id(story_id)

        if story is None:
            logger.error(f"História não encontrada: id='{story_id}'")
            raise StoryNotFoundException(story_id)

        # 2. Buscar todas histórias ordenadas por prioridade
        all_stories = self._story_repository.find_all()
        sorted_stories = sorted(all_stories, key=lambda s: s.priority)
        logger.debug(f"Total de histórias: {len(sorted_stories)}")

        # 3. Encontrar posição atual
        current_index = next((i for i, s in enumerate(sorted_stories) if s.id == story_id), None)

        if current_index is None:
            logger.error(f"História não encontrada no backlog: id='{story_id}'")
            raise StoryNotFoundException(story_id)

        logger.debug(f"Posição atual: {current_index}, prioridade: {story.priority}")

        # 4. Calcular nova posição
        if direction == Direction.UP:
            if current_index == 0:
                logger.warning(f"História já está no topo: id='{story_id}'")
                raise ValueError("História já está no topo da lista de prioridades")
            new_index = current_index - 1
        else:  # DOWN
            if current_index == len(sorted_stories) - 1:
                logger.warning(f"História já está no final: id='{story_id}'")
                raise ValueError("História já está no final da lista de prioridades")
            new_index = current_index + 1

        logger.debug(f"Nova posição: {new_index}")

        # 5. Validar movimento dentro da mesma onda
        story_to_move = sorted_stories[current_index]
        story_to_swap = sorted_stories[new_index]

        logger.debug(f"História a mover: id='{story_to_move.id}', feature_id={story_to_move.feature_id}")
        logger.debug(f"História a trocar: id='{story_to_swap.id}', feature_id={story_to_swap.feature_id}")

        # Verificar se ambas pertencem à mesma feature (mesma onda)
        if story_to_move.feature_id != story_to_swap.feature_id:
            # Uma delas não tem feature, ou têm features diferentes
            if story_to_move.feature_id is None and story_to_swap.feature_id is None:
                # Ambas sem feature - permitir movimento
                logger.debug("Ambas histórias sem feature - permitindo movimento")
                pass
            else:
                # Features diferentes - bloquear movimento
                logger.warning(
                    f"Movimento bloqueado: features diferentes "
                    f"('{story_to_move.feature_id}' vs '{story_to_swap.feature_id}')"
                )
                raise ValueError(
                    "Não é possível mover a história para outra onda. "
                    "A mudança de prioridade só é permitida dentro da mesma feature/onda."
                )

        # 6. Trocar prioridades

        # Guardar prioridades originais
        original_priority_move = story_to_move.priority
        original_priority_swap = story_to_swap.priority

        logger.debug(
            f"Trocando prioridades: '{story_to_move.id}' ({original_priority_move} -> {original_priority_swap}), "
            f"'{story_to_swap.id}' ({original_priority_swap} -> {original_priority_move})"
        )

        # Trocar
        story_to_move.priority = original_priority_swap
        story_to_swap.priority = original_priority_move

        # 7. Persistir ambas
        self._story_repository.save(story_to_move)
        self._story_repository.save(story_to_swap)
        logger.debug("Prioridades atualizadas e persistidas")

        # 8. Reordenar e retornar BacklogDTO
        all_stories_updated = self._story_repository.find_all()
        sorted_stories_updated = sorted(all_stories_updated, key=lambda s: s.priority)

        total_sp = sum(s.story_point.value for s in sorted_stories_updated)

        # Calcular duração total
        if sorted_stories_updated and sorted_stories_updated[0].start_date and sorted_stories_updated[-1].end_date:
            first_start = sorted_stories_updated[0].start_date
            last_end = sorted_stories_updated[-1].end_date
            duration_days = (last_end - first_start).days + 1
        else:
            duration_days = 0

        logger.info(
            f"Prioridade alterada com sucesso: '{story_id}' movida para posição {new_index}, "
            f"total de histórias: {len(sorted_stories_updated)}"
        )

        return BacklogDTO(
            stories=[story_to_dto(s) for s in sorted_stories_updated],
            total_count=len(sorted_stories_updated),
            total_story_points=total_sp,
            estimated_duration_days=duration_days,
        )
