"""Serviço para validar alocação de desenvolvedores."""
from typing import List, Optional, Tuple
from datetime import date
from backlog_manager.domain.entities.story import Story


class AllocationConflict:
    """Representa um conflito de alocação."""

    def __init__(
        self,
        story_id: str,
        developer_id: str,
        start_date: date,
        end_date: date
    ):
        """
        Inicializa conflito de alocação.

        Args:
            story_id: ID da história conflitante
            developer_id: ID do desenvolvedor
            start_date: Data início do período conflitante
            end_date: Data fim do período conflitante
        """
        self.story_id = story_id
        self.developer_id = developer_id
        self.start_date = start_date
        self.end_date = end_date

    def __str__(self) -> str:
        """Representação em string."""
        return (
            f"{self.story_id}: {self.developer_id} "
            f"({self.start_date.strftime('%d/%m/%Y')} - "
            f"{self.end_date.strftime('%d/%m/%Y')})"
        )


class AllocationValidator:
    """
    Serviço de domínio para validar alocação de desenvolvedores.

    Regra de Negócio:
    Um desenvolvedor não pode estar alocado a múltiplas histórias
    com períodos de execução sobrepostos.

    Exemplo de sobreposição:
    História A: 01/01 - 10/01
    História B: 05/01 - 15/01
    → Conflito! Períodos se sobrepõem de 05/01 a 10/01
    """

    @staticmethod
    def has_conflict(
        developer_id: str,
        story_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        all_stories: List[Story]
    ) -> Tuple[bool, List[AllocationConflict]]:
        """
        Verifica se há conflito ao alocar desenvolvedor.

        Args:
            developer_id: ID do desenvolvedor a alocar
            story_id: ID da história sendo alocada
            start_date: Data início da história
            end_date: Data fim da história
            all_stories: Lista de todas as histórias

        Returns:
            Tupla (has_conflict: bool, conflicts: List[AllocationConflict])

        Example:
            >>> validator = AllocationValidator()
            >>> stories = [...]
            >>> has_conflict, conflicts = validator.has_conflict(
            ...     "DEV1", "S2", date(2025,1,5), date(2025,1,15), stories
            ... )
            >>> if has_conflict:
            ...     print(f"Conflitos: {conflicts}")
        """
        # Se história não tem datas definidas, não há como haver conflito
        if not start_date or not end_date:
            return False, []

        conflicts = []

        for story in all_stories:
            # Ignorar a própria história
            if story.id == story_id:
                continue

            # Verificar se tem mesmo desenvolvedor
            if story.developer_id != developer_id:
                continue

            # Verificar se tem datas definidas
            if not story.start_date or not story.end_date:
                continue

            # Verificar sobreposição de períodos
            # Períodos se sobrepõem se: (A.start <= B.end) AND (B.start <= A.end)
            overlaps = AllocationValidator.periods_overlap(
                start_date, end_date,
                story.start_date, story.end_date
            )

            if overlaps:
                conflict = AllocationConflict(
                    story_id=story.id,
                    developer_id=story.developer_id,
                    start_date=story.start_date,
                    end_date=story.end_date
                )
                conflicts.append(conflict)

        return len(conflicts) > 0, conflicts

    @staticmethod
    def periods_overlap(
        start1: date,
        end1: date,
        start2: date,
        end2: date
    ) -> bool:
        """
        Verifica se dois períodos se sobrepõem.

        Algoritmo: Dois períodos se sobrepõem se o início de um
        é antes ou igual ao fim do outro, E vice-versa.

        Args:
            start1: Início do período 1
            end1: Fim do período 1
            start2: Início do período 2
            end2: Fim do período 2

        Returns:
            True se períodos se sobrepõem

        Example:
            >>> AllocationValidator.periods_overlap(
            ...     date(2025,1,1), date(2025,1,10),
            ...     date(2025,1,5), date(2025,1,15)
            ... )
            True
            >>> AllocationValidator.periods_overlap(
            ...     date(2025,1,1), date(2025,1,10),
            ...     date(2025,1,15), date(2025,1,20)
            ... )
            False
        """
        return start1 <= end2 and start2 <= end1
