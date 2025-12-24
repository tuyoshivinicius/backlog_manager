"""Conversores entre Entities e DTOs."""
from backlog_manager.application.dto.configuration_dto import ConfigurationDTO
from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.domain.entities.developer import Developer
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


def story_to_dto(story: Story) -> StoryDTO:
    """
    Converte Story entity para StoryDTO.

    Args:
        story: Entidade Story

    Returns:
        StoryDTO correspondente
    """
    return StoryDTO(
        id=story.id,
        component=story.component,
        name=story.name,
        status=story.status.value,
        priority=story.priority,
        developer_id=story.developer_id,
        dependencies=story.dependencies.copy(),
        story_point=story.story_point.value,
        start_date=story.start_date,
        end_date=story.end_date,
        duration=story.duration,
    )


def dto_to_story(dto: StoryDTO) -> Story:
    """
    Converte StoryDTO para Story entity.

    Args:
        dto: StoryDTO

    Returns:
        Entidade Story correspondente

    Raises:
        ValueError: Se story_point for inválido
    """
    # Converter story_point se não for None
    story_point = None
    if dto.story_point is not None:
        story_point = StoryPoint(dto.story_point)

    return Story(
        id=dto.id,
        component=dto.component,
        name=dto.name,
        story_point=story_point,  # type: ignore
        status=StoryStatus.from_string(dto.status),
        priority=dto.priority,
        developer_id=dto.developer_id,
        dependencies=dto.dependencies.copy(),
        start_date=dto.start_date,
        end_date=dto.end_date,
        duration=dto.duration,
    )


def developer_to_dto(developer: Developer) -> DeveloperDTO:
    """
    Converte Developer entity para DeveloperDTO.

    Args:
        developer: Entidade Developer

    Returns:
        DeveloperDTO correspondente
    """
    return DeveloperDTO(id=developer.id, name=developer.name)


def dto_to_developer(dto: DeveloperDTO) -> Developer:
    """
    Converte DeveloperDTO para Developer entity.

    Args:
        dto: DeveloperDTO

    Returns:
        Entidade Developer correspondente
    """
    return Developer(id=dto.id, name=dto.name)


def configuration_to_dto(config: Configuration) -> ConfigurationDTO:
    """
    Converte Configuration entity para ConfigurationDTO.

    Args:
        config: Entidade Configuration

    Returns:
        ConfigurationDTO correspondente
    """
    return ConfigurationDTO(
        story_points_per_sprint=config.story_points_per_sprint,
        workdays_per_sprint=config.workdays_per_sprint,
        velocity_per_day=config.velocity_per_day,
        roadmap_start_date=config.roadmap_start_date,
    )


def dto_to_configuration(dto: ConfigurationDTO) -> Configuration:
    """
    Converte ConfigurationDTO para Configuration entity.

    Args:
        dto: ConfigurationDTO

    Returns:
        Entidade Configuration correspondente
    """
    return Configuration(
        story_points_per_sprint=dto.story_points_per_sprint, workdays_per_sprint=dto.workdays_per_sprint
    )
