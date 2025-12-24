"""Testes unitários para entidade Story."""
import pytest

from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


class TestStory:
    """Testes para entidade Story."""

    def test_create_valid_story(self) -> None:
        """Deve criar história com dados válidos."""
        story = Story(
            id="S1", component="Autenticação", name="Implementar login", story_point=StoryPoint(5), priority=1
        )

        assert story.id == "S1"
        assert story.component == "Autenticação"
        assert story.name == "Implementar login"
        assert story.story_point.value == 5
        assert story.status == StoryStatus.BACKLOG
        assert story.priority == 1
        assert story.developer_id is None
        assert story.dependencies == []

    def test_reject_empty_id(self) -> None:
        """Deve rejeitar ID vazio."""
        with pytest.raises(ValueError, match="ID da história não pode ser vazio"):
            Story(id="", component="Test", name="Test", story_point=StoryPoint(5))

    def test_reject_empty_component(self) -> None:
        """Deve rejeitar component vazia."""
        with pytest.raises(ValueError, match="Component não pode ser vazia"):
            Story(id="S1", component="", name="Test", story_point=StoryPoint(5))

    def test_reject_empty_name(self) -> None:
        """Deve rejeitar nome vazio."""
        with pytest.raises(ValueError, match="Nome da história não pode ser vazio"):
            Story(id="S1", component="Test", name="", story_point=StoryPoint(5))

    def test_reject_negative_priority(self) -> None:
        """Deve rejeitar prioridade negativa."""
        with pytest.raises(ValueError, match="Prioridade não pode ser negativa"):
            Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5), priority=-1)

    def test_reject_negative_duration(self) -> None:
        """Deve rejeitar duração negativa."""
        with pytest.raises(ValueError, match="Duração não pode ser negativa"):
            Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5), duration=-1)

    def test_add_dependency(self) -> None:
        """Deve adicionar dependência."""
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

        story.add_dependency("S2")
        assert story.has_dependency("S2")
        assert "S2" in story.dependencies

    def test_reject_self_dependency(self) -> None:
        """Não deve permitir dependência de si mesma."""
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

        with pytest.raises(ValueError, match="não pode depender de si mesma"):
            story.add_dependency("S1")

    def test_reject_self_dependency_in_init(self) -> None:
        """Não deve permitir dependência de si mesma na criação."""
        with pytest.raises(ValueError, match="não pode depender de si mesma"):
            Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5), dependencies=["S1"])

    def test_remove_dependency(self) -> None:
        """Deve remover dependência."""
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

        story.add_dependency("S2")
        story.remove_dependency("S2")
        assert not story.has_dependency("S2")

    def test_remove_nonexistent_dependency(self) -> None:
        """Deve ignorar remoção de dependência inexistente."""
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

        story.remove_dependency("S2")  # Não deve lançar erro
        assert not story.has_dependency("S2")

    def test_allocate_developer(self) -> None:
        """Deve alocar desenvolvedor."""
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

        assert not story.is_allocated()
        story.allocate_developer("DEV1")
        assert story.is_allocated()
        assert story.developer_id == "DEV1"

    def test_reject_empty_developer_id(self) -> None:
        """Deve rejeitar ID de desenvolvedor vazio."""
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

        with pytest.raises(ValueError, match="ID do desenvolvedor não pode ser vazio"):
            story.allocate_developer("")

    def test_deallocate_developer(self) -> None:
        """Deve desalocar desenvolvedor."""
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5), developer_id="DEV1")

        story.deallocate_developer()
        assert not story.is_allocated()

    def test_story_equality_by_id(self) -> None:
        """Histórias são iguais se têm mesmo ID."""
        story1 = Story(id="S1", component="Component1", name="Name1", story_point=StoryPoint(5))
        story2 = Story(id="S1", component="Component2", name="Name2", story_point=StoryPoint(8))
        story3 = Story(id="S2", component="Component1", name="Name1", story_point=StoryPoint(5))

        assert story1 == story2  # Mesmo ID
        assert story1 != story3  # IDs diferentes

    def test_story_hashable(self) -> None:
        """Histórias devem ser hashable."""
        story1 = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))
        story2 = Story(id="S1", component="Test2", name="Test2", story_point=StoryPoint(8))
        story3 = Story(id="S2", component="Test", name="Test", story_point=StoryPoint(5))

        stories_set = {story1, story2, story3}
        assert len(stories_set) == 2  # story1 e story2 são iguais

    def test_add_duplicate_dependency(self) -> None:
        """Não deve adicionar dependência duplicada."""
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

        story.add_dependency("S2")
        story.add_dependency("S2")  # Tentar adicionar novamente

        assert story.dependencies.count("S2") == 1
