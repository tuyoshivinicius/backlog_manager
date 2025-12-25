"""Testes para CycleDetector."""
import time

import pytest

from backlog_manager.domain.exceptions.domain_exceptions import CyclicDependencyException
from backlog_manager.domain.services.cycle_detector import CycleDetector


class TestCycleDetector:
    """Testes para detecção de ciclos."""

    def test_no_cycle_empty_graph(self) -> None:
        """Grafo vazio não tem ciclo."""
        detector = CycleDetector()
        assert not detector.has_cycle({})

    def test_no_cycle_single_node(self) -> None:
        """Nó único sem dependências não tem ciclo."""
        detector = CycleDetector()
        deps = {"A": []}
        assert not detector.has_cycle(deps)

    def test_no_cycle_linear_dependency(self) -> None:
        """Dependência linear não tem ciclo."""
        detector = CycleDetector()
        deps = {"A": ["B"], "B": ["C"], "C": []}
        assert not detector.has_cycle(deps)

    def test_detects_simple_cycle(self) -> None:
        """Deve detectar ciclo simples A → B → A."""
        detector = CycleDetector()
        deps = {"A": ["B"], "B": ["A"]}
        assert detector.has_cycle(deps)

        with pytest.raises(CyclicDependencyException) as exc_info:
            detector.find_cycle_path(deps)

        assert "A" in exc_info.value.cycle_path
        assert "B" in exc_info.value.cycle_path

    def test_detects_indirect_cycle(self) -> None:
        """Deve detectar ciclo indireto A → B → C → A."""
        detector = CycleDetector()
        deps = {"A": ["B"], "B": ["C"], "C": ["A"]}
        assert detector.has_cycle(deps)

    def test_detects_self_loop(self) -> None:
        """Deve detectar auto-referência A → A."""
        detector = CycleDetector()
        deps = {"A": ["A"]}
        assert detector.has_cycle(deps)

    def test_complex_graph_no_cycle(self) -> None:
        """Grafo complexo sem ciclo (DAG)."""
        detector = CycleDetector()
        deps = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": ["E"], "E": []}
        assert not detector.has_cycle(deps)

    def test_complex_graph_with_cycle(self) -> None:
        """Grafo complexo com ciclo escondido."""
        detector = CycleDetector()
        deps = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": ["E"], "E": ["B"]}
        assert detector.has_cycle(deps)

    def test_cycle_path_contains_cycle_only(self) -> None:
        """Caminho do ciclo deve conter apenas os nós do ciclo."""
        detector = CycleDetector()
        deps = {"A": ["B"], "B": ["C"], "C": ["B"]}  # Ciclo: B → C → B

        with pytest.raises(CyclicDependencyException) as exc_info:
            detector.find_cycle_path(deps)

        cycle_path = exc_info.value.cycle_path
        assert "B" in cycle_path
        assert "C" in cycle_path

    def test_multiple_components_no_cycle(self) -> None:
        """Grafo com múltiplos componentes sem ciclo."""
        detector = CycleDetector()
        deps = {"A": ["B"], "B": [], "C": ["D"], "D": []}
        assert not detector.has_cycle(deps)

    def test_multiple_components_with_cycle(self) -> None:
        """Grafo com múltiplos componentes, um com ciclo."""
        detector = CycleDetector()
        deps = {"A": ["B"], "B": [], "C": ["D"], "D": ["C"]}
        assert detector.has_cycle(deps)

    def test_diamond_graph_no_cycle(self) -> None:
        """Grafo em formato diamante sem ciclo."""
        detector = CycleDetector()
        deps = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        assert not detector.has_cycle(deps)

    def test_nodes_only_in_dependencies(self) -> None:
        """Nós que aparecem apenas como dependências."""
        detector = CycleDetector()
        deps = {"A": ["B", "C"]}  # B e C não têm suas próprias dependências
        assert not detector.has_cycle(deps)

    def test_performance_large_graph(self) -> None:
        """Deve processar grafo grande rapidamente."""
        detector = CycleDetector()

        # Criar grafo com 100 nós em cadeia (sem ciclo)
        deps = {f"S{i}": [f"S{i+1}"] for i in range(99)}
        deps["S99"] = []

        start = time.time()
        result = detector.has_cycle(deps)
        elapsed = time.time() - start

        assert not result
        assert elapsed < 0.1  # Deve ser < 100ms

    def test_performance_large_graph_with_cycle(self) -> None:
        """Deve detectar ciclo em grafo grande rapidamente."""
        detector = CycleDetector()

        # Criar grafo com 100 nós em cadeia com ciclo no final
        deps = {f"S{i}": [f"S{i+1}"] for i in range(99)}
        deps["S99"] = ["S0"]  # Ciclo: volta ao início

        start = time.time()
        result = detector.has_cycle(deps)
        elapsed = time.time() - start

        assert result
        assert elapsed < 0.1  # Deve ser < 100ms

    def test_cycle_path_format(self) -> None:
        """Deve formatar caminho do ciclo corretamente."""
        detector = CycleDetector()
        deps = {"A": ["B"], "B": ["C"], "C": ["A"]}

        with pytest.raises(CyclicDependencyException) as exc_info:
            detector.find_cycle_path(deps)

        # Verificar que a mensagem contém o símbolo de seta
        assert "->" in str(exc_info.value)

    def test_find_cycle_path_returns_none_when_no_cycle(self) -> None:
        """find_cycle_path deve retornar None quando não há ciclo."""
        detector = CycleDetector()
        deps = {"A": ["B"], "B": ["C"], "C": []}

        result = detector.find_cycle_path(deps)
        assert result is None
