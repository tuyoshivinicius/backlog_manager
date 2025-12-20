"""DTO para backlog completo com metadados."""
from dataclasses import dataclass
from typing import List

from backlog_manager.application.dto.story_dto import StoryDTO


@dataclass
class BacklogDTO:
    """
    Data Transfer Object para backlog completo.

    Contém lista de histórias e metadados agregados.
    """

    stories: List[StoryDTO]
    total_count: int
    total_story_points: int
    estimated_duration_days: int
