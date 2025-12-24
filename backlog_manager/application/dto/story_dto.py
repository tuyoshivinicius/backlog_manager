"""DTO para transferência de dados de Story."""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class StoryDTO:
    """
    Data Transfer Object para Story.

    Usado para transferir dados de histórias entre camadas,
    isolando a entidade de domínio das camadas externas.
    """

    id: str
    component: str
    name: str
    status: str
    priority: int
    developer_id: Optional[str]
    dependencies: List[str]
    story_point: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    duration: Optional[int]

    def __post_init__(self) -> None:
        """Garante que dependencies é sempre uma lista."""
        if self.dependencies is None:
            self.dependencies = []
