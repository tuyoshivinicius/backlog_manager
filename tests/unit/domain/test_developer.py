"""Testes unitários para entidade Developer."""
import pytest

from backlog_manager.domain.entities.developer import Developer


class TestDeveloper:
    """Testes para entidade Developer."""

    def test_create_valid_developer(self) -> None:
        """Deve criar desenvolvedor com dados válidos."""
        dev = Developer(id="GA", name="Gabriela")

        assert dev.id == "GA"
        assert dev.name == "Gabriela"

    def test_reject_empty_id(self) -> None:
        """Deve rejeitar ID vazio."""
        with pytest.raises(ValueError, match="ID do desenvolvedor não pode ser vazio"):
            Developer(id="", name="Test")

    def test_reject_empty_name(self) -> None:
        """Deve rejeitar nome vazio."""
        with pytest.raises(ValueError, match="Nome do desenvolvedor não pode ser vazio"):
            Developer(id="GA", name="")

    def test_developer_equality_by_id(self) -> None:
        """Desenvolvedores são iguais se têm mesmo ID."""
        dev1 = Developer(id="GA", name="Gabriela")
        dev2 = Developer(id="GA", name="Outro Nome")
        dev3 = Developer(id="LU", name="Lucas")

        assert dev1 == dev2  # Mesmo ID
        assert dev1 != dev3  # IDs diferentes

    def test_developer_hashable(self) -> None:
        """Desenvolvedores devem ser hashable."""
        dev1 = Developer(id="GA", name="Gabriela")
        dev2 = Developer(id="GA", name="Outro Nome")
        dev3 = Developer(id="LU", name="Lucas")

        devs_set = {dev1, dev2, dev3}
        assert len(devs_set) == 2  # dev1 e dev2 são iguais
