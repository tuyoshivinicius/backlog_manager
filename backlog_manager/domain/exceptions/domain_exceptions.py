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
        cycle_str = " -> ".join(cycle_path)
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


class InvalidWaveDependencyException(DomainException):
    """Lançada quando uma história depende de outra em onda posterior."""

    def __init__(self, story_id: str, story_wave: int, dependency_id: str, dependency_wave: int):
        """
        Inicializa exceção com detalhes da violação.

        Args:
            story_id: ID da história que depende
            story_wave: Onda da história
            dependency_id: ID da dependência
            dependency_wave: Onda da dependência
        """
        self.story_id = story_id
        self.story_wave = story_wave
        self.dependency_id = dependency_id
        self.dependency_wave = dependency_wave

        message = (
            f"Dependência de onda posterior não permitida: "
            f"História '{story_id}' (onda {story_wave}) não pode depender de "
            f"'{dependency_id}' (onda {dependency_wave}). "
            f"Dependências devem estar em ondas iguais ou anteriores."
        )
        super().__init__(message)


class FeatureNotFoundException(DomainException):
    """Lançada quando feature não encontrada."""

    def __init__(self, feature_id: str):
        """
        Inicializa exceção.

        Args:
            feature_id: ID da feature não encontrada
        """
        self.feature_id = feature_id
        super().__init__(f"Feature não encontrada: {feature_id}")


class DuplicateWaveException(DomainException):
    """Lançada quando tentativa de criar feature com onda duplicada."""

    def __init__(self, wave: int, existing_feature_name: str = ""):
        """
        Inicializa exceção.

        Args:
            wave: Número da onda duplicada
            existing_feature_name: Nome da feature existente com essa onda
        """
        self.wave = wave
        self.existing_feature_name = existing_feature_name

        if existing_feature_name:
            message = f"Já existe uma feature '{existing_feature_name}' com onda {wave}"
        else:
            message = f"Já existe uma feature com onda {wave}"

        super().__init__(message)


class FeatureHasStoriesException(DomainException):
    """Lançada quando tentativa de deletar feature que possui histórias."""

    def __init__(self, feature_id: str, feature_name: str, story_count: int):
        """
        Inicializa exceção.

        Args:
            feature_id: ID da feature
            feature_name: Nome da feature
            story_count: Número de histórias associadas
        """
        self.feature_id = feature_id
        self.feature_name = feature_name
        self.story_count = story_count

        message = (
            f"Não é possível deletar a feature '{feature_name}' porque possui "
            f"{story_count} história(s) associada(s). "
            f"Reatribua ou delete as histórias antes de deletar a feature."
        )
        super().__init__(message)
