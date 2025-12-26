"""Entidade Configuration (Configuração global)."""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from backlog_manager.domain.value_objects.allocation_criteria import AllocationCriteria


@dataclass
class Configuration:
    """
    Configuração global do sistema para cálculo de cronograma.

    Attributes:
        story_points_per_sprint: Velocidade do time em SP por sprint
        workdays_per_sprint: Dias úteis em uma sprint
        roadmap_start_date: Data de início do roadmap (opcional)
        allocation_criteria: Critério de alocação de desenvolvedores
        max_idle_days: Máximo de dias úteis ociosos permitidos DENTRO DA MESMA ONDA
    """

    story_points_per_sprint: int = 21
    workdays_per_sprint: int = 15
    roadmap_start_date: Optional[date] = None
    allocation_criteria: AllocationCriteria = AllocationCriteria.LOAD_BALANCING
    max_idle_days: int = 3  # Padrão: 3 dias úteis de ociosidade máxima (mín: 2)

    def __post_init__(self) -> None:
        """Valida configuração."""
        self._validate()

    def _validate(self) -> None:
        """
        Valida valores de configuração.

        Raises:
            ValueError: Se valores inválidos
        """
        if self.story_points_per_sprint <= 0:
            raise ValueError("Story Points por sprint deve ser maior que zero")

        if self.workdays_per_sprint <= 0:
            raise ValueError("Dias úteis por sprint deve ser maior que zero")

        if self.roadmap_start_date is not None and self.roadmap_start_date.weekday() >= 5:
            raise ValueError("Data de início do roadmap deve ser um dia útil (segunda a sexta)")

        if self.max_idle_days < 2:
            raise ValueError("Ociosidade máxima deve ser pelo menos 2 dias")

    @property
    def velocity_per_day(self) -> float:
        """
        Calcula velocidade do time por dia útil.

        Returns:
            Story Points por dia útil
        """
        return self.story_points_per_sprint / self.workdays_per_sprint
