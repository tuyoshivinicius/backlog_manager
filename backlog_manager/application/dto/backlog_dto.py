"""DTO para backlog completo com metadados."""
from dataclasses import dataclass
from typing import List, Optional

from backlog_manager.application.dto.story_dto import StoryDTO


@dataclass
class BacklogDTO:
    """
    Data Transfer Object para backlog completo.

    Contém lista de histórias e metadados agregados.

    Attributes:
        stories: Lista de histórias
        total_count: Número total de histórias
        total_story_points: Soma total de story points
        estimated_duration_days: Duração estimada em dias
        import_stats: Estatísticas de importação (opcional, apenas quando importado do Excel)
    """

    stories: List[StoryDTO]
    total_count: int
    total_story_points: int
    estimated_duration_days: int
    import_stats: Optional[dict] = None  # NOVO: estatísticas de importação
