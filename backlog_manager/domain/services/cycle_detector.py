"""Serviço para detecção de ciclos em grafo de dependências."""
from enum import Enum
from typing import Optional

from backlog_manager.domain.exceptions.domain_exceptions import CyclicDependencyException


class NodeState(Enum):
    """Estado de um nó durante DFS."""

    UNVISITED = "unvisited"
    VISITING = "visiting"
    VISITED = "visited"


class CycleDetector:
    """
    Serviço de domínio para detectar ciclos em grafo de dependências.

    Utiliza algoritmo DFS (Depth-First Search) para detectar ciclos
    em grafo direcionado de dependências entre histórias.

    Complexidade: O(V + E) onde V = vértices, E = arestas
    """

    def has_cycle(self, dependencies: dict[str, list[str]]) -> bool:
        """
        Verifica se existe ciclo no grafo de dependências.

        Args:
            dependencies: Dicionário {story_id: [list_of_dependencies]}

        Returns:
            True se houver ciclo, False caso contrário

        Example:
            >>> detector = CycleDetector()
            >>> deps = {"A": ["B"], "B": ["A"]}
            >>> detector.has_cycle(deps)
            True
        """
        try:
            self.find_cycle_path(dependencies)
            return False
        except CyclicDependencyException:
            return True

    def find_cycle_path(self, dependencies: dict[str, list[str]]) -> Optional[list[str]]:
        """
        Encontra caminho do ciclo se existir.

        Args:
            dependencies: Dicionário {story_id: [list_of_dependencies]}

        Returns:
            Lista de IDs formando o ciclo, ou None se sem ciclo

        Raises:
            CyclicDependencyException: Se ciclo detectado
        """
        # Inicializar estados de todos os nós
        states: dict[str, NodeState] = {}
        all_nodes = set(dependencies.keys())
        for deps_list in dependencies.values():
            all_nodes.update(deps_list)

        for node in all_nodes:
            states[node] = NodeState.UNVISITED

        # DFS para cada nó não visitado
        for node in all_nodes:
            if states[node] == NodeState.UNVISITED:
                path: list[str] = []
                cycle = self._dfs(node, dependencies, states, path)
                if cycle:
                    raise CyclicDependencyException(cycle)

        return None

    def _dfs(
        self,
        node: str,
        dependencies: dict[str, list[str]],
        states: dict[str, NodeState],
        path: list[str],
    ) -> Optional[list[str]]:
        """
        Executa DFS recursivo a partir de um nó.

        Args:
            node: Nó atual
            dependencies: Grafo de dependências
            states: Estados dos nós
            path: Caminho atual sendo explorado

        Returns:
            Lista formando ciclo se detectado, None caso contrário
        """
        states[node] = NodeState.VISITING
        path.append(node)

        # Visitar dependências
        for dependency in dependencies.get(node, []):
            if states.get(dependency, NodeState.UNVISITED) == NodeState.VISITING:
                # Ciclo detectado! Construir caminho do ciclo
                cycle_start_index = path.index(dependency)
                cycle_path = path[cycle_start_index:] + [dependency]
                return cycle_path

            if states.get(dependency, NodeState.UNVISITED) == NodeState.UNVISITED:
                cycle = self._dfs(dependency, dependencies, states, path)
                if cycle:
                    return cycle

        states[node] = NodeState.VISITED
        path.pop()
        return None
