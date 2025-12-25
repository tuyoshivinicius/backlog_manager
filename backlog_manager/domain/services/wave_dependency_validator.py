"""Serviço para validação de dependências entre ondas."""
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.exceptions.domain_exceptions import InvalidWaveDependencyException


class WaveDependencyValidator:
    """
    Serviço de domínio para validar regras de dependência entre ondas.

    Regra: Uma história só pode depender de histórias em ondas IGUAIS ou ANTERIORES.

    Formalmente:
    - Se História H (onda W_h) depende de História D (onda W_d):
      - VÁLIDO: W_d <= W_h (dependência de onda anterior ou igual)
      - INVÁLIDO: W_d > W_h (dependência de onda futura)

    Justificativa:
    Histórias de ondas anteriores são entregues primeiro. Uma história não pode
    depender de algo que será entregue depois.
    """

    def validate(self, story: Story, dependency: Story) -> None:
        """
        Valida se uma história pode depender de outra baseado nas ondas.

        Args:
            story: História que vai ter a dependência
            dependency: História que será a dependência

        Raises:
            InvalidWaveDependencyException: Se dependência de onda posterior
            AttributeError: Se features não foram carregadas

        Example:
            >>> validator = WaveDependencyValidator()
            >>> story_wave2 = Story(..., feature=Feature(wave=2))
            >>> dep_wave1 = Story(..., feature=Feature(wave=1))
            >>> validator.validate(story_wave2, dep_wave1)  # OK
            >>> validator.validate(dep_wave1, story_wave2)  # Raises exception
        """
        # Obter ondas das histórias
        story_wave = story.wave
        dependency_wave = dependency.wave

        # Validar regra: dependência deve estar em onda igual ou anterior
        if dependency_wave > story_wave:
            raise InvalidWaveDependencyException(
                story_id=story.id,
                story_wave=story_wave,
                dependency_id=dependency.id,
                dependency_wave=dependency_wave,
            )

    def validate_wave_change(
        self, story: Story, new_wave: int, dependencies: list[Story], dependents: list[Story]
    ) -> None:
        """
        Valida se uma história pode mudar para uma nova onda.

        Verifica tanto as dependências da história quanto as histórias que dependem dela.

        Args:
            story: História que vai mudar de onda
            new_wave: Nova onda da história
            dependencies: Lista de histórias das quais a história depende
            dependents: Lista de histórias que dependem desta história

        Raises:
            InvalidWaveDependencyException: Se mudança violar regras

        Example:
            >>> validator = WaveDependencyValidator()
            >>> story = Story(..., feature=Feature(wave=2))
            >>> dep = Story(..., feature=Feature(wave=1))  # História depende de dep
            >>> dependent = Story(..., feature=Feature(wave=3))  # dependent depende de história
            >>> validator.validate_wave_change(story, 3, [dep], [dependent])  # OK
            >>> validator.validate_wave_change(story, 4, [dep], [dependent])  # Raises (dependent em wave 3)
        """
        # Validar dependências: todas devem estar em ondas <= new_wave
        for dependency in dependencies:
            dependency_wave = dependency.wave
            if dependency_wave > new_wave:
                raise InvalidWaveDependencyException(
                    story_id=story.id,
                    story_wave=new_wave,
                    dependency_id=dependency.id,
                    dependency_wave=dependency_wave,
                )

        # Validar dependentes: todos devem estar em ondas >= new_wave
        for dependent in dependents:
            dependent_wave = dependent.wave
            if new_wave > dependent_wave:
                raise InvalidWaveDependencyException(
                    story_id=dependent.id,
                    story_wave=dependent_wave,
                    dependency_id=story.id,
                    dependency_wave=new_wave,
                )
