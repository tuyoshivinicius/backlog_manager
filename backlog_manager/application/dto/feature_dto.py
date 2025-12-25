"""DTO para transferência de dados de Feature."""
from dataclasses import dataclass


@dataclass
class FeatureDTO:
    """
    Data Transfer Object para Feature.

    Usado para transferir dados de features entre camadas.
    """

    id: str
    name: str
    wave: int
