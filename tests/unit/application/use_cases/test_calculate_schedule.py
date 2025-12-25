"""Testes unitários para CalculateScheduleUseCase."""
import logging
from datetime import date
from unittest.mock import Mock, call

import pytest

from backlog_manager.application.use_cases.schedule.calculate_schedule import CalculateScheduleUseCase
from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.domain.entities.feature import Feature
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


class TestCalculateScheduleUseCase:
    """Testes para CalculateScheduleUseCase."""

    def test_renumber_priorities_after_sorting(self) -> None:
        """Deve renumerar priorities para 0, 1, 2, 3... após ordenação."""
        # Arrange
        story_repo = Mock()
        config_repo = Mock()
        backlog_sorter = Mock()
        schedule_calculator = Mock()

        feature = Feature(id="F1", name="Feature 1", wave=1)

        # Histórias com priorities não sequenciais
        story1 = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=10, dependencies=[]
        )
        story1.feature = feature

        story2 = Story(
            id="S2", component="Core", name="Story 2", story_point=StoryPoint(3),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=25, dependencies=[]
        )
        story2.feature = feature

        story3 = Story(
            id="S3", component="Core", name="Story 3", story_point=StoryPoint(8),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=50, dependencies=[]
        )
        story3.feature = feature

        # Sorter retorna as histórias em ordem diferente
        sorted_stories = [story2, story1, story3]

        config = Configuration(
            story_points_per_sprint=10, workdays_per_sprint=10,
            roadmap_start_date=date(2025, 1, 1)
        )

        story_repo.find_all.return_value = [story1, story2, story3]
        config_repo.get.return_value = config
        backlog_sorter.sort.return_value = sorted_stories
        schedule_calculator.calculate.return_value = sorted_stories

        use_case = CalculateScheduleUseCase(story_repo, config_repo, backlog_sorter, schedule_calculator)

        # Act
        result = use_case.execute()

        # Assert
        # Verifica que priorities foram renumeradas
        assert story2.priority == 0  # Primeira na ordenação
        assert story1.priority == 1  # Segunda na ordenação
        assert story3.priority == 2  # Terceira na ordenação

        # Verifica que schedule_order também foi atualizado
        assert story2.schedule_order == 0
        assert story1.schedule_order == 1
        assert story3.schedule_order == 2

    def test_renumber_priorities_with_waves(self) -> None:
        """Deve renumerar priorities respeitando ordenação por onda."""
        # Arrange
        story_repo = Mock()
        config_repo = Mock()
        backlog_sorter = Mock()
        schedule_calculator = Mock()

        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)

        # Histórias em ondas diferentes
        s_wave2_a = Story(
            id="S2A", component="Core", name="Story Wave 2A", story_point=StoryPoint(5),
            feature_id="F2", status=StoryStatus.BACKLOG, priority=5, dependencies=[]
        )
        s_wave2_a.feature = feature_wave2

        s_wave1_a = Story(
            id="S1A", component="Core", name="Story Wave 1A", story_point=StoryPoint(3),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=20, dependencies=[]
        )
        s_wave1_a.feature = feature_wave1

        s_wave1_b = Story(
            id="S1B", component="Core", name="Story Wave 1B", story_point=StoryPoint(8),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=30, dependencies=[]
        )
        s_wave1_b.feature = feature_wave1

        # Sorter retorna ordenado por wave (wave 1 antes de wave 2)
        sorted_stories = [s_wave1_a, s_wave1_b, s_wave2_a]

        config = Configuration(
            story_points_per_sprint=10, workdays_per_sprint=10,
            roadmap_start_date=date(2025, 1, 1)
        )

        story_repo.find_all.return_value = [s_wave2_a, s_wave1_a, s_wave1_b]
        config_repo.get.return_value = config
        backlog_sorter.sort.return_value = sorted_stories
        schedule_calculator.calculate.return_value = sorted_stories

        use_case = CalculateScheduleUseCase(story_repo, config_repo, backlog_sorter, schedule_calculator)

        # Act
        result = use_case.execute()

        # Assert
        # Wave 1 vem primeiro
        assert s_wave1_a.priority == 0
        assert s_wave1_b.priority == 1
        # Wave 2 vem depois
        assert s_wave2_a.priority == 2

    def test_logging_priority_adjustments(self, caplog) -> None:
        """Deve logar ajustes de prioridade."""
        # Arrange
        story_repo = Mock()
        config_repo = Mock()
        backlog_sorter = Mock()
        schedule_calculator = Mock()

        feature = Feature(id="F1", name="Feature 1", wave=1)

        story1 = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=100, dependencies=[]
        )
        story1.feature = feature

        story2 = Story(
            id="S2", component="Core", name="Story 2", story_point=StoryPoint(3),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=200, dependencies=[]
        )
        story2.feature = feature

        sorted_stories = [story1, story2]

        config = Configuration(
            story_points_per_sprint=10, workdays_per_sprint=10,
            roadmap_start_date=date(2025, 1, 1)
        )

        story_repo.find_all.return_value = [story1, story2]
        config_repo.get.return_value = config
        backlog_sorter.sort.return_value = sorted_stories
        schedule_calculator.calculate.return_value = sorted_stories

        use_case = CalculateScheduleUseCase(story_repo, config_repo, backlog_sorter, schedule_calculator)

        # Act
        with caplog.at_level(logging.INFO):
            result = use_case.execute()

        # Assert
        # Verifica logs de renumeração
        assert "Renumerando priorities para 2 histórias" in caplog.text
        assert "Renumeração concluída: 2 ajustes em 2 histórias" in caplog.text

    def test_logging_no_adjustments_needed(self, caplog) -> None:
        """Deve logar quando não há ajustes necessários."""
        # Arrange
        story_repo = Mock()
        config_repo = Mock()
        backlog_sorter = Mock()
        schedule_calculator = Mock()

        feature = Feature(id="F1", name="Feature 1", wave=1)

        # Histórias já com priorities corretas (0, 1)
        story1 = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story1.feature = feature

        story2 = Story(
            id="S2", component="Core", name="Story 2", story_point=StoryPoint(3),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=1, dependencies=[]
        )
        story2.feature = feature

        sorted_stories = [story1, story2]

        config = Configuration(
            story_points_per_sprint=10, workdays_per_sprint=10,
            roadmap_start_date=date(2025, 1, 1)
        )

        story_repo.find_all.return_value = [story1, story2]
        config_repo.get.return_value = config
        backlog_sorter.sort.return_value = sorted_stories
        schedule_calculator.calculate.return_value = sorted_stories

        use_case = CalculateScheduleUseCase(story_repo, config_repo, backlog_sorter, schedule_calculator)

        # Act
        with caplog.at_level(logging.INFO):
            result = use_case.execute()

        # Assert
        assert "Renumeração concluída: 0 ajustes em 2 histórias" in caplog.text

    def test_empty_backlog(self) -> None:
        """Deve retornar backlog vazio quando não há histórias."""
        # Arrange
        story_repo = Mock()
        config_repo = Mock()
        backlog_sorter = Mock()
        schedule_calculator = Mock()

        config = Configuration(
            story_points_per_sprint=10, workdays_per_sprint=10,
            roadmap_start_date=date(2025, 1, 1)
        )

        story_repo.find_all.return_value = []
        config_repo.get.return_value = config

        use_case = CalculateScheduleUseCase(story_repo, config_repo, backlog_sorter, schedule_calculator)

        # Act
        result = use_case.execute()

        # Assert
        assert result.total_count == 0
        assert result.total_story_points == 0
        assert result.estimated_duration_days == 0
        assert result.stories == []

        # Não deve chamar sorter nem calculator
        backlog_sorter.sort.assert_not_called()
        schedule_calculator.calculate.assert_not_called()

    def test_deallocate_developers_on_calculate(self) -> None:
        """Deve desalocar todos desenvolvedores ao calcular cronograma."""
        # Arrange
        story_repo = Mock()
        config_repo = Mock()
        backlog_sorter = Mock()
        schedule_calculator = Mock()

        feature = Feature(id="F1", name="Feature 1", wave=1)

        # Histórias com desenvolvedores alocados
        story1 = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story1.feature = feature
        story1.developer_id = 1  # Alocado

        story2 = Story(
            id="S2", component="Core", name="Story 2", story_point=StoryPoint(3),
            feature_id="F1", status=StoryStatus.BACKLOG, priority=1, dependencies=[]
        )
        story2.feature = feature
        story2.developer_id = 2  # Alocado

        sorted_stories = [story1, story2]

        config = Configuration(
            story_points_per_sprint=10, workdays_per_sprint=10,
            roadmap_start_date=date(2025, 1, 1)
        )

        story_repo.find_all.return_value = [story1, story2]
        config_repo.get.return_value = config
        backlog_sorter.sort.return_value = sorted_stories
        schedule_calculator.calculate.return_value = sorted_stories

        use_case = CalculateScheduleUseCase(story_repo, config_repo, backlog_sorter, schedule_calculator)

        # Act
        result = use_case.execute()

        # Assert
        # Verifica que desalocou desenvolvedores
        assert story1.developer_id is None
        assert story2.developer_id is None
