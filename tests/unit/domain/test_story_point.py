"""Testes unitários para StoryPoint value object."""
import pytest

from backlog_manager.domain.value_objects.story_point import StoryPoint


class TestStoryPoint:
    """Testes para StoryPoint."""

    def test_create_valid_story_point(self) -> None:
        """Deve criar StoryPoint com valores válidos."""
        for value in [3, 5, 8, 13]:
            sp = StoryPoint(value)
            assert sp.value == value

    def test_reject_invalid_story_point(self) -> None:
        """Deve rejeitar valores inválidos."""
        invalid_values = [1, 2, 4, 6, 7, 9, 10, 21, 0, -1]
        for value in invalid_values:
            with pytest.raises(ValueError, match="Story Point inválido"):
                StoryPoint(value)

    def test_story_point_equality(self) -> None:
        """Deve comparar igualdade corretamente."""
        sp1 = StoryPoint(5)
        sp2 = StoryPoint(5)
        sp3 = StoryPoint(8)

        assert sp1 == sp2
        assert sp1 != sp3

    def test_story_point_hashable(self) -> None:
        """Deve ser hashable para uso em sets."""
        sp1 = StoryPoint(5)
        sp2 = StoryPoint(5)
        sp3 = StoryPoint(8)

        story_points_set = {sp1, sp2, sp3}
        assert len(story_points_set) == 2

    def test_from_size_label(self) -> None:
        """Deve criar a partir de label."""
        assert StoryPoint.from_size_label("P").value == 3
        assert StoryPoint.from_size_label("M").value == 5
        assert StoryPoint.from_size_label("G").value == 8
        assert StoryPoint.from_size_label("GG").value == 13

    def test_from_invalid_label(self) -> None:
        """Deve rejeitar label inválido."""
        with pytest.raises(ValueError, match="Label inválido"):
            StoryPoint.from_size_label("XL")

    def test_string_representation(self) -> None:
        """Deve ter representação string clara."""
        sp = StoryPoint(5)
        assert str(sp) == "5"
        assert repr(sp) == "StoryPoint(5)"
