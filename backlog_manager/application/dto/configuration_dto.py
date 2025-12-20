"""DTO para transferência de dados de Configuration."""
from dataclasses import dataclass


@dataclass
class ConfigurationDTO:
    """
    Data Transfer Object para Configuration.

    Usado para transferir dados de configuração entre camadas.
    """

    story_points_per_sprint: int
    workdays_per_sprint: int
    velocity_per_day: float
