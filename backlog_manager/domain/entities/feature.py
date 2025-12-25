"""Entidade Feature."""
from dataclasses import dataclass


@dataclass
class Feature:
    """
    Entidade que representa uma feature que agrupa histórias em uma onda de entrega.

    Uma onda define a sequência de entrega. Quanto menor o valor, mais cedo a feature
    será entregue.

    Attributes:
        id: Identificador único (gerado automaticamente)
        name: Nome da feature (deve ser único)
        wave: Número inteiro que define a ordem de entrega (deve ser único e > 0)
    """

    id: str
    name: str
    wave: int

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
            raise ValueError("ID da feature não pode ser vazio")

        if not self.name or not self.name.strip():
            raise ValueError("Nome da feature não pode ser vazio")

        if self.wave <= 0:
            raise ValueError("Onda deve ser um número positivo (> 0)")

    def __eq__(self, other: object) -> bool:
        """Features são iguais se têm mesmo ID."""
        if not isinstance(other, Feature):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash baseado no ID."""
        return hash(self.id)
