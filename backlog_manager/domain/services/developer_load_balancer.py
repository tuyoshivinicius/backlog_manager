"""Serviço para balancear carga de desenvolvedores."""
import random
from datetime import date
from typing import Dict, List, Optional, Tuple

from backlog_manager.domain.entities.developer import Developer
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator
from backlog_manager.domain.value_objects.allocation_criteria import AllocationCriteria


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

    @staticmethod
    def get_dependency_owner(
        story: Story,
        story_map: Dict[str, Story],
        available_developers: List[Developer]
    ) -> Optional[Developer]:
        """
        Retorna o desenvolvedor que é "dono" de uma dependência da história.

        Prioriza histórias dependentes serem alocadas ao mesmo desenvolvedor
        que trabalhou nas suas dependências (propriedade de contexto).

        Regras:
        1. Se a história não tem dependências, retorna None
        2. Se nenhuma dependência tem desenvolvedor alocado, retorna None
        3. Se o desenvolvedor da dependência não está na lista de disponíveis, retorna None
        4. Se múltiplas dependências têm desenvolvedores diferentes, usa o da primeira

        Args:
            story: História que está sendo alocada
            story_map: Mapa de ID -> Story para busca O(1)
            available_developers: Lista de desenvolvedores disponíveis

        Returns:
            Desenvolvedor que deve ter prioridade, ou None se não houver
        """
        if not story.dependencies:
            return None

        # Criar set de IDs de devs disponíveis para busca O(1)
        available_dev_ids = {dev.id for dev in available_developers}

        # Procurar nas dependências um desenvolvedor alocado que esteja disponível
        for dep_id in story.dependencies:
            dep_story = story_map.get(dep_id)
            if dep_story and dep_story.developer_id:
                # Verificar se o dev da dependência está disponível
                if dep_story.developer_id in available_dev_ids:
                    # Encontrar o objeto Developer correspondente
                    for dev in available_developers:
                        if dev.id == dep_story.developer_id:
                            return dev

        return None

    @staticmethod
    def _get_developer_last_allocation(
        developer_id: int,
        story_map: Dict[str, Story],
    ) -> Optional[Story]:
        """
        Retorna a última história alocada a um desenvolvedor.

        Considera a história com a maior data de fim (end_date).

        Args:
            developer_id: ID do desenvolvedor
            story_map: Mapa de ID -> Story

        Returns:
            A história mais recente do desenvolvedor, ou None se não houver
        """
        dev_stories = [
            story for story in story_map.values()
            if story.developer_id == developer_id and story.end_date is not None
        ]

        if not dev_stories:
            return None

        # Retornar a história com a maior end_date
        return max(dev_stories, key=lambda s: s.end_date)  # type: ignore

    @staticmethod
    def _get_developer_last_allocation_before(
        developer_id: int,
        story_map: Dict[str, Story],
        before_date: date,
        current_wave: Optional[int] = None,
    ) -> Optional[Story]:
        """
        Retorna a última história alocada a um desenvolvedor que termina ANTES de uma data.

        Usado para calcular ociosidade: encontra a história que termina imediatamente
        antes da nova história começar, para medir o gap entre elas.

        Se current_wave for fornecido, considera apenas histórias DA MESMA ONDA,
        pois a ociosidade entre ondas diferentes é permitida.

        Args:
            developer_id: ID do desenvolvedor
            story_map: Mapa de ID -> Story
            before_date: Data limite (busca histórias que terminam ANTES desta data)
            current_wave: Se fornecido, filtra apenas histórias desta onda

        Returns:
            A história mais recente que termina antes de before_date, ou None
        """
        dev_stories = [
            story for story in story_map.values()
            if story.developer_id == developer_id
            and story.end_date is not None
            and story.end_date < before_date  # Somente histórias que terminam ANTES
            and (current_wave is None or story.wave == current_wave)  # Filtrar por onda
        ]

        if not dev_stories:
            return None

        # Retornar a história com a maior end_date (mais próxima de before_date)
        return max(dev_stories, key=lambda s: s.end_date)  # type: ignore

    @staticmethod
    def _calculate_idle_days(
        last_story_end_date: date,
        new_story_start_date: date,
    ) -> int:
        """
        Calcula os dias úteis ociosos entre duas histórias.

        Usa o ScheduleCalculator para considerar feriados brasileiros.

        Args:
            last_story_end_date: Data de fim da última história
            new_story_start_date: Data de início da nova história

        Returns:
            Número de dias úteis ociosos (0 se não houver gap ou sobreposição)
        """
        if new_story_start_date <= last_story_end_date:
            return 0

        calculator = ScheduleCalculator()
        return calculator.count_workdays_between(last_story_end_date, new_story_start_date)

    @staticmethod
    def _filter_developers_by_idle_threshold(
        developers: List[Developer],
        story_map: Dict[str, Story],
        new_story_start_date: date,
        max_idle_days: int,
        current_wave: Optional[int] = None,
    ) -> Tuple[List[Developer], Dict[int, int]]:
        """
        Filtra desenvolvedores que estão dentro do limite de ociosidade NA MESMA ONDA.

        Usa _get_developer_last_allocation_before para encontrar a história
        que termina imediatamente ANTES da nova história, calculando assim
        o gap real de ociosidade.

        Se current_wave for fornecido, apenas considera histórias da mesma onda
        para o cálculo de ociosidade. Gaps entre ondas diferentes são permitidos.

        Args:
            developers: Lista de desenvolvedores a filtrar
            story_map: Mapa de ID -> Story
            new_story_start_date: Data de início da nova história
            max_idle_days: Máximo de dias ociosos permitidos
            current_wave: Onda atual (se fornecido, filtra apenas por esta onda)

        Returns:
            Tupla (lista de devs dentro do limite, dicionário dev_id -> idle_days)
        """
        within_threshold: List[Developer] = []
        idle_days_map: Dict[int, int] = {}

        for dev in developers:
            # Buscar última alocação que termina ANTES da nova história (na mesma onda)
            last_allocation = DeveloperLoadBalancer._get_developer_last_allocation_before(
                dev.id, story_map, new_story_start_date, current_wave
            )

            if last_allocation is None:
                # Desenvolvedor sem alocações anteriores à nova história nesta onda
                # Pode ser: (1) sem histórias na onda, ou (2) primeira história na onda
                idle_days_map[dev.id] = 0
                within_threshold.append(dev)
            else:
                idle_days = DeveloperLoadBalancer._calculate_idle_days(
                    last_allocation.end_date,  # type: ignore
                    new_story_start_date,
                )
                idle_days_map[dev.id] = idle_days

                if idle_days <= max_idle_days:
                    within_threshold.append(dev)

        return within_threshold, idle_days_map

    @staticmethod
    def get_developer_for_story(
        story: Story,
        story_map: Dict[str, Story],
        available_developers: List[Developer],
        all_stories: List[Story],
        allocation_criteria: AllocationCriteria = AllocationCriteria.LOAD_BALANCING,
        random_seed: Optional[int] = None,
        new_story_start_date: Optional[date] = None,
        max_idle_days: Optional[int] = None,
        current_wave: Optional[int] = None,
    ) -> Optional[Developer]:
        """
        Seleciona o melhor desenvolvedor para uma história.

        A estratégia de seleção depende do critério configurado:

        - LOAD_BALANCING: Usa apenas balanceamento de carga (distribuição uniforme)
        - DEPENDENCY_OWNER: Tenta alocar ao "dono" de uma dependência primeiro,
          com fallback para balanceamento de carga

        Adicionalmente, se max_idle_days for fornecido, filtra desenvolvedores
        que estão dentro do limite de ociosidade considerando TODAS as ondas.
        Se nenhum estiver dentro do limite, usa o desenvolvedor com menor
        ociosidade (fallback).

        NOTA: O parâmetro current_wave NÃO é usado para filtrar ociosidade na
        seleção. A ociosidade é calculada desde a última história do desenvolvedor,
        independente da onda. Isso garante que max_idle_days seja respeitado mesmo
        na primeira história de cada onda.

        Args:
            story: História a ser alocada
            story_map: Mapa de ID -> Story para busca O(1)
            available_developers: Lista de desenvolvedores disponíveis
            all_stories: Todas as histórias (para calcular carga)
            allocation_criteria: Critério de alocação configurado
            random_seed: Seed opcional para testes determinísticos
            new_story_start_date: Data de início da nova história (para cálculo de ociosidade)
            max_idle_days: Máximo de dias ociosos permitidos
            current_wave: Onda atual (não usado para seleção, mantido para compatibilidade)

        Returns:
            Desenvolvedor selecionado, ou None se não há disponíveis
        """
        if not available_developers:
            return None

        # Aplicar filtro de ociosidade se parâmetros fornecidos
        candidates = available_developers
        idle_days_map: Dict[int, int] = {}

        if new_story_start_date is not None and max_idle_days is not None:
            # NOTA: Usamos current_wave=None para considerar histórias de TODAS as ondas
            # na seleção do desenvolvedor. O parâmetro current_wave é usado apenas para
            # detecção de warnings de ociosidade, não para seleção.
            # Isso garante que max_idle_days seja respeitado mesmo na primeira história
            # de cada onda.
            within_threshold, idle_days_map = DeveloperLoadBalancer._filter_developers_by_idle_threshold(
                available_developers, story_map, new_story_start_date, max_idle_days,
                current_wave=None  # Considera ociosidade global, não por onda
            )

            if within_threshold:
                # Usar apenas desenvolvedores dentro do limite de ociosidade
                candidates = within_threshold
            else:
                # Nenhum dev dentro do limite: manter todos disponíveis como candidatos
                # O critério de alocação (DEPENDENCY_OWNER → balanceamento) será aplicado
                # normalmente, e o fallback final usará o menos ocioso se necessário.
                candidates = available_developers

        # Se critério for DEPENDENCY_OWNER, tentar priorizar proprietário de dependência
        if allocation_criteria == AllocationCriteria.DEPENDENCY_OWNER:
            dependency_owner = DeveloperLoadBalancer.get_dependency_owner(
                story, story_map, candidates
            )
            if dependency_owner:
                return dependency_owner

        # Usar balanceamento de carga (seja como critério principal ou fallback)
        sorted_devs = DeveloperLoadBalancer.sort_by_load_random_tiebreak(
            candidates, all_stories, random_seed
        )

        return sorted_devs[0] if sorted_devs else None
