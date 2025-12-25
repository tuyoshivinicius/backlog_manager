"""Testes para exceções de domínio."""
from backlog_manager.domain.exceptions.domain_exceptions import (
    CyclicDependencyException,
    DeveloperNotFoundException,
    DomainException,
    StoryNotFoundException,
)


class TestDomainExceptions:
    """Testes para hierarquia de exceções."""

    def test_cyclic_dependency_exception(self) -> None:
        """Deve criar exceção com caminho do ciclo."""
        cycle = ["A", "B", "C", "A"]
        exc = CyclicDependencyException(cycle)

        assert exc.cycle_path == cycle
        assert "A -> B -> C -> A" in str(exc)
        assert isinstance(exc, DomainException)

    def test_story_not_found_exception(self) -> None:
        """Deve criar exceção com ID da história."""
        exc = StoryNotFoundException("S1")

        assert exc.story_id == "S1"
        assert "S1" in str(exc)
        assert isinstance(exc, DomainException)

    def test_developer_not_found_exception(self) -> None:
        """Deve criar exceção com ID do desenvolvedor."""
        exc = DeveloperNotFoundException("DEV1")

        assert exc.developer_id == "DEV1"
        assert "DEV1" in str(exc)
        assert isinstance(exc, DomainException)
