"""Serviço para ordenar backlog considerando dependências e prioridade."""
from collections import deque

from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.exceptions.domain_exceptions import CyclicDependencyException
from backlog_manager.domain.services.cycle_detector import CycleDetector


class BacklogSorter:
    """
    Serviço de ordenação de backlog usando ordenação topológica.

    Ordena histórias considerando:
    1. Dependências técnicas (histórias sem dependências vêm primeiro)
    2. Prioridade numérica (menor número = maior prioridade)

    Utiliza algoritmo de Kahn para ordenação topológica.
    Complexidade: O(V + E) onde V = histórias, E = dependências
    """

    def __init__(self) -> None:
        """Inicializa o sorter com detector de ciclos."""
        self._cycle_detector = CycleDetector()

    def sort(self, stories: list[Story]) -> list[Story]:
        """
        Ordena lista de histórias respeitando dependências e prioridade.

        Args:
            stories: Lista de histórias para ordenar

        Returns:
            Lista ordenada de histórias

        Raises:
            CyclicDependencyException: Se detectado ciclo nas dependências
        """
        if not stories:
            return []

        # Verificar ciclos primeiro
        dependencies_map = {story.id: story.dependencies for story in stories}
        if self._cycle_detector.has_cycle(dependencies_map):
            self._cycle_detector.find_cycle_path(dependencies_map)

        # Criar mapa de histórias por ID
        stories_map = {story.id: story for story in stories}

        # Calcular in-degree (número de dependências) para cada história
        in_degree: dict[str, int] = {}
        for story in stories:
            if story.id not in in_degree:
                in_degree[story.id] = 0

            for dep_id in story.dependencies:
                # Incrementar in-degree da história que depende de outra
                in_degree[story.id] = in_degree.get(story.id, 0) + 1

        # Fila com histórias que não têm dependências (in-degree = 0)
        # Ordenadas por prioridade
        queue: deque[str] = deque()
        zero_in_degree = [story.id for story in stories if in_degree.get(story.id, 0) == 0]
        # Ordenar por prioridade antes de adicionar na fila
        zero_in_degree.sort(key=lambda sid: stories_map[sid].priority)
        queue.extend(zero_in_degree)

        # Lista resultado ordenada
        sorted_stories: list[Story] = []

        # Processar fila
        while queue:
            # Remover história da fila
            current_id = queue.popleft()
            sorted_stories.append(stories_map[current_id])

            # Para cada história que depende da atual
            for story in stories:
                if current_id in story.dependencies:
                    # Decrementar in-degree
                    in_degree[story.id] -= 1

                    # Se in-degree chegou a 0, adicionar na fila (ordenado por prioridade)
                    if in_degree[story.id] == 0:
                        # Inserir na posição correta mantendo ordem de prioridade
                        inserted = False
                        for i, existing_id in enumerate(queue):
                            if stories_map[story.id].priority < stories_map[existing_id].priority:
                                queue.insert(i, story.id)
                                inserted = True
                                break
                        if not inserted:
                            queue.append(story.id)

        return sorted_stories
