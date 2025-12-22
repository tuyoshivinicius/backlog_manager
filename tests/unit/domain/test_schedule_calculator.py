"""Testes para ScheduleCalculator."""
import time
from datetime import date

from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator
from backlog_manager.domain.value_objects.story_point import StoryPoint


class TestScheduleCalculator:
    """Testes para cálculo de cronograma."""

    def test_calculate_empty_list(self) -> None:
        """Deve retornar lista vazia para entrada vazia."""
        calculator = ScheduleCalculator()
        config = Configuration()

        result = calculator.calculate([], config)

        assert result == []

    def test_calculate_duration_simple(self) -> None:
        """Deve calcular duração corretamente."""
        calculator = ScheduleCalculator()
        config = Configuration(story_points_per_sprint=21, workdays_per_sprint=15)

        # Velocidade = 21/15 = 1.4 SP/dia
        # Story de 8 SP = ceil(8/1.4) = ceil(5.71) = 6 dias
        story = Story(id="S1", feature="Test", name="Test", story_point=StoryPoint(8))

        result = calculator.calculate([story], config)

        assert result[0].duration == 6

    def test_calculate_duration_various_story_points(self) -> None:
        """Deve calcular duração para diferentes story points."""
        calculator = ScheduleCalculator()
        config = Configuration(story_points_per_sprint=21, workdays_per_sprint=15)
        # Velocidade = 1.4 SP/dia

        test_cases = [
            (3, 3),  # ceil(3/1.4) = ceil(2.14) = 3
            (5, 4),  # ceil(5/1.4) = ceil(3.57) = 4
            (8, 6),  # ceil(8/1.4) = ceil(5.71) = 6
            (13, 10),  # ceil(13/1.4) = ceil(9.29) = 10
        ]

        for sp, expected_duration in test_cases:
            story = Story(id=f"S{sp}", feature="Test", name="Test", story_point=StoryPoint(sp))
            result = calculator.calculate([story], config)
            assert (
                result[0].duration == expected_duration
            ), f"SP {sp} should have duration {expected_duration}"

    def test_calculate_minimum_duration_one_day(self) -> None:
        """Duração mínima deve ser 1 dia."""
        calculator = ScheduleCalculator()
        # Velocidade muito alta
        config = Configuration(story_points_per_sprint=1000, workdays_per_sprint=10)

        story = Story(id="S1", feature="Test", name="Test", story_point=StoryPoint(3))

        result = calculator.calculate([story], config)

        assert result[0].duration >= 1

    def test_calculate_dates_single_story(self) -> None:
        """Deve calcular datas de início e fim corretamente."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)  # Segunda-feira

        story = Story(id="S1", feature="Test", name="Test", story_point=StoryPoint(5))

        result = calculator.calculate([story], config, start_date)

        assert result[0].start_date == date(2025, 1, 6)  # Segunda
        # Duração de 4 dias: seg, ter, qua, qui
        assert result[0].end_date == date(2025, 1, 9)  # Quinta

    def test_calculate_dates_skip_weekend(self) -> None:
        """Deve pular fins de semana no cálculo de datas."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 3)  # Sexta-feira

        # História com duração de 4 dias úteis (5 SP / 1.4 = 3.57, ceil = 4)
        story = Story(id="S1", feature="Test", name="Test", story_point=StoryPoint(5))

        result = calculator.calculate([story], config, start_date)

        assert result[0].start_date == date(2025, 1, 3)  # Sexta
        assert result[0].duration == 4  # 4 dias úteis
        # 4 dias: Sexta (3), Segunda (6), Terça (7), Quarta (8)
        assert result[0].end_date == date(2025, 1, 8)  # Quarta

    def test_calculate_sequential_stories_same_developer(self) -> None:
        """Histórias do mesmo desenvolvedor devem executar em sequência."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)  # Segunda

        story1 = Story(
            id="S1", feature="Test", name="Test1", story_point=StoryPoint(5), developer_id="DEV1"
        )
        story2 = Story(
            id="S2", feature="Test", name="Test2", story_point=StoryPoint(5), developer_id="DEV1"
        )

        result = calculator.calculate([story1, story2], config, start_date)

        # Story1: Segunda (6) a Quinta (9)
        assert result[0].start_date == date(2025, 1, 6)
        assert result[0].end_date == date(2025, 1, 9)

        # Story2: Sexta (10) a Quarta (15) - próximo dia após Story1
        assert result[1].start_date == date(2025, 1, 10)
        assert result[1].end_date == date(2025, 1, 15)

    def test_calculate_parallel_stories_different_developers(self) -> None:
        """Histórias de desenvolvedores diferentes devem executar em paralelo."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)  # Segunda

        story1 = Story(
            id="S1", feature="Test", name="Test1", story_point=StoryPoint(5), developer_id="DEV1"
        )
        story2 = Story(
            id="S2", feature="Test", name="Test2", story_point=StoryPoint(5), developer_id="DEV2"
        )

        result = calculator.calculate([story1, story2], config, start_date)

        # Ambas começam na mesma data
        assert result[0].start_date == date(2025, 1, 6)
        assert result[1].start_date == date(2025, 1, 6)

        # Ambas terminam na mesma data (mesma duração)
        assert result[0].end_date == date(2025, 1, 9)
        assert result[1].end_date == date(2025, 1, 9)

    def test_calculate_stories_without_developer(self) -> None:
        """Histórias sem desenvolvedor devem começar na data inicial."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)

        story1 = Story(id="S1", feature="Test", name="Test1", story_point=StoryPoint(5))
        story2 = Story(id="S2", feature="Test", name="Test2", story_point=StoryPoint(5))

        result = calculator.calculate([story1, story2], config, start_date)

        # Ambas sem dev, ambas começam na data inicial
        assert result[0].start_date == date(2025, 1, 6)
        assert result[1].start_date == date(2025, 1, 6)

    def test_calculate_mixed_allocated_and_unallocated(self) -> None:
        """Deve lidar com mix de histórias alocadas e não alocadas."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)

        story1 = Story(
            id="S1", feature="Test", name="Test1", story_point=StoryPoint(5), developer_id="DEV1"
        )
        story2 = Story(id="S2", feature="Test", name="Test2", story_point=StoryPoint(5))
        story3 = Story(
            id="S3", feature="Test", name="Test3", story_point=StoryPoint(5), developer_id="DEV1"
        )

        result = calculator.calculate([story1, story2, story3], config, start_date)

        # Story1 e Story3 (DEV1) em sequência
        assert result[0].start_date == date(2025, 1, 6)
        assert result[2].start_date == date(2025, 1, 10)  # Após Story1

        # Story2 sem dev, começa na data inicial
        assert result[1].start_date == date(2025, 1, 6)

    def test_calculate_start_on_weekend(self) -> None:
        """Se data inicial for fim de semana, deve ajustar."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 4)  # Sábado

        story = Story(id="S1", feature="Test", name="Test", story_point=StoryPoint(5))

        result = calculator.calculate([story], config, start_date)

        # Sábado (04/01) deve ser ajustado para segunda-feira (06/01)
        assert result[0].start_date == date(2025, 1, 6)  # Segunda
        # Duração de 4 dias: seg (06), ter (07), qua (08), qui (09)
        assert result[0].end_date == date(2025, 1, 9)  # Quinta

    def test_performance_large_backlog(self) -> None:
        """Deve calcular cronograma de backlog grande rapidamente."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)

        # 100 histórias
        stories = []
        for i in range(100):
            story = Story(
                id=f"S{i}",
                feature="Test",
                name=f"Test{i}",
                story_point=StoryPoint(5),
                developer_id=f"DEV{i % 10}",  # 10 desenvolvedores
            )
            stories.append(story)

        start_time = time.time()
        result = calculator.calculate(stories, config, start_date)
        elapsed = time.time() - start_time

        assert len(result) == 100
        assert all(s.duration is not None for s in result)
        assert all(s.start_date is not None for s in result)
        assert all(s.end_date is not None for s in result)
        assert elapsed < 1.0  # Deve ser < 1s

    def test_calculate_preserves_story_order(self) -> None:
        """Deve preservar ordem das histórias na entrada."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)

        story1 = Story(id="S1", feature="Test", name="Test1", story_point=StoryPoint(5))
        story2 = Story(id="S2", feature="Test", name="Test2", story_point=StoryPoint(8))
        story3 = Story(id="S3", feature="Test", name="Test3", story_point=StoryPoint(3))

        result = calculator.calculate([story1, story2, story3], config, start_date)

        assert result[0].id == "S1"
        assert result[1].id == "S2"
        assert result[2].id == "S3"

    def test_next_workday_after_friday(self) -> None:
        """Próximo dia útil após sexta deve ser segunda."""
        calculator = ScheduleCalculator()
        friday = date(2025, 1, 3)

        next_day = calculator._next_workday(friday)

        assert next_day == date(2025, 1, 6)  # Segunda
        assert next_day.weekday() == 0  # Segunda-feira

    def test_next_workday_after_thursday(self) -> None:
        """Próximo dia útil após quinta deve ser sexta."""
        calculator = ScheduleCalculator()
        thursday = date(2025, 1, 2)

        next_day = calculator._next_workday(thursday)

        assert next_day == date(2025, 1, 3)  # Sexta
        assert next_day.weekday() == 4  # Sexta-feira
