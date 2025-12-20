"""Value Object para Story Points."""
from typing import Final


class StoryPoint:
    """
    Value Object que representa a medida de esforço de uma história.

    Story Points seguem escala Fibonacci modificada:
    - 3: Tarefa Pequena (P)
    - 5: Tarefa Média (M)
    - 8: Tarefa Grande (G)
    - 13: Tarefa Muito Grande (GG)

    Raises:
        ValueError: Se o valor não estiver na escala permitida
    """

    VALID_VALUES: Final[tuple[int, ...]] = (3, 5, 8, 13)

    def __init__(self, value: int) -> None:
        """
        Inicializa StoryPoint com validação.

        Args:
            value: Valor numérico do story point

        Raises:
            ValueError: Se valor não for 3, 5, 8 ou 13
        """
        if value not in self.VALID_VALUES:
            raise ValueError(
                f"Story Point inválido: {value}. " f"Valores permitidos: {self.VALID_VALUES}"
            )
        self._value = value

    @property
    def value(self) -> int:
        """Retorna valor do story point."""
        return self._value

    def __eq__(self, other: object) -> bool:
        """Compara igualdade de StoryPoints."""
        if not isinstance(other, StoryPoint):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """Hash para uso em sets e dicts."""
        return hash(self._value)

    def __repr__(self) -> str:
        """Representação string para debug."""
        return f"StoryPoint({self._value})"

    def __str__(self) -> str:
        """Representação string legível."""
        return str(self._value)

    @classmethod
    def from_size_label(cls, label: str) -> "StoryPoint":
        """
        Cria StoryPoint a partir de label de tamanho.

        Args:
            label: 'P', 'M', 'G' ou 'GG'

        Returns:
            StoryPoint correspondente

        Raises:
            ValueError: Se label inválido
        """
        mapping = {"P": 3, "M": 5, "G": 8, "GG": 13}
        if label not in mapping:
            raise ValueError(f"Label inválido: {label}. Use P, M, G ou GG")
        return cls(mapping[label])
