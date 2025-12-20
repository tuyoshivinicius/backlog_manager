"""Entidade Developer (Desenvolvedor)."""
from dataclasses import dataclass


@dataclass
class Developer:
    """
    Entidade que representa um desenvolvedor que pode ser alocado a histórias.

    Attributes:
        id: Identificador único (gerado automaticamente)
        name: Nome do desenvolvedor
    """

    id: str
    name: str

    def __post_init__(self) -> None:
        """Valida dados após inicialização."""
        self._validate()

    def _validate(self) -> None:
        """
        Valida invariantes da entidade.

        Raises:
            ValueError: Se dados inválidos
        """
        if not self.id or not self.id.strip():
            raise ValueError("ID do desenvolvedor não pode ser vazio")

        if not self.name or not self.name.strip():
            raise ValueError("Nome do desenvolvedor não pode ser vazio")

    def __eq__(self, other: object) -> bool:
        """Desenvolvedores são iguais se têm mesmo ID."""
        if not isinstance(other, Developer):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash baseado no ID."""
        return hash(self.id)
