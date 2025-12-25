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
    2. Onda da feature (ondas menores vêm primeiro)
    3. Prioridade numérica dentro da onda (menor número = maior prioridade)

    Utiliza algoritmo de Kahn para ordenação topológica com prioridade composta:
    priority_composta = (wave * 10000) + priority

    Isso garante que:
    - Ondas anteriores sempre vêm primeiro (wave * 10000 domina)
    - Dentro da mesma onda, prioridade desempata (+ priority)
    - Suporta até 9999 histórias por onda

    Complexidade: O(V + E) onde V = histórias, E = dependências
    """

    def __init__(self) -> None:
        """Inicializa o sorter com detector de ciclos."""
        self._cycle_detector = CycleDetector()

    def sort(self, stories: list[Story]) -> list[Story]:
        """
        Ordena lista de histórias respeitando dependências, ondas e prioridade.

        Args:
            stories: Lista de histórias para ordenar (devem ter features carregadas)

        Returns:
            Lista ordenada de histórias

        Raises:
            CyclicDependencyException: Se detectado ciclo nas dependências
            AttributeError: Se alguma história não tem feature carregada
        """
        if not stories:
            return []

        # Verificar ciclos primeiro
        dependencies_map = {story.id: story.dependencies for story in stories}
        if self._cycle_detector.has_cycle(dependencies_map):
            self._cycle_detector.find_cycle_path(dependencies_map)

        # Criar mapa de histórias por ID
        stories_map = {story.id: story for story in stories}

        # Função auxiliar para calcular prioridade composta
        def _composite_priority(story: Story) -> int:
            """Calcula prioridade composta: (wave * 10000) + priority."""
            return (story.wave * 10000) + story.priority

        # Calcular in-degree (número de dependências) para cada história
        in_degree: dict[str, int] = {}
        for story in stories:
            if story.id not in in_degree:
                in_degree[story.id] = 0

            for dep_id in story.dependencies:
                # Incrementar in-degree da história que depende de outra
                in_degree[story.id] = in_degree.get(story.id, 0) + 1

        # Fila com histórias que não têm dependências (in-degree = 0)
        # Ordenadas por prioridade composta (wave * 10000 + priority)
        queue: deque[str] = deque()
        zero_in_degree = [story.id for story in stories if in_degree.get(story.id, 0) == 0]
        # Ordenar por prioridade composta antes de adicionar na fila
        zero_in_degree.sort(key=lambda sid: _composite_priority(stories_map[sid]))
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

                    # Se in-degree chegou a 0, adicionar na fila (ordenado por prioridade composta)
                    if in_degree[story.id] == 0:
                        # Inserir na posição correta mantendo ordem de prioridade composta
                        inserted = False
                        story_composite = _composite_priority(stories_map[story.id])
                        for i, existing_id in enumerate(queue):
                            if story_composite < _composite_priority(stories_map[existing_id]):
                                queue.insert(i, story.id)
                                inserted = True
                                break
                        if not inserted:
                            queue.append(story.id)

        return sorted_stories
