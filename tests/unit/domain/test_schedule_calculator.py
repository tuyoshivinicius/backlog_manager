"""Testes para ScheduleCalculator."""
import time
from datetime import date

from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.domain.entities.feature import Feature
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator
from backlog_manager.domain.value_objects.story_point import StoryPoint


def create_story_with_wave(
    id: str,
    wave: int = 1,
    story_points: int = 5,
    dependencies: list[str] | None = None,
    developer_id: str | None = None,
) -> Story:
    """Cria história com feature mockada para testes de onda."""
    feature = Feature(id=f"F{wave}", name=f"Feature {wave}", wave=wave) if wave > 0 else None
    return Story(
        id=id,
        component="TEST",
        name=f"Story {id}",
        story_point=StoryPoint(story_points),
        feature_id=feature.id if feature else None,
        feature=feature,
        dependencies=dependencies or [],
        developer_id=developer_id,
    )


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
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(8))

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
            story = Story(id=f"S{sp}", component="Test", name="Test", story_point=StoryPoint(sp))
            result = calculator.calculate([story], config)
            assert (
                result[0].duration == expected_duration
            ), f"SP {sp} should have duration {expected_duration}"

    def test_calculate_minimum_duration_one_day(self) -> None:
        """Duração mínima deve ser 1 dia."""
        calculator = ScheduleCalculator()
        # Velocidade muito alta
        config = Configuration(story_points_per_sprint=1000, workdays_per_sprint=10)

        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(3))

        result = calculator.calculate([story], config)

        assert result[0].duration >= 1

    def test_calculate_dates_single_story(self) -> None:
        """Deve calcular datas de início e fim corretamente."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)  # Segunda-feira

        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

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
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

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
            id="S1", component="Test", name="Test1", story_point=StoryPoint(5), developer_id="DEV1"
        )
        story2 = Story(
            id="S2", component="Test", name="Test2", story_point=StoryPoint(5), developer_id="DEV1"
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
            id="S1", component="Test", name="Test1", story_point=StoryPoint(5), developer_id="DEV1"
        )
        story2 = Story(
            id="S2", component="Test", name="Test2", story_point=StoryPoint(5), developer_id="DEV2"
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

        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5))
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5))

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
            id="S1", component="Test", name="Test1", story_point=StoryPoint(5), developer_id="DEV1"
        )
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5))
        story3 = Story(
            id="S3", component="Test", name="Test3", story_point=StoryPoint(5), developer_id="DEV1"
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

        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

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
                component="Test",
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

        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5))
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(8))
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(3))

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

    def test_is_workday_excludes_holidays(self) -> None:
        """Deve considerar feriados como não úteis."""
        calculator = ScheduleCalculator()

        # 01/01/2026 é quinta-feira E feriado
        assert not calculator._is_workday(date(2026, 1, 1))

        # 08/01/2026 é quinta-feira normal
        assert calculator._is_workday(date(2026, 1, 8))

    def test_add_workdays_skips_holidays(self) -> None:
        """Deve pular feriados ao adicionar dias úteis."""
        calculator = ScheduleCalculator()

        # 31/12/2025 (qua) + 2 dias úteis
        # Deve pular 01/01/2026 (qui - feriado) e fim de semana
        # Resultado: 05/01/2026 (seg)
        result = calculator.add_workdays(date(2025, 12, 31), 2)
        assert result == date(2026, 1, 5)

    def test_ensure_workday_skips_holiday(self) -> None:
        """Deve avançar para próximo dia útil se data for feriado."""
        calculator = ScheduleCalculator()

        # 01/01/2026 (qui - feriado) → 02/01/2026 (sex)
        result = calculator._ensure_workday(date(2026, 1, 1))
        assert result == date(2026, 1, 2)

    # ========================================
    # Testes de Barreira de Onda (Wave Barrier)
    # ========================================

    def test_wave_barrier_prevents_overlap(self) -> None:
        """Histórias de onda 2 só podem iniciar após onda 1 terminar."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)  # Segunda-feira

        # Onda 1: 1 história de 4 dias (5 SP)
        story1 = create_story_with_wave("S1", wave=1, story_points=5)
        # Onda 2: 1 história de 4 dias (5 SP)
        story2 = create_story_with_wave("S2", wave=2, story_points=5)

        result = calculator.calculate([story1, story2], config, start_date)

        # Story1 (onda 1): Segunda (6) a Quinta (9)
        assert result[0].start_date == date(2025, 1, 6)
        assert result[0].end_date == date(2025, 1, 9)

        # Story2 (onda 2): Deve iniciar APÓS story1 terminar (sexta 10)
        assert result[1].start_date == date(2025, 1, 10)
        assert result[1].start_date > result[0].end_date

    def test_non_contiguous_waves(self) -> None:
        """Onda 3 deve aguardar onda 1 mesmo sem onda 2."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)  # Segunda-feira

        # Onda 1: 1 história
        story1 = create_story_with_wave("S1", wave=1, story_points=5)
        # Onda 3 (sem onda 2): 1 história
        story3 = create_story_with_wave("S3", wave=3, story_points=5)

        result = calculator.calculate([story1, story3], config, start_date)

        # Story1 (onda 1): Segunda (6) a Quinta (9)
        assert result[0].end_date == date(2025, 1, 9)

        # Story3 (onda 3): Deve iniciar após onda 1 terminar
        assert result[1].start_date == date(2025, 1, 10)
        assert result[1].start_date > result[0].end_date

    def test_wave_zero_does_not_block(self) -> None:
        """Wave 0 (histórias sem feature) não bloqueia outras ondas."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)  # Segunda-feira

        # Wave 0: história sem feature
        story0 = create_story_with_wave("S0", wave=0, story_points=5)
        # Wave 1: história com feature
        story1 = create_story_with_wave("S1", wave=1, story_points=5)

        result = calculator.calculate([story0, story1], config, start_date)

        # Story0 (wave 0): Segunda (6) a Quinta (9)
        assert result[0].start_date == date(2025, 1, 6)

        # Story1 (wave 1): Também começa segunda (6) - wave 0 não bloqueia
        assert result[1].start_date == date(2025, 1, 6)

    def test_dependency_and_wave_barrier(self) -> None:
        """A maior restrição (dependência ou barreira de onda) prevalece."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)  # Segunda-feira

        # Onda 1: história curta (1 dia)
        story1 = create_story_with_wave("S1", wave=1, story_points=3)

        # Onda 2: história que também depende de S1
        story2 = create_story_with_wave("S2", wave=2, story_points=5, dependencies=["S1"])

        # Onda 2: segunda história longa (sem dependência de S1)
        story3 = create_story_with_wave("S3", wave=2, story_points=8)

        result = calculator.calculate([story1, story2, story3], config, start_date)

        # Story1 (onda 1): Segunda (6) a Quarta (8) - 3 dias
        assert result[0].end_date == date(2025, 1, 8)

        # Story2 (onda 2): Deve iniciar após story1 (dependência e barreira coincidem)
        assert result[1].start_date == date(2025, 1, 9)

        # Story3 (onda 2): Também deve respeitar barreira de onda
        assert result[2].start_date == date(2025, 1, 9)

    def test_multiple_stories_same_wave(self) -> None:
        """Múltiplas histórias da mesma onda podem iniciar na mesma data."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)  # Segunda-feira

        # Onda 1: duas histórias sem dependências entre si
        story1 = create_story_with_wave("S1", wave=1, story_points=5)
        story2 = create_story_with_wave("S2", wave=1, story_points=8)

        result = calculator.calculate([story1, story2], config, start_date)

        # Ambas devem começar na mesma data (sem dev, sem deps)
        assert result[0].start_date == date(2025, 1, 6)
        assert result[1].start_date == date(2025, 1, 6)

    def test_wave_end_date_uses_latest_story(self) -> None:
        """Barreira de onda deve usar a data de fim da última história da onda anterior."""
        calculator = ScheduleCalculator()
        config = Configuration()
        start_date = date(2025, 1, 6)  # Segunda-feira

        # Onda 1: história curta (3 dias)
        story1 = create_story_with_wave("S1", wave=1, story_points=3)
        # Onda 1: história longa (6 dias)
        story2 = create_story_with_wave("S2", wave=1, story_points=8)
        # Onda 2: deve esperar história mais longa da onda 1
        story3 = create_story_with_wave("S3", wave=2, story_points=5)

        result = calculator.calculate([story1, story2, story3], config, start_date)

        # Story1 (onda 1): Segunda (6) a Quarta (8) - 3 dias
        assert result[0].end_date == date(2025, 1, 8)

        # Story2 (onda 1): Segunda (6) a Segunda (13) - 6 dias
        assert result[1].end_date == date(2025, 1, 13)

        # Story3 (onda 2): Deve iniciar após story2 (a mais longa da onda 1)
        assert result[2].start_date == date(2025, 1, 14)
        assert result[2].start_date > result[1].end_date
