"""Enum para critério de alocação de desenvolvedores."""
from enum import Enum


class AllocationCriteria(str, Enum):
    """
    Critério de alocação de desenvolvedores.

    Define a estratégia utilizada pelo algoritmo de alocação
    para decidir qual desenvolvedor recebe cada história.

    Valores:
        LOAD_BALANCING: Prioriza distribuição uniforme de carga entre desenvolvedores.
            Escolhe sempre o desenvolvedor com menos histórias alocadas.

        DEPENDENCY_OWNER: Prioriza continuidade de contexto.
            Tenta alocar a história ao desenvolvedor que implementou suas dependências.
            Se não houver ou não estiver disponível, faz fallback para balanceamento de carga.
    """

    LOAD_BALANCING = "LOAD_BALANCING"
    DEPENDENCY_OWNER = "DEPENDENCY_OWNER"

    def __str__(self) -> str:
        """Retorna a string representando o critério."""
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "AllocationCriteria":
        """
        Cria AllocationCriteria a partir de string (case-insensitive).

        Args:
            value: String representando o critério

        Returns:
            AllocationCriteria correspondente

        Raises:
            ValueError: Se string não corresponder a nenhum critério
        """
        value_upper = value.upper().replace(" ", "_")
        for criteria in cls:
            if criteria.value.upper() == value_upper:
                return criteria
        raise ValueError(
            f"Critério de alocação inválido: {value}. "
            f"Valores válidos: {[c.value for c in cls]}"
        )

    @classmethod
    def get_display_name(cls, value: "AllocationCriteria") -> str:
        """
        Retorna nome para exibição na UI (Português).

        Args:
            value: Critério de alocação

        Returns:
            Nome em português para exibição
        """
        names = {
            cls.LOAD_BALANCING: "Balanceamento de Carga",
            cls.DEPENDENCY_OWNER: "Proprietário de Dependência",
        }
        return names.get(value, value.value)

    @classmethod
    def get_description(cls, value: "AllocationCriteria") -> str:
        """
        Retorna descrição do critério para tooltip.

        Args:
            value: Critério de alocação

        Returns:
            Descrição em português
        """
        descriptions = {
            cls.LOAD_BALANCING: (
                "Distribui histórias uniformemente entre desenvolvedores, "
                "priorizando quem tem menos carga."
            ),
            cls.DEPENDENCY_OWNER: (
                "Prioriza o desenvolvedor que implementou as dependências da história, "
                "promovendo continuidade de contexto. Se não disponível, usa balanceamento de carga."
            ),
        }
        return descriptions.get(value, "")
