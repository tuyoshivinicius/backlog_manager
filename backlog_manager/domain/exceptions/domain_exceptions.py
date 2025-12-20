"""Exceções de domínio."""


class DomainException(Exception):
    """Exceção base para erros de domínio."""

    pass


class InvalidStoryPointException(DomainException):
    """Lançada quando Story Point inválido."""

    pass


class CyclicDependencyException(DomainException):
    """Lançada quando detectada dependência cíclica."""

    def __init__(self, cycle_path: list[str]):
        """
        Inicializa exceção com caminho do ciclo.

        Args:
            cycle_path: Lista de IDs formando o ciclo
        """
        self.cycle_path = cycle_path
        cycle_str = " → ".join(cycle_path)
        super().__init__(f"Dependência cíclica detectada: {cycle_str}")


class StoryNotFoundException(DomainException):
    """Lançada quando história não encontrada."""

    def __init__(self, story_id: str):
        """
        Inicializa exceção.

        Args:
            story_id: ID da história não encontrada
        """
        self.story_id = story_id
        super().__init__(f"História não encontrada: {story_id}")


class DeveloperNotFoundException(DomainException):
    """Lançada quando desenvolvedor não encontrado."""

    def __init__(self, developer_id: str):
        """
        Inicializa exceção.

        Args:
            developer_id: ID do desenvolvedor não encontrado
        """
        self.developer_id = developer_id
        super().__init__(f"Desenvolvedor não encontrado: {developer_id}")
