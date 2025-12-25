"""Caso de uso para validar alocação de desenvolvedor."""
import logging
from typing import List, Tuple

from backlog_manager.application.interfaces.repositories.story_repository import (
    StoryRepository
)
from backlog_manager.domain.services.allocation_validator import (
    AllocationValidator,
    AllocationConflict
)

logger = logging.getLogger(__name__)


class ValidateDeveloperAllocationUseCase:
    """
    Valida se desenvolvedor pode ser alocado sem conflitos.

    Responsabilidades:
    - Buscar história no repositório
    - Buscar todas as histórias para comparação
    - Delegar validação para AllocationValidator
    - Retornar se alocação é válida e lista de conflitos
    """

    def __init__(
        self,
        story_repository: StoryRepository,
        validator: AllocationValidator
    ):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            validator: Validador de alocação
        """
        self._story_repo = story_repository
        self._validator = validator

    def execute(
        self,
        story_id: str,
        developer_id: str
    ) -> Tuple[bool, List[AllocationConflict]]:
        """
        Valida alocação de desenvolvedor.

        Args:
            story_id: ID da história
            developer_id: ID do desenvolvedor

        Returns:
            Tupla (is_valid: bool, conflicts: List[AllocationConflict])

        Example:
            >>> use_case = ValidateDeveloperAllocationUseCase(repo, validator)
            >>> is_valid, conflicts = use_case.execute("S1", "DEV1")
            >>> if not is_valid:
            ...     print(f"Conflitos: {[c.story_id for c in conflicts]}")
        """
        logger.info(f"Validando alocação: story_id='{story_id}', developer_id='{developer_id}'")

        # Buscar história
        story = self._story_repo.find_by_id(story_id)
        if not story:
            logger.debug(f"História não encontrada: id='{story_id}' - sem conflito")
            return True, []  # História não existe, sem conflito

        logger.debug(
            f"História encontrada: id='{story_id}', "
            f"período: {story.start_date} a {story.end_date}"
        )

        # Buscar todas as histórias
        all_stories = self._story_repo.find_all()
        logger.debug(f"Total de histórias para comparação: {len(all_stories)}")

        # Validar
        has_conflict, conflicts = self._validator.has_conflict(
            developer_id=developer_id,
            story_id=story_id,
            start_date=story.start_date,
            end_date=story.end_date,
            all_stories=all_stories
        )

        is_valid = not has_conflict
        if is_valid:
            logger.info(f"Alocação válida: sem conflitos para desenvolvedor '{developer_id}'")
        else:
            logger.warning(
                f"Alocação inválida: {len(conflicts)} conflito(s) detectado(s) "
                f"para desenvolvedor '{developer_id}'"
            )
            logger.debug(f"Conflitos: {[c.story_id for c in conflicts]}")

        return is_valid, conflicts
