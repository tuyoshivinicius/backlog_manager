"""Testes unitários para WaveDependencyValidator."""
import pytest

from backlog_manager.domain.entities.feature import Feature
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.exceptions.domain_exceptions import InvalidWaveDependencyException
from backlog_manager.domain.services.wave_dependency_validator import WaveDependencyValidator
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


class TestWaveDependencyValidator:
    """Testes para WaveDependencyValidator."""

    def test_validate_dependency_same_wave(self) -> None:
        """Deve permitir dependência em mesma onda."""
        # Arrange
        feature = Feature(id="F1", name="Feature 1", wave=1)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F1",
            status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story.feature = feature

        dependency = Story(
            id="S2", component="Core", name="Story 2", story_point=StoryPoint(3), feature_id="F1",
            status=StoryStatus.BACKLOG, priority=1, dependencies=[]
        )
        dependency.feature = feature

        validator = WaveDependencyValidator()

        # Act & Assert (não deve lançar exceção)
        validator.validate(story, dependency)

    def test_validate_dependency_earlier_wave(self) -> None:
        """Deve permitir dependência em onda anterior."""
        # Arrange
        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F2",
            status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story.feature = feature_wave2

        dependency = Story(
            id="S2", component="Core", name="Story 2", story_point=StoryPoint(3), feature_id="F1",
            status=StoryStatus.BACKLOG, priority=1, dependencies=[]
        )
        dependency.feature = feature_wave1

        validator = WaveDependencyValidator()

        # Act & Assert (não deve lançar exceção)
        validator.validate(story, dependency)

    def test_validate_reject_dependency_later_wave(self) -> None:
        """Deve rejeitar dependência em onda posterior."""
        # Arrange
        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F1",
            status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story.feature = feature_wave1

        dependency = Story(
            id="S2", component="Core", name="Story 2", story_point=StoryPoint(3), feature_id="F2",
            status=StoryStatus.BACKLOG, priority=1, dependencies=[]
        )
        dependency.feature = feature_wave2

        validator = WaveDependencyValidator()

        # Act & Assert
        with pytest.raises(InvalidWaveDependencyException) as exc_info:
            validator.validate(story, dependency)

        assert exc_info.value.story_id == "S1"
        assert exc_info.value.story_wave == 1
        assert exc_info.value.dependency_id == "S2"
        assert exc_info.value.dependency_wave == 2

    def test_validate_reject_large_wave_gap(self) -> None:
        """Deve rejeitar dependência com grande gap de onda."""
        # Arrange
        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave10 = Feature(id="F10", name="Feature Wave 10", wave=10)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F1",
            status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story.feature = feature_wave1

        dependency = Story(
            id="S2", component="Core", name="Story 2", story_point=StoryPoint(3), feature_id="F10",
            status=StoryStatus.BACKLOG, priority=1, dependencies=[]
        )
        dependency.feature = feature_wave10

        validator = WaveDependencyValidator()

        # Act & Assert
        with pytest.raises(InvalidWaveDependencyException) as exc_info:
            validator.validate(story, dependency)

        assert exc_info.value.story_wave == 1
        assert exc_info.value.dependency_wave == 10


class TestWaveDependencyValidatorWaveChange:
    """Testes para validate_wave_change."""

    def test_validate_wave_change_no_dependencies(self) -> None:
        """Deve permitir mudança de wave sem dependências."""
        # Arrange
        feature = Feature(id="F1", name="Feature 1", wave=1)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F1",
            status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story.feature = feature

        validator = WaveDependencyValidator()

        # Act & Assert (não deve lançar exceção)
        validator.validate_wave_change(story, new_wave=2, dependencies=[], dependents=[])

    def test_validate_wave_change_with_valid_dependencies(self) -> None:
        """Deve permitir mudança para wave posterior às dependências."""
        # Arrange
        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F2",
            status=StoryStatus.BACKLOG, priority=0, dependencies=["S0"]
        )
        story.feature = feature_wave2

        dependency = Story(
            id="S0", component="Dep", name="Dependency", story_point=StoryPoint(3), feature_id="F1",
            status=StoryStatus.BACKLOG, priority=1, dependencies=[]
        )
        dependency.feature = feature_wave1

        validator = WaveDependencyValidator()

        # Act & Assert (mudança de wave 2 para 3 com dependência em wave 1)
        validator.validate_wave_change(story, new_wave=3, dependencies=[dependency], dependents=[])

    def test_validate_wave_change_reject_earlier_than_dependency(self) -> None:
        """Deve rejeitar mudança para wave anterior à dependência."""
        # Arrange
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)
        feature_wave3 = Feature(id="F3", name="Feature Wave 3", wave=3)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F3",
            status=StoryStatus.BACKLOG, priority=0, dependencies=["S0"]
        )
        story.feature = feature_wave3

        dependency = Story(
            id="S0", component="Dep", name="Dependency", story_point=StoryPoint(3), feature_id="F2",
            status=StoryStatus.BACKLOG, priority=1, dependencies=[]
        )
        dependency.feature = feature_wave2

        validator = WaveDependencyValidator()

        # Act & Assert (tentando mudar de wave 3 para 1, mas dependência está em wave 2)
        with pytest.raises(InvalidWaveDependencyException) as exc_info:
            validator.validate_wave_change(story, new_wave=1, dependencies=[dependency], dependents=[])

        assert exc_info.value.story_id == "S1"
        assert exc_info.value.story_wave == 1  # Nova wave
        assert exc_info.value.dependency_id == "S0"
        assert exc_info.value.dependency_wave == 2

    def test_validate_wave_change_with_valid_dependents(self) -> None:
        """Deve permitir mudança para wave anterior aos dependentes."""
        # Arrange
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)
        feature_wave3 = Feature(id="F3", name="Feature Wave 3", wave=3)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F2",
            status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story.feature = feature_wave2

        dependent = Story(
            id="S2", component="Dep", name="Dependent", story_point=StoryPoint(3), feature_id="F3",
            status=StoryStatus.BACKLOG, priority=1, dependencies=["S1"]
        )
        dependent.feature = feature_wave3

        validator = WaveDependencyValidator()

        # Act & Assert (mudança de wave 2 para 1 com dependente em wave 3)
        validator.validate_wave_change(story, new_wave=1, dependencies=[], dependents=[dependent])

    def test_validate_wave_change_reject_later_than_dependent(self) -> None:
        """Deve rejeitar mudança para wave posterior ao dependente."""
        # Arrange
        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F1",
            status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story.feature = feature_wave1

        dependent = Story(
            id="S2", component="Dep", name="Dependent", story_point=StoryPoint(3), feature_id="F2",
            status=StoryStatus.BACKLOG, priority=1, dependencies=["S1"]
        )
        dependent.feature = feature_wave2

        validator = WaveDependencyValidator()

        # Act & Assert (tentando mudar de wave 1 para 3, mas dependente está em wave 2)
        with pytest.raises(InvalidWaveDependencyException) as exc_info:
            validator.validate_wave_change(story, new_wave=3, dependencies=[], dependents=[dependent])

        assert exc_info.value.story_id == "S2"  # História dependente
        assert exc_info.value.story_wave == 2  # Wave do dependente
        assert exc_info.value.dependency_id == "S1"  # História que está mudando
        assert exc_info.value.dependency_wave == 3  # Nova wave

    def test_validate_wave_change_complex_scenario(self) -> None:
        """Deve validar mudança com múltiplas dependências e dependentes."""
        # Arrange
        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)
        feature_wave3 = Feature(id="F3", name="Feature Wave 3", wave=3)
        feature_wave5 = Feature(id="F5", name="Feature Wave 5", wave=5)

        story = Story(
            id="S2", component="Core", name="Story Middle", story_point=StoryPoint(5), feature_id="F2",
            status=StoryStatus.BACKLOG, priority=0, dependencies=["S1"]
        )
        story.feature = feature_wave2

        dep1 = Story(
            id="S1", component="Dep", name="Dependency 1", story_point=StoryPoint(3), feature_id="F1",
            status=StoryStatus.BACKLOG, priority=1, dependencies=[]
        )
        dep1.feature = feature_wave1

        dependent1 = Story(
            id="S3", component="Dep", name="Dependent 1", story_point=StoryPoint(3), feature_id="F3",
            status=StoryStatus.BACKLOG, priority=2, dependencies=["S2"]
        )
        dependent1.feature = feature_wave3

        dependent2 = Story(
            id="S5", component="Dep", name="Dependent 2", story_point=StoryPoint(8), feature_id="F5",
            status=StoryStatus.BACKLOG, priority=3, dependencies=["S2"]
        )
        dependent2.feature = feature_wave5

        validator = WaveDependencyValidator()

        # Act & Assert
        # Deve permitir mudança de wave 2 para qualquer valor entre 1 (dep) e 3 (dependent1)
        validator.validate_wave_change(story, new_wave=2, dependencies=[dep1], dependents=[dependent1, dependent2])

        # Deve rejeitar mudança para wave 4 (maior que dependent1 em wave 3)
        with pytest.raises(InvalidWaveDependencyException):
            validator.validate_wave_change(story, new_wave=4, dependencies=[dep1], dependents=[dependent1, dependent2])

    def test_validate_wave_change_allow_same_wave_as_dependency(self) -> None:
        """Deve permitir mudança para mesma wave da dependência."""
        # Arrange
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)
        feature_wave3 = Feature(id="F3", name="Feature Wave 3", wave=3)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F3",
            status=StoryStatus.BACKLOG, priority=0, dependencies=["S0"]
        )
        story.feature = feature_wave3

        dependency = Story(
            id="S0", component="Dep", name="Dependency", story_point=StoryPoint(3), feature_id="F2",
            status=StoryStatus.BACKLOG, priority=1, dependencies=[]
        )
        dependency.feature = feature_wave2

        validator = WaveDependencyValidator()

        # Act & Assert (mudança para mesma wave da dependência deve ser permitida)
        validator.validate_wave_change(story, new_wave=2, dependencies=[dependency], dependents=[])

    def test_validate_wave_change_allow_same_wave_as_dependent(self) -> None:
        """Deve permitir mudança para mesma wave do dependente."""
        # Arrange
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)
        feature_wave3 = Feature(id="F3", name="Feature Wave 3", wave=3)

        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="F2",
            status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story.feature = feature_wave2

        dependent = Story(
            id="S2", component="Dep", name="Dependent", story_point=StoryPoint(3), feature_id="F3",
            status=StoryStatus.BACKLOG, priority=1, dependencies=["S1"]
        )
        dependent.feature = feature_wave3

        validator = WaveDependencyValidator()

        # Act & Assert (mudança para mesma wave do dependente deve ser permitida)
        validator.validate_wave_change(story, new_wave=3, dependencies=[], dependents=[dependent])
