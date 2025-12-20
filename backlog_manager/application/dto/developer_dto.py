"""DTO para transferência de dados de Developer."""
from dataclasses import dataclass


@dataclass
class DeveloperDTO:
    """
    Data Transfer Object para Developer.

    Usado para transferir dados de desenvolvedores entre camadas.
    """

    id: str
    name: str
