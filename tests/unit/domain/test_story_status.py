"""Testes para StoryStatus enum."""
import pytest

from backlog_manager.domain.value_objects.story_status import StoryStatus


class TestStoryStatus:
    """Testes para enum StoryStatus."""

    def test_all_statuses_exist(self) -> None:
        """Deve ter todos os status esperados."""
        expected = ["BACKLOG", "EXECUÇÃO", "TESTES", "CONCLUÍDO", "IMPEDIDO"]
        actual = [s.value for s in StoryStatus]
        assert actual == expected

    def test_from_string_case_insensitive(self) -> None:
        """Deve aceitar string case-insensitive."""
        assert StoryStatus.from_string("backlog") == StoryStatus.BACKLOG
        assert StoryStatus.from_string("BACKLOG") == StoryStatus.BACKLOG
        assert StoryStatus.from_string("Backlog") == StoryStatus.BACKLOG

    def test_from_string_invalid(self) -> None:
        """Deve rejeitar string inválida."""
        with pytest.raises(ValueError, match="Status inválido"):
            StoryStatus.from_string("INVALID")

    def test_status_as_string(self) -> None:
        """Enum deve funcionar como string."""
        status = StoryStatus.BACKLOG
        assert status == "BACKLOG"
        assert str(status) == "BACKLOG"
