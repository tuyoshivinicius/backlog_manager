"""Entidade Configuration (Configuração global)."""
from dataclasses import dataclass


@dataclass
class Configuration:
    """
    Configuração global do sistema para cálculo de cronograma.

    Attributes:
        story_points_per_sprint: Velocidade do time em SP por sprint
        workdays_per_sprint: Dias úteis em uma sprint
    """

    story_points_per_sprint: int = 21
    workdays_per_sprint: int = 15

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

    @property
    def velocity_per_day(self) -> float:
        """
        Calcula velocidade do time por dia útil.

        Returns:
            Story Points por dia útil
        """
        return self.story_points_per_sprint / self.workdays_per_sprint
