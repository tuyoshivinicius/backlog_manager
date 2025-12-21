"""DTO para transferência de dados de Configuration."""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ConfigurationDTO:
    """
    Data Transfer Object para Configuration.

    Usado para transferir dados de configuração entre camadas.
    """

    story_points_per_sprint: int
    workdays_per_sprint: int
    velocity_per_day: float
    roadmap_start_date: Optional[date] = None
