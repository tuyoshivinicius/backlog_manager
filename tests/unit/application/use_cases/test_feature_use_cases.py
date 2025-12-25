"""Testes unitários para use cases de Feature."""
from unittest.mock import Mock

import pytest

from backlog_manager.application.use_cases.feature.create_feature import CreateFeatureUseCase
from backlog_manager.application.use_cases.feature.delete_feature import DeleteFeatureUseCase
from backlog_manager.application.use_cases.feature.get_feature import GetFeatureUseCase
from backlog_manager.application.use_cases.feature.list_features import ListFeaturesUseCase
from backlog_manager.application.use_cases.feature.update_feature import UpdateFeatureUseCase
from backlog_manager.domain.entities.feature import Feature
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.exceptions.domain_exceptions import (
    DuplicateWaveException,
    FeatureHasStoriesException,
    FeatureNotFoundException,
    InvalidWaveDependencyException,
)
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


class TestCreateFeatureUseCase:
    """Testes para CreateFeatureUseCase."""

    def test_create_feature_success(self) -> None:
        """Deve criar feature com sucesso."""
        # Arrange
        feature_repo = Mock()
        feature_repo.find_by_wave.return_value = None  # Wave não existe
        feature_repo.exists.return_value = False  # ID não existe (disponível)

        use_case = CreateFeatureUseCase(feature_repo)

        # Act
        result = use_case.execute(name="MVP Core", wave=1)

        # Assert
        assert result.name == "MVP Core"
        assert result.wave == 1
        assert result.id == "MVP"  # 3 primeiras letras
        feature_repo.save.assert_called_once()

    def test_create_feature_id_conflict_resolution(self) -> None:
        """Deve resolver conflitos de ID incrementando contador."""
        # Arrange
        feature_repo = Mock()
        feature_repo.find_by_wave.return_value = None
        feature_repo.exists.side_effect = [True, True, False]  # MVP existe, MVP2 existe, MVP3 não existe (livre)

        use_case = CreateFeatureUseCase(feature_repo)

        # Act
        result = use_case.execute(name="MVP Iteration", wave=1)

        # Assert
        assert result.id == "MVP3"  # Deve ter incrementado até 3

    def test_create_feature_reject_short_name(self) -> None:
        """Deve rejeitar nome com menos de 3 caracteres."""
        # Arrange
        feature_repo = Mock()
        use_case = CreateFeatureUseCase(feature_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="Nome da feature deve ter pelo menos 3 caracteres"):
            use_case.execute(name="AB", wave=1)

    def test_create_feature_reject_empty_name(self) -> None:
        """Deve rejeitar nome vazio."""
        # Arrange
        feature_repo = Mock()
        use_case = CreateFeatureUseCase(feature_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="Nome da feature deve ter pelo menos 3 caracteres"):
            use_case.execute(name="", wave=1)

    def test_create_feature_reject_zero_wave(self) -> None:
        """Deve rejeitar onda igual a zero."""
        # Arrange
        feature_repo = Mock()
        use_case = CreateFeatureUseCase(feature_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="Onda deve ser um número positivo"):
            use_case.execute(name="MVP Core", wave=0)

    def test_create_feature_reject_negative_wave(self) -> None:
        """Deve rejeitar onda negativa."""
        # Arrange
        feature_repo = Mock()
        use_case = CreateFeatureUseCase(feature_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="Onda deve ser um número positivo"):
            use_case.execute(name="MVP Core", wave=-1)

    def test_create_feature_reject_duplicate_wave(self) -> None:
        """Deve rejeitar onda duplicada."""
        # Arrange
        feature_repo = Mock()
        existing_feature = Feature(id="MVP", name="MVP Existente", wave=1)
        feature_repo.find_by_wave.return_value = existing_feature

        use_case = CreateFeatureUseCase(feature_repo)

        # Act & Assert
        with pytest.raises(DuplicateWaveException) as exc_info:
            use_case.execute(name="Nova Feature", wave=1)

        assert exc_info.value.wave == 1
        assert exc_info.value.existing_feature_name == "MVP Existente"


class TestUpdateFeatureUseCase:
    """Testes para UpdateFeatureUseCase."""

    def test_update_feature_name_only(self) -> None:
        """Deve atualizar apenas o nome sem validar dependências."""
        # Arrange
        feature_repo = Mock()
        story_repo = Mock()
        wave_validator = Mock()

        feature = Feature(id="MVP", name="MVP Antigo", wave=1)
        feature_repo.find_by_id.return_value = feature

        use_case = UpdateFeatureUseCase(feature_repo, story_repo, wave_validator)

        # Act
        result = use_case.execute(feature_id="MVP", name="MVP Novo", wave=1)

        # Assert
        assert result.name == "MVP Novo"
        assert result.wave == 1
        wave_validator.validate_wave_change.assert_not_called()  # Não mudou wave

    def test_update_feature_wave_without_stories(self) -> None:
        """Deve atualizar wave quando feature não tem histórias."""
        # Arrange
        feature_repo = Mock()
        story_repo = Mock()
        wave_validator = Mock()

        feature = Feature(id="MVP", name="MVP Core", wave=1)
        feature_repo.find_by_id.return_value = feature
        feature_repo.find_by_wave.return_value = None  # Nova wave disponível
        story_repo.find_by_feature_id.return_value = []  # Sem histórias

        use_case = UpdateFeatureUseCase(feature_repo, story_repo, wave_validator)

        # Act
        result = use_case.execute(feature_id="MVP", name="MVP Core", wave=2)

        # Assert
        assert result.wave == 2
        wave_validator.validate_wave_change.assert_not_called()  # Sem histórias, não precisa validar

    def test_update_feature_wave_with_stories(self) -> None:
        """Deve validar dependências ao mudar wave com histórias."""
        # Arrange
        feature_repo = Mock()
        story_repo = Mock()
        wave_validator = Mock()

        feature = Feature(id="MVP", name="MVP Core", wave=1)
        feature_repo.find_by_id.return_value = feature
        feature_repo.find_by_wave.return_value = None

        # Histórias da feature
        story1 = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="MVP",
            status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        story1.feature = feature

        story_repo.find_by_feature_id.return_value = [story1]
        story_repo.find_by_id.return_value = None  # Sem dependências
        story_repo.find_all.return_value = [story1]  # Sem dependentes

        use_case = UpdateFeatureUseCase(feature_repo, story_repo, wave_validator)

        # Act
        result = use_case.execute(feature_id="MVP", name="MVP Core", wave=2)

        # Assert
        assert result.wave == 2
        wave_validator.validate_wave_change.assert_called_once()

    def test_update_feature_reject_duplicate_wave(self) -> None:
        """Deve rejeitar mudança para wave já existente."""
        # Arrange
        feature_repo = Mock()
        story_repo = Mock()
        wave_validator = Mock()

        feature = Feature(id="MVP", name="MVP Core", wave=1)
        other_feature = Feature(id="V2", name="Versão 2", wave=2)

        feature_repo.find_by_id.return_value = feature
        feature_repo.find_by_wave.return_value = other_feature  # Wave 2 já existe

        use_case = UpdateFeatureUseCase(feature_repo, story_repo, wave_validator)

        # Act & Assert
        with pytest.raises(DuplicateWaveException) as exc_info:
            use_case.execute(feature_id="MVP", name="MVP Core", wave=2)

        assert exc_info.value.wave == 2
        assert exc_info.value.existing_feature_name == "Versão 2"

    def test_update_feature_reject_wave_change_violating_dependencies(self) -> None:
        """Deve rejeitar mudança de wave que viola dependências."""
        # Arrange
        feature_repo = Mock()
        story_repo = Mock()
        wave_validator = Mock()

        feature = Feature(id="MVP", name="MVP Core", wave=2)
        feature_repo.find_by_id.return_value = feature
        feature_repo.find_by_wave.return_value = None

        # História da feature com dependência em wave 1
        story = Story(
            id="S1", component="Core", name="Story 1", story_point=StoryPoint(5), feature_id="MVP",
            status=StoryStatus.BACKLOG, priority=0, dependencies=["S0"]
        )
        story.feature = feature

        dep_feature = Feature(id="DEP", name="Dep Feature", wave=1)
        dependency = Story(
            id="S0", component="Dep", name="Dependency", story_point=StoryPoint(3), feature_id="DEP",
            status=StoryStatus.BACKLOG, priority=0, dependencies=[]
        )
        dependency.feature = dep_feature

        story_repo.find_by_feature_id.return_value = [story]
        story_repo.find_by_id.return_value = dependency
        story_repo.find_all.return_value = [story, dependency]

        # Validador rejeita mudança para wave 1 (dependência em wave 1 não permite)
        wave_validator.validate_wave_change.side_effect = InvalidWaveDependencyException(
            "S1", 1, "S0", 1
        )

        use_case = UpdateFeatureUseCase(feature_repo, story_repo, wave_validator)

        # Act & Assert
        with pytest.raises(InvalidWaveDependencyException):
            use_case.execute(feature_id="MVP", name="MVP Core", wave=1)

    def test_update_feature_not_found(self) -> None:
        """Deve lançar exceção se feature não existe."""
        # Arrange
        feature_repo = Mock()
        story_repo = Mock()
        wave_validator = Mock()

        feature_repo.find_by_id.return_value = None

        use_case = UpdateFeatureUseCase(feature_repo, story_repo, wave_validator)

        # Act & Assert
        with pytest.raises(FeatureNotFoundException) as exc_info:
            use_case.execute(feature_id="INEXISTENTE", name="Nome", wave=1)

        assert exc_info.value.feature_id == "INEXISTENTE"


class TestDeleteFeatureUseCase:
    """Testes para DeleteFeatureUseCase."""

    def test_delete_feature_success(self) -> None:
        """Deve deletar feature sem histórias."""
        # Arrange
        feature_repo = Mock()
        feature = Feature(id="MVP", name="MVP Core", wave=1)
        feature_repo.find_by_id.return_value = feature
        feature_repo.count_stories_by_feature.return_value = 0

        use_case = DeleteFeatureUseCase(feature_repo)

        # Act
        use_case.execute(feature_id="MVP")

        # Assert
        feature_repo.delete.assert_called_once_with("MVP")

    def test_delete_feature_not_found(self) -> None:
        """Deve lançar exceção se feature não existe."""
        # Arrange
        feature_repo = Mock()
        feature_repo.find_by_id.return_value = None

        use_case = DeleteFeatureUseCase(feature_repo)

        # Act & Assert
        with pytest.raises(FeatureNotFoundException) as exc_info:
            use_case.execute(feature_id="INEXISTENTE")

        assert exc_info.value.feature_id == "INEXISTENTE"

    def test_delete_feature_with_stories(self) -> None:
        """Deve rejeitar deleção de feature com histórias."""
        # Arrange
        feature_repo = Mock()
        feature = Feature(id="MVP", name="MVP Core", wave=1)
        feature_repo.find_by_id.return_value = feature
        feature_repo.count_stories_by_feature.return_value = 5  # 5 histórias

        use_case = DeleteFeatureUseCase(feature_repo)

        # Act & Assert
        with pytest.raises(FeatureHasStoriesException) as exc_info:
            use_case.execute(feature_id="MVP")

        assert exc_info.value.feature_id == "MVP"
        assert exc_info.value.feature_name == "MVP Core"
        assert exc_info.value.story_count == 5


class TestGetFeatureUseCase:
    """Testes para GetFeatureUseCase."""

    def test_get_feature_success(self) -> None:
        """Deve retornar feature existente."""
        # Arrange
        feature_repo = Mock()
        feature = Feature(id="MVP", name="MVP Core", wave=1)
        feature_repo.find_by_id.return_value = feature

        use_case = GetFeatureUseCase(feature_repo)

        # Act
        result = use_case.execute(feature_id="MVP")

        # Assert
        assert result.id == "MVP"
        assert result.name == "MVP Core"
        assert result.wave == 1

    def test_get_feature_not_found(self) -> None:
        """Deve lançar exceção se feature não existe."""
        # Arrange
        feature_repo = Mock()
        feature_repo.find_by_id.return_value = None

        use_case = GetFeatureUseCase(feature_repo)

        # Act & Assert
        with pytest.raises(FeatureNotFoundException) as exc_info:
            use_case.execute(feature_id="INEXISTENTE")

        assert exc_info.value.feature_id == "INEXISTENTE"


class TestListFeaturesUseCase:
    """Testes para ListFeaturesUseCase."""

    def test_list_features_empty(self) -> None:
        """Deve retornar lista vazia quando não há features."""
        # Arrange
        feature_repo = Mock()
        feature_repo.find_all.return_value = []

        use_case = ListFeaturesUseCase(feature_repo)

        # Act
        result = use_case.execute()

        # Assert
        assert result == []

    def test_list_features_ordered_by_wave(self) -> None:
        """Deve retornar features ordenadas por wave."""
        # Arrange
        feature_repo = Mock()
        feature1 = Feature(id="V3", name="Versão 3", wave=3)
        feature2 = Feature(id="MVP", name="MVP", wave=1)
        feature3 = Feature(id="V2", name="Versão 2", wave=2)

        feature_repo.find_all.return_value = [feature1, feature2, feature3]

        use_case = ListFeaturesUseCase(feature_repo)

        # Act
        result = use_case.execute()

        # Assert
        assert len(result) == 3
        assert result[0].wave == 1  # MVP
        assert result[1].wave == 2  # V2
        assert result[2].wave == 3  # V3

    def test_list_features_with_gaps(self) -> None:
        """Deve lidar com gaps em waves."""
        # Arrange
        feature_repo = Mock()
        feature1 = Feature(id="LATE", name="Late Wave", wave=100)
        feature2 = Feature(id="MVP", name="MVP", wave=1)
        feature3 = Feature(id="MID", name="Mid Wave", wave=10)

        feature_repo.find_all.return_value = [feature1, feature2, feature3]

        use_case = ListFeaturesUseCase(feature_repo)

        # Act
        result = use_case.execute()

        # Assert
        assert len(result) == 3
        assert result[0].wave == 1
        assert result[1].wave == 10
        assert result[2].wave == 100
