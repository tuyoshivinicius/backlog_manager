"""Testes para BacklogSorter."""
import time

import pytest

from backlog_manager.domain.entities.feature import Feature
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.exceptions.domain_exceptions import CyclicDependencyException
from backlog_manager.domain.services.backlog_sorter import BacklogSorter
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


class TestBacklogSorter:
    """Testes para ordenação de backlog."""

    def _create_default_feature(self) -> Feature:
        """Cria feature padrão para testes."""
        return Feature(id="DEFAULT", name="Default Feature", wave=1)

    def _add_feature_to_story(self, story: Story, feature: Feature = None) -> Story:
        """Adiciona feature a uma história."""
        if feature is None:
            feature = self._create_default_feature()
        story.feature_id = feature.id
        story.feature = feature
        story.status = StoryStatus.BACKLOG
        return story

    def test_sort_empty_list(self) -> None:
        """Deve retornar lista vazia para entrada vazia."""
        sorter = BacklogSorter()
        result = sorter.sort([])
        assert result == []

    def test_sort_single_story(self) -> None:
        """Deve retornar história única sem mudanças."""
        sorter = BacklogSorter()
        story = Story(id="S1", component="Test", name="Test", story_point=StoryPoint(5), feature_id="DEFAULT")
        self._add_feature_to_story(story)

        result = sorter.sort([story])

        assert len(result) == 1
        assert result[0] == story

    def test_sort_stories_no_dependencies(self) -> None:
        """Deve ordenar por prioridade quando não há dependências."""
        sorter = BacklogSorter()
        feature = self._create_default_feature()
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), feature_id="DEFAULT", priority=3)
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), feature_id="DEFAULT", priority=1)
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), feature_id="DEFAULT", priority=2)
        self._add_feature_to_story(story1, feature)
        self._add_feature_to_story(story2, feature)
        self._add_feature_to_story(story3, feature)

        result = sorter.sort([story1, story2, story3])

        assert result[0].id == "S2"  # prioridade 1
        assert result[1].id == "S3"  # prioridade 2
        assert result[2].id == "S1"  # prioridade 3

    def test_sort_linear_dependency(self) -> None:
        """Deve ordenar respeitando dependência linear."""
        sorter = BacklogSorter()
        feature = self._create_default_feature()
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S2"])
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S3"])
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), feature_id="DEFAULT")
        self._add_feature_to_story(story1, feature)
        self._add_feature_to_story(story2, feature)
        self._add_feature_to_story(story3, feature)

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
        feature = self._create_default_feature()
        # S1 depende de S2 e S3
        # S2 e S3 não têm dependências
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S2", "S3"])
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), feature_id="DEFAULT", priority=2)
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), feature_id="DEFAULT", priority=1)
        self._add_feature_to_story(story1, feature)
        self._add_feature_to_story(story2, feature)
        self._add_feature_to_story(story3, feature)

        result = sorter.sort([story1, story2, story3])

        # S3 e S2 devem vir antes de S1
        # Entre S2 e S3, S3 tem maior prioridade (menor número)
        assert result[0].id == "S3"
        assert result[1].id == "S2"
        assert result[2].id == "S1"

    def test_sort_complex_dag(self) -> None:
        """Deve ordenar DAG complexo corretamente."""
        sorter = BacklogSorter()
        feature = self._create_default_feature()
        # Grafo:
        #     S1 → S3
        #     S2 → S3
        #     S3 → S4
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S3"])
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S3"])
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S4"])
        story4 = Story(id="S4", component="Test", name="Test4", story_point=StoryPoint(5), feature_id="DEFAULT")
        self._add_feature_to_story(story1, feature)
        self._add_feature_to_story(story2, feature)
        self._add_feature_to_story(story3, feature)
        self._add_feature_to_story(story4, feature)

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
        feature = self._create_default_feature()
        # S1 e S2 ambos dependem de S3
        # S1 tem prioridade maior que S2
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S3"], priority=2)
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S3"], priority=1)
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), feature_id="DEFAULT")
        self._add_feature_to_story(story1, feature)
        self._add_feature_to_story(story2, feature)
        self._add_feature_to_story(story3, feature)

        result = sorter.sort([story1, story2, story3])

        assert result[0].id == "S3"
        assert result[1].id == "S2"  # Prioridade 1 (maior)
        assert result[2].id == "S1"  # Prioridade 2

    def test_reject_cyclic_dependency(self) -> None:
        """Deve lançar exceção para dependências cíclicas."""
        sorter = BacklogSorter()
        feature = self._create_default_feature()
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S2"])
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S1"])
        self._add_feature_to_story(story1, feature)
        self._add_feature_to_story(story2, feature)

        with pytest.raises(CyclicDependencyException):
            sorter.sort([story1, story2])

    def test_reject_indirect_cycle(self) -> None:
        """Deve detectar ciclos indiretos."""
        sorter = BacklogSorter()
        feature = self._create_default_feature()
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S2"])
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S3"])
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S1"])
        self._add_feature_to_story(story1, feature)
        self._add_feature_to_story(story2, feature)
        self._add_feature_to_story(story3, feature)

        with pytest.raises(CyclicDependencyException):
            sorter.sort([story1, story2, story3])

    def test_performance_large_backlog(self) -> None:
        """Deve ordenar backlog grande rapidamente."""
        sorter = BacklogSorter()
        feature = self._create_default_feature()

        # Criar 100 histórias em cadeia
        stories = []
        for i in range(100):
            deps = [f"S{i+1}"] if i < 99 else []
            story = Story(
                id=f"S{i}",
                component="Test",
                name=f"Test{i}",
                story_point=StoryPoint(5),
                feature_id="DEFAULT",
                dependencies=deps,
                priority=i,
            )
            self._add_feature_to_story(story, feature)
            stories.append(story)

        start = time.time()
        result = sorter.sort(stories)
        elapsed = time.time() - start

        assert len(result) == 100
        assert elapsed < 0.5  # Deve ser < 500ms

    def test_dependencies_on_nonexistent_stories(self) -> None:
        """Deve lidar com dependências em histórias que não existem na lista."""
        sorter = BacklogSorter()
        feature = self._create_default_feature()
        # S1 depende de S2, mas S2 não está na lista
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), feature_id="DEFAULT", dependencies=["S2"])
        self._add_feature_to_story(story1, feature)

        # Não deve lançar exceção, apenas não conseguir resolver a dependência
        result = sorter.sort([story1])

        # S1 nunca terá in-degree 0 porque S2 não está na lista
        # Logo, não será incluída no resultado
        assert len(result) == 0

    def test_multiple_stories_same_priority_no_deps(self) -> None:
        """Histórias com mesma prioridade e sem dependências mantêm ordem."""
        sorter = BacklogSorter()
        feature = self._create_default_feature()
        story1 = Story(id="S1", component="Test", name="Test1", story_point=StoryPoint(5), feature_id="DEFAULT", priority=1)
        story2 = Story(id="S2", component="Test", name="Test2", story_point=StoryPoint(5), feature_id="DEFAULT", priority=1)
        story3 = Story(id="S3", component="Test", name="Test3", story_point=StoryPoint(5), feature_id="DEFAULT", priority=1)
        self._add_feature_to_story(story1, feature)
        self._add_feature_to_story(story2, feature)
        self._add_feature_to_story(story3, feature)

        result = sorter.sort([story1, story2, story3])

        # Todas devem estar no resultado
        assert len(result) == 3
        result_ids = {s.id for s in result}
        assert result_ids == {"S1", "S2", "S3"}


class TestBacklogSorterWithWaves:
    """Testes para ordenação de backlog com waves."""

    def test_sort_with_waves_respects_wave_order(self) -> None:
        """Histórias de ondas anteriores vêm primeiro, independente da prioridade."""
        sorter = BacklogSorter()

        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)

        # Story da onda 2 com prioridade 0 (maior prioridade)
        story_wave2 = Story(
            id="S1",
            component="Test",
            name="Test Wave 2",
            story_point=StoryPoint(5),
            feature_id="F2",
            status=StoryStatus.BACKLOG,
            priority=0,
        )
        story_wave2.feature = feature_wave2

        # Story da onda 1 com prioridade 5 (menor prioridade)
        story_wave1 = Story(
            id="S2",
            component="Test",
            name="Test Wave 1",
            story_point=StoryPoint(5),
            feature_id="F1",
            status=StoryStatus.BACKLOG,
            priority=5,
        )
        story_wave1.feature = feature_wave1

        result = sorter.sort([story_wave2, story_wave1])

        # Wave 1 deve vir primeiro, mesmo com prioridade menor
        assert result[0].id == "S2"  # Wave 1
        assert result[1].id == "S1"  # Wave 2

    def test_sort_with_same_wave_respects_priority(self) -> None:
        """Dentro da mesma onda, ordena por prioridade."""
        sorter = BacklogSorter()

        feature = Feature(id="F1", name="Feature 1", wave=1)

        story1 = Story(
            id="S1",
            component="Test",
            name="Test 1",
            story_point=StoryPoint(5),
            feature_id="F1",
            status=StoryStatus.BACKLOG,
            priority=3,
        )
        story1.feature = feature

        story2 = Story(
            id="S2",
            component="Test",
            name="Test 2",
            story_point=StoryPoint(5),
            feature_id="F1",
            status=StoryStatus.BACKLOG,
            priority=1,
        )
        story2.feature = feature

        story3 = Story(
            id="S3",
            component="Test",
            name="Test 3",
            story_point=StoryPoint(5),
            feature_id="F1",
            status=StoryStatus.BACKLOG,
            priority=2,
        )
        story3.feature = feature

        result = sorter.sort([story1, story2, story3])

        # Mesma wave, ordenar por prioridade
        assert result[0].id == "S2"  # Priority 1
        assert result[1].id == "S3"  # Priority 2
        assert result[2].id == "S1"  # Priority 3

    def test_sort_with_dependencies_across_waves(self) -> None:
        """Dependências entre ondas são respeitadas."""
        sorter = BacklogSorter()

        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)

        # Story onda 1 (dependência)
        dep_story = Story(
            id="S1",
            component="Test",
            name="Dependency",
            story_point=StoryPoint(5),
            feature_id="F1",
            status=StoryStatus.BACKLOG,
            priority=0,
        )
        dep_story.feature = feature_wave1

        # Story onda 2 (depende de S1)
        story_wave2 = Story(
            id="S2",
            component="Test",
            name="Depends on S1",
            story_point=StoryPoint(5),
            feature_id="F2",
            status=StoryStatus.BACKLOG,
            priority=0,
            dependencies=["S1"],
        )
        story_wave2.feature = feature_wave2

        result = sorter.sort([story_wave2, dep_story])

        # S1 deve vir primeiro (é dependência)
        assert result[0].id == "S1"
        assert result[1].id == "S2"

    def test_sort_multiple_waves_with_mixed_priorities(self) -> None:
        """Ordenação complexa com múltiplas ondas e prioridades."""
        sorter = BacklogSorter()

        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)
        feature_wave3 = Feature(id="F3", name="Feature Wave 3", wave=3)

        # Wave 1 (2 stories)
        story_w1_p0 = Story(
            id="S1",
            component="Test",
            name="W1 P0",
            story_point=StoryPoint(5),
            feature_id="F1",
            status=StoryStatus.BACKLOG,
            priority=0,
        )
        story_w1_p0.feature = feature_wave1

        story_w1_p1 = Story(
            id="S2",
            component="Test",
            name="W1 P1",
            story_point=StoryPoint(5),
            feature_id="F1",
            status=StoryStatus.BACKLOG,
            priority=1,
        )
        story_w1_p1.feature = feature_wave1

        # Wave 2 (1 story)
        story_w2_p0 = Story(
            id="S3",
            component="Test",
            name="W2 P0",
            story_point=StoryPoint(5),
            feature_id="F2",
            status=StoryStatus.BACKLOG,
            priority=0,
        )
        story_w2_p0.feature = feature_wave2

        # Wave 3 (1 story)
        story_w3_p0 = Story(
            id="S4",
            component="Test",
            name="W3 P0",
            story_point=StoryPoint(5),
            feature_id="F3",
            status=StoryStatus.BACKLOG,
            priority=0,
        )
        story_w3_p0.feature = feature_wave3

        # Inserir em ordem aleatória
        result = sorter.sort([story_w3_p0, story_w1_p1, story_w2_p0, story_w1_p0])

        # Ordenação esperada: Wave 1 (P0, P1), Wave 2 (P0), Wave 3 (P0)
        assert result[0].id == "S1"  # W1 P0
        assert result[1].id == "S2"  # W1 P1
        assert result[2].id == "S3"  # W2 P0
        assert result[3].id == "S4"  # W3 P0

    def test_sort_with_large_wave_numbers(self) -> None:
        """Deve funcionar com números de onda grandes (gaps)."""
        sorter = BacklogSorter()

        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave10 = Feature(id="F10", name="Feature Wave 10", wave=10)
        feature_wave100 = Feature(id="F100", name="Feature Wave 100", wave=100)

        story_w1 = Story(
            id="S1",
            component="Test",
            name="W1",
            story_point=StoryPoint(5),
            feature_id="F1",
            status=StoryStatus.BACKLOG,
            priority=0,
        )
        story_w1.feature = feature_wave1

        story_w10 = Story(
            id="S2",
            component="Test",
            name="W10",
            story_point=StoryPoint(5),
            feature_id="F10",
            status=StoryStatus.BACKLOG,
            priority=0,
        )
        story_w10.feature = feature_wave10

        story_w100 = Story(
            id="S3",
            component="Test",
            name="W100",
            story_point=StoryPoint(5),
            feature_id="F100",
            status=StoryStatus.BACKLOG,
            priority=0,
        )
        story_w100.feature = feature_wave100

        result = sorter.sort([story_w100, story_w10, story_w1])

        # Ordenação por wave crescente
        assert result[0].id == "S1"  # Wave 1
        assert result[1].id == "S2"  # Wave 10
        assert result[2].id == "S3"  # Wave 100

    def test_sort_composite_priority_calculation(self) -> None:
        """Verifica que priority_composta = (wave * 10000) + priority funciona."""
        sorter = BacklogSorter()

        feature_wave1 = Feature(id="F1", name="Feature Wave 1", wave=1)
        feature_wave2 = Feature(id="F2", name="Feature Wave 2", wave=2)

        # Wave 1, Priority 9999 (composite: 19999)
        story_w1_p9999 = Story(
            id="S1",
            component="Test",
            name="W1 P9999",
            story_point=StoryPoint(5),
            feature_id="F1",
            status=StoryStatus.BACKLOG,
            priority=9999,
        )
        story_w1_p9999.feature = feature_wave1

        # Wave 2, Priority 0 (composite: 20000)
        story_w2_p0 = Story(
            id="S2",
            component="Test",
            name="W2 P0",
            story_point=StoryPoint(5),
            feature_id="F2",
            status=StoryStatus.BACKLOG,
            priority=0,
        )
        story_w2_p0.feature = feature_wave2

        result = sorter.sort([story_w2_p0, story_w1_p9999])

        # S1 deve vir primeiro (composite 19999 < 20000), mesmo com priority alta
        assert result[0].id == "S1"  # 19999
        assert result[1].id == "S2"  # 20000
