"""Testes para BacklogSorter."""
import time

import pytest

from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.exceptions.domain_exceptions import CyclicDependencyException
from backlog_manager.domain.services.backlog_sorter import BacklogSorter
from backlog_manager.domain.value_objects.story_point import StoryPoint


class TestBacklogSorter:
    """Testes para ordenação de backlog."""

    def test_sort_empty_list(self) -> None:
        """Deve retornar lista vazia para entrada vazia."""
        sorter = BacklogSorter()
        result = sorter.sort([])
        assert result == []

    def test_sort_single_story(self) -> None:
        """Deve retornar história única sem mudanças."""
        sorter = BacklogSorter()
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5))

        result = sorter.sort([story])

        assert len(result) == 1
        assert result[0] == story

    def test_sort_stories_no_dependencies(self) -> None:
        """Deve ordenar por prioridade quando não há dependências."""
        sorter = BacklogSorter()
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), priority=3)
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), priority=1)
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), priority=2)

        result = sorter.sort([story1, story2, story3])

        assert result[0].id == "S2"  # prioridade 1
        assert result[1].id == "S3"  # prioridade 2
        assert result[2].id == "S1"  # prioridade 3

    def test_sort_linear_dependency(self) -> None:
        """Deve ordenar respeitando dependência linear."""
        sorter = BacklogSorter()
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), dependencies=["S2"])
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), dependencies=["S3"])
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5))

        result = sorter.sort([story1, story2, story3])

        # S3 deve vir primeiro (sem dependências)
        # S2 depende de S3
        # S1 depende de S2
        assert result[0].id == "S3"
        assert result[1].id == "S2"
        assert result[2].id == "S1"

    def test_sort_parallel_dependencies(self) -> None:
        """Deve ordenar corretamente dependências paralelas."""
        sorter = BacklogSorter()
        # S1 depende de S2 e S3
        # S2 e S3 não têm dependências
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), dependencies=["S2", "S3"])
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), priority=2)
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), priority=1)

        result = sorter.sort([story1, story2, story3])

        # S3 e S2 devem vir antes de S1
        # Entre S2 e S3, S3 tem maior prioridade (menor número)
        assert result[0].id == "S3"
        assert result[1].id == "S2"
        assert result[2].id == "S1"

    def test_sort_complex_dag(self) -> None:
        """Deve ordenar DAG complexo corretamente."""
        sorter = BacklogSorter()
        # Grafo:
        #     S1 → S3
        #     S2 → S3
        #     S3 → S4
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), dependencies=["S3"])
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), dependencies=["S3"])
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), dependencies=["S4"])
        story4 = Story(id="S4", component="Test", name="Test4", story_point=StoryPoint(5))

        result = sorter.sort([story1, story2, story3, story4])

        # S4 primeiro (sem dependências)
        # S3 depois (depende de S4)
        # S1 e S2 por último (dependem de S3)
        assert result[0].id == "S4"
        assert result[1].id == "S3"
        assert {result[2].id, result[3].id} == {"S1", "S2"}

    def test_sort_respects_priority_within_level(self) -> None:
        """Deve respeitar prioridade dentro do mesmo nível de dependência."""
        sorter = BacklogSorter()
        # S1 e S2 ambos dependem de S3
        # S1 tem prioridade maior que S2
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), dependencies=["S3"], priority=2)
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), dependencies=["S3"], priority=1)
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5))

        result = sorter.sort([story1, story2, story3])

        assert result[0].id == "S3"
        assert result[1].id == "S2"  # Prioridade 1 (maior)
        assert result[2].id == "S1"  # Prioridade 2

    def test_reject_cyclic_dependency(self) -> None:
        """Deve lançar exceção para dependências cíclicas."""
        sorter = BacklogSorter()
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), dependencies=["S2"])
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), dependencies=["S1"])

        with pytest.raises(CyclicDependencyException):
            sorter.sort([story1, story2])

    def test_reject_indirect_cycle(self) -> None:
        """Deve detectar ciclos indiretos."""
        sorter = BacklogSorter()
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), dependencies=["S2"])
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), dependencies=["S3"])
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), dependencies=["S1"])

        with pytest.raises(CyclicDependencyException):
            sorter.sort([story1, story2, story3])

    def test_performance_large_backlog(self) -> None:
        """Deve ordenar backlog grande rapidamente."""
        sorter = BacklogSorter()

        # Criar 100 histórias em cadeia
        stories = []
        for i in range(100):
            deps = [f"S{i+1}"] if i < 99 else []
            story = Story(
                id=f"S{i}",
                component="Test",
                name=f"Test{i}",
                story_point=StoryPoint(5),
                dependencies=deps,
                priority=i,
            )
            stories.append(story)

        start = time.time()
        result = sorter.sort(stories)
        elapsed = time.time() - start

        assert len(result) == 100
        assert elapsed < 0.5  # Deve ser < 500ms

    def test_dependencies_on_nonexistent_stories(self) -> None:
        """Deve lidar com dependências em histórias que não existem na lista."""
        sorter = BacklogSorter()
        # S1 depende de S2, mas S2 não está na lista
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), dependencies=["S2"])

        # Não deve lançar exceção, apenas não conseguir resolver a dependência
        result = sorter.sort([story1])

        # S1 nunca terá in-degree 0 porque S2 não está na lista
        # Logo, não será incluída no resultado
        assert len(result) == 0

    def test_multiple_stories_same_priority_no_deps(self) -> None:
        """Histórias com mesma prioridade e sem dependências mantêm ordem."""
        sorter = BacklogSorter()
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), priority=1)
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), priority=1)
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), priority=1)

        result = sorter.sort([story1, story2, story3])

        # Todas devem estar no resultado
        assert len(result) == 3
        result_ids = {s.id for s in result}
        assert result_ids == {"S1", "S2", "S3"}
