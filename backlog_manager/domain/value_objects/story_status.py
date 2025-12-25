"""Enum para status de histórias."""
from enum import Enum


class StoryStatus(str, Enum):
    """
    Status possíveis de uma história no ciclo de vida.

    Fluxo normal: BACKLOG → EXECUÇÃO → TESTES → CONCLUÍDO
    Fluxo alternativo: Qualquer estado → IMPEDIDO
    """

    BACKLOG = "BACKLOG"
    EXECUCAO = "EXECUÇÃO"
    TESTES = "TESTES"
    CONCLUIDO = "CONCLUÍDO"
    IMPEDIDO = "IMPEDIDO"

    def __str__(self) -> str:
        """Retorna a string representando o status."""
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "StoryStatus":
        """
        Cria StoryStatus a partir de string (case-insensitive).

        Args:
            value: String representando o status

        Returns:
            StoryStatus correspondente

        Raises:
            ValueError: Se string não corresponder a nenhum status
        """
        value_upper = value.upper()
        for status in cls:
            if status.value.upper() == value_upper:
                return status
        raise ValueError(f"Status inválido: {value}. " f"Valores válidos: {[s.value for s in cls]}")
