"""Entidade Story (História)."""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


@dataclass
class Story:
    """
    Entidade que representa uma história (user story) no backlog.

    Uma história é uma unidade de trabalho a ser desenvolvida,
    com esforço medido em Story Points e com possíveis dependências.

    Attributes:
        id: Identificador único (gerado automaticamente)
        feature: Agrupamento funcional da história
        name: Nome descritivo da história
        story_point: Esforço de implementação (3, 5, 8 ou 13)
        status: Estado atual no ciclo de vida
        priority: Ordem de prioridade (menor = mais prioritário)
        developer_id: ID do desenvolvedor alocado (opcional)
        dependencies: Lista de IDs de histórias das quais depende
        start_date: Data de início planejada
        end_date: Data de término planejada
        duration: Duração em dias úteis
    """

    id: str
    feature: str
    name: str
    story_point: StoryPoint
    status: StoryStatus = StoryStatus.BACKLOG
    priority: int = 0
    developer_id: Optional[str] = None
    dependencies: list[str] = field(default_factory=list)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration: Optional[int] = None

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
            raise ValueError("ID da história não pode ser vazio")

        if not self.feature or not self.feature.strip():
            raise ValueError("Feature não pode ser vazia")

        if not self.name or not self.name.strip():
            raise ValueError("Nome da história não pode ser vazio")

        if self.priority < 0:
            raise ValueError("Prioridade não pode ser negativa")

        if self.duration is not None and self.duration < 0:
            raise ValueError("Duração não pode ser negativa")

        if self.id in self.dependencies:
            raise ValueError("História não pode depender de si mesma")

    def add_dependency(self, story_id: str) -> None:
        """
        Adiciona dependência a outra história.

        Args:
            story_id: ID da história da qual depende

        Raises:
            ValueError: Se tentar adicionar dependência circular
        """
        if story_id == self.id:
            raise ValueError("História não pode depender de si mesma")

        if story_id not in self.dependencies:
            self.dependencies.append(story_id)

    def remove_dependency(self, story_id: str) -> None:
        """
        Remove dependência de outra história.

        Args:
            story_id: ID da história para remover dependência
        """
        if story_id in self.dependencies:
            self.dependencies.remove(story_id)

    def has_dependency(self, story_id: str) -> bool:
        """
        Verifica se depende de determinada história.

        Args:
            story_id: ID da história para verificar

        Returns:
            True se depende, False caso contrário
        """
        return story_id in self.dependencies

    def allocate_developer(self, developer_id: str) -> None:
        """
        Aloca desenvolvedor à história.

        Args:
            developer_id: ID do desenvolvedor
        """
        if not developer_id or not developer_id.strip():
            raise ValueError("ID do desenvolvedor não pode ser vazio")
        self.developer_id = developer_id

    def deallocate_developer(self) -> None:
        """Remove desenvolvedor alocado."""
        self.developer_id = None

    def is_allocated(self) -> bool:
        """Verifica se tem desenvolvedor alocado."""
        return self.developer_id is not None

    def __eq__(self, other: object) -> bool:
        """Entidades são iguais se têm mesmo ID."""
        if not isinstance(other, Story):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash baseado no ID."""
        return hash(self.id)
