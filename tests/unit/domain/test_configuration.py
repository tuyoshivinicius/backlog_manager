"""Testes unitários para entidade Configuration."""
from datetime import date

import pytest

from backlog_manager.domain.entities.configuration import Configuration


class TestConfiguration:
    """Testes para entidade Configuration."""

    def test_create_default_configuration(self) -> None:
        """Deve criar configuração com valores padrão."""
        config = Configuration()

        assert config.story_points_per_sprint == 21
        assert config.workdays_per_sprint == 15

    def test_create_custom_configuration(self) -> None:
        """Deve criar configuração com valores customizados."""
        config = Configuration(story_points_per_sprint=30, workdays_per_sprint=10)

        assert config.story_points_per_sprint == 30
        assert config.workdays_per_sprint == 10

    def test_reject_zero_story_points(self) -> None:
        """Deve rejeitar story points zero ou negativo."""
        with pytest.raises(ValueError, match="Story Points por sprint deve ser maior que zero"):
            Configuration(story_points_per_sprint=0)

        with pytest.raises(ValueError, match="Story Points por sprint deve ser maior que zero"):
            Configuration(story_points_per_sprint=-5)

    def test_reject_zero_workdays(self) -> None:
        """Deve rejeitar dias úteis zero ou negativo."""
        with pytest.raises(ValueError, match="Dias úteis por sprint deve ser maior que zero"):
            Configuration(workdays_per_sprint=0)

        with pytest.raises(ValueError, match="Dias úteis por sprint deve ser maior que zero"):
            Configuration(workdays_per_sprint=-3)

    def test_velocity_per_day(self) -> None:
        """Deve calcular velocidade por dia corretamente."""
        config = Configuration(story_points_per_sprint=21, workdays_per_sprint=15)

        assert config.velocity_per_day == pytest.approx(1.4, rel=0.01)

    def test_velocity_per_day_custom(self) -> None:
        """Deve calcular velocidade por dia com valores customizados."""
        config = Configuration(story_points_per_sprint=30, workdays_per_sprint=10)

        assert config.velocity_per_day == pytest.approx(3.0, rel=0.01)

    def test_create_configuration_with_roadmap_start_date(self) -> None:
        """Deve criar configuração com data de início do roadmap."""
        start_date = date(2025, 1, 6)  # Segunda-feira
        config = Configuration(
            story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=start_date
        )

        assert config.roadmap_start_date == start_date

    def test_create_configuration_without_roadmap_start_date(self) -> None:
        """Deve criar configuração sem data de início (None)."""
        config = Configuration(story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=None)

        assert config.roadmap_start_date is None

    def test_reject_weekend_roadmap_start_date(self) -> None:
        """Deve rejeitar data de início em fim de semana."""
        saturday = date(2025, 1, 4)  # Sábado
        with pytest.raises(ValueError, match="dia útil"):
            Configuration(story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=saturday)

        sunday = date(2025, 1, 5)  # Domingo
        with pytest.raises(ValueError, match="dia útil"):
            Configuration(story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=sunday)

    def test_accept_weekday_roadmap_start_date(self) -> None:
        """Deve aceitar data de início em dias úteis."""
        monday = date(2025, 1, 6)  # Segunda-feira
        config_mon = Configuration(story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=monday)
        assert config_mon.roadmap_start_date == monday

        friday = date(2025, 1, 10)  # Sexta-feira
        config_fri = Configuration(story_points_per_sprint=21, workdays_per_sprint=15, roadmap_start_date=friday)
        assert config_fri.roadmap_start_date == friday
