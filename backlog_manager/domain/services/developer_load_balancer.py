"""Serviço para balancear carga de desenvolvedores."""
import random
from typing import Dict, List, Optional

from backlog_manager.domain.entities.developer import Developer
from backlog_manager.domain.entities.story import Story


class DeveloperLoadBalancer:
    """
    Serviço de domínio para balancear carga entre desenvolvedores.

    Garante distribuição equitativa de histórias considerando
    a carga atual de cada desenvolvedor.
    """

    @staticmethod
    def select_least_loaded_developer(
        developers: List[Developer], all_stories: List[Story]
    ) -> Developer:
        """
        Seleciona desenvolvedor com MENOR número de histórias alocadas.

        Args:
            developers: Lista de desenvolvedores disponíveis
            all_stories: Lista de todas as histórias (para contar carga)

        Returns:
            Desenvolvedor com menor carga

        Raises:
            ValueError: Se lista de desenvolvedores estiver vazia
        """
        if not developers:
            raise ValueError("Lista de desenvolvedores não pode estar vazia")

        # Contar histórias por desenvolvedor
        load_count = DeveloperLoadBalancer._count_stories_per_developer(developers, all_stories)

        # Selecionar desenvolvedor com menor carga
        # Em caso de empate, retorna o primeiro da lista
        least_loaded_dev = min(developers, key=lambda dev: load_count.get(dev.id, 0))

        return least_loaded_dev

    @staticmethod
    def _count_stories_per_developer(
        developers: List[Developer], all_stories: List[Story]
    ) -> Dict[str, int]:
        """
        Conta número de histórias alocadas para cada desenvolvedor.

        Args:
            developers: Lista de desenvolvedores
            all_stories: Lista de todas as histórias

        Returns:
            Dicionário {developer_id: contagem}
        """
        load_count = {dev.id: 0 for dev in developers}

        for story in all_stories:
            if story.developer_id and story.developer_id in load_count:
                load_count[story.developer_id] += 1

        return load_count

    @staticmethod
    def get_load_report(developers: List[Developer], all_stories: List[Story]) -> Dict[str, int]:
        """
        Gera relatório de carga por desenvolvedor.

        Args:
            developers: Lista de desenvolvedores
            all_stories: Lista de histórias

        Returns:
            Dicionário {developer_id: contagem}
        """
        return DeveloperLoadBalancer._count_stories_per_developer(developers, all_stories)

    @staticmethod
    def sort_by_load_and_name(
        developers: List[Developer], all_stories: List[Story]
    ) -> List[Developer]:
        """
        Ordena desenvolvedores por carga e nome alfabético.

        Critérios de ordenação (nesta ordem):
        1. Menor número de histórias alocadas
        2. Nome alfabético (A-Z)

        Args:
            developers: Lista de desenvolvedores
            all_stories: Todas as histórias (para contar carga)

        Returns:
            Lista ordenada de desenvolvedores

        Example:
            >>> devs = [Dev("Carlos", 2 stories), Dev("Ana", 2 stories), Dev("Bruno", 1 story)]
            >>> sorted_devs = sort_by_load_and_name(devs, all_stories)
            >>> # Resultado: [Bruno (1), Ana (2), Carlos (2)]
        """
        # Contar histórias por desenvolvedor
        load_count = DeveloperLoadBalancer._count_stories_per_developer(developers, all_stories)

        # Ordenar por carga (menor primeiro) + nome alfabético
        sorted_devs = sorted(developers, key=lambda d: (load_count.get(d.id, 0), d.name.lower()))

        return sorted_devs

    @staticmethod
    def sort_by_load_random_tiebreak(
        developers: List[Developer], all_stories: List[Story], random_seed: Optional[int] = None
    ) -> List[Developer]:
        """
        Ordena desenvolvedores por carga com desempate ALEATÓRIO.

        Critérios de ordenação (nesta ordem):
        1. Menor número de histórias alocadas
        2. Aleatório entre desenvolvedores com mesma carga

        Args:
            developers: Lista de desenvolvedores
            all_stories: Todas as histórias (para contar carga)
            random_seed: Seed opcional para aleatoriedade determinística (para testes)

        Returns:
            Lista ordenada de desenvolvedores

        Example:
            >>> devs = [Dev("Carlos", 2 stories), Dev("Ana", 2 stories), Dev("Bruno", 1 story)]
            >>> sorted_devs = sort_by_load_random_tiebreak(devs, all_stories)
            >>> # Resultado: [Bruno (1), Ana ou Carlos aleatório (2), Ana ou Carlos aleatório (2)]
        """
        # Configurar seed se fornecida (para testes determinísticos)
        if random_seed is not None:
            random.seed(random_seed)

        # Contar histórias por desenvolvedor
        load_count = DeveloperLoadBalancer._count_stories_per_developer(developers, all_stories)

        # Agrupar desenvolvedores por carga
        by_load: Dict[int, List[Developer]] = {}
        for dev in developers:
            load = load_count.get(dev.id, 0)
            if load not in by_load:
                by_load[load] = []
            by_load[load].append(dev)

        # Ordenar por carga e embaralhar cada grupo
        sorted_devs: List[Developer] = []
        for load in sorted(by_load.keys()):
            group = by_load[load]
            random.shuffle(group)  # Embaralha devs com mesma carga
            sorted_devs.extend(group)

        return sorted_devs
