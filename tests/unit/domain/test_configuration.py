"""Testes unitários para entidade Configuration."""
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
