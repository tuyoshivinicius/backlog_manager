"""Caso de uso para alocar desenvolvedores."""
from typing import Tuple, List, Optional
from datetime import date
from dataclasses import dataclass

from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.application.interfaces.repositories.configuration_repository import ConfigurationRepository
from backlog_manager.domain.entities.developer import Developer
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.domain.services.developer_load_balancer import DeveloperLoadBalancer
from backlog_manager.domain.services.idleness_detector import IdlenessDetector, IdlenessWarning
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator


class NoDevelopersAvailableException(Exception):
    """Lançada quando não há desenvolvedores disponíveis."""

    pass


@dataclass
class PendingStory:
    """
    Representa uma história pendente de alocação.

    Mantém o número de tentativas de alocação para calcular
    o incremento linear de dias.
    """

    story: Story
    attempts: int = 0

    def next_increment(self) -> int:
        """
        Calcula próximo incremento linear de dias.

        Returns:
            Número de dias a incrementar (1, 2, 3, 4...)

        Examples:
            >>> ps = PendingStory(story, attempts=0)
            >>> ps.next_increment()
            1
            >>> ps = PendingStory(story, attempts=1)
            >>> ps.next_increment()
            2
            >>> ps = PendingStory(story, attempts=3)
            >>> ps.next_increment()
            4
        """
        return self.attempts + 1


class AllocationQueue:
    """
    Fila de histórias pendentes de alocação.

    Mantém histórias que não puderam ser alocadas imediatamente
    devido à indisponibilidade de desenvolvedores.
    """

    def __init__(self):
        """Inicializa fila vazia."""
        self._pending: List[PendingStory] = []

    def add(self, story: Story, attempts: int = 0) -> None:
        """
        Adiciona história à fila de pendentes.

        Args:
            story: História a adicionar
            attempts: Número de tentativas anteriores
        """
        self._pending.append(PendingStory(story, attempts))

    def pop_next(self) -> Optional[PendingStory]:
        """
        Remove e retorna próxima história pendente.

        Returns:
            PendingStory ou None se fila vazia
        """
        if not self._pending:
            return None
        return self._pending.pop(0)

    def is_empty(self) -> bool:
        """
        Verifica se fila está vazia.

        Returns:
            True se fila vazia
        """
        return len(self._pending) == 0

    def size(self) -> int:
        """
        Retorna tamanho da fila.

        Returns:
            Número de histórias pendentes
        """
        return len(self._pending)


class AllocateDevelopersUseCase:
    """
    Caso de uso para alocar desenvolvedores em histórias.

    **NOVO ALGORITMO - Baseado em Ordem da Tabela (schedule_order):**

    Estratégia:
    0. Sincroniza schedule_order com ordem ATUAL da tabela (priority)
    1. Ordena histórias por schedule_order (reflete ordem da tabela)
    2. Mantém fila de histórias pendentes
    3. Prioriza retorno a histórias pendentes antes de processar novas
    4. Quando não há dev disponível: ajusta data de início da história
    5. Usa incremento linear nas tentativas (1, 2, 3, 4...)
    6. Balanceia carga entre desenvolvedores (menos histórias + alfabético)

    O campo schedule_order:
    - É atualizado AUTOMATICAMENTE no início de cada alocação
    - Reflete a ordem ATUAL da tabela (ordenada por priority)
    - Permite que mudanças manuais de prioridade sejam respeitadas
    - Garante que alocação usa ordem visual da tabela

    Fluxo:
    1. Usuário pode reordenar histórias manualmente (muda priority)
    2. Ao clicar "Alocar Desenvolvedores":
       - schedule_order é atualizado automaticamente
       - Alocação usa ordem atual (não ordem do último Calcular Cronograma)

    Responsabilidades:
    - Sincronizar schedule_order com tabela
    - Buscar histórias não alocadas
    - Ordenar por schedule_order
    - Buscar desenvolvedores disponíveis
    - Distribuir com balanceamento de carga
    - Ajustar datas quando não há disponibilidade
    - Detectar e reportar gaps de ociosidade
    - Persistir alocações
    """

    def __init__(
        self,
        story_repository: StoryRepository,
        developer_repository: DeveloperRepository,
        configuration_repository: ConfigurationRepository,
        load_balancer: DeveloperLoadBalancer,
        idleness_detector: IdlenessDetector,
        schedule_calculator: ScheduleCalculator
    ):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            developer_repository: Repositório de desenvolvedores
            configuration_repository: Repositório de configuração
            load_balancer: Serviço de balanceamento de carga
            idleness_detector: Serviço de detecção de ociosidade
            schedule_calculator: Serviço de cálculo de cronograma
        """
        self._story_repository = story_repository
        self._developer_repository = developer_repository
        self._configuration_repository = configuration_repository
        self._load_balancer = load_balancer
        self._idleness_detector = idleness_detector
        self._schedule_calculator = schedule_calculator

    def execute(self) -> Tuple[int, List[IdlenessWarning]]:
        """
        Aloca desenvolvedores usando ordem ATUAL da tabela (schedule_order).

        **ALGORITMO:**

        0. Atualiza schedule_order baseado na ordem atual da tabela (priority)
        1. Busca histórias não alocadas com datas e story points definidos
        2. Ordena por schedule_order (reflete ordem atual da tabela)
        3. Cria fila de histórias pendentes
        4. Loop principal:
           - PRIORIDADE 1: Processar fila de pendentes primeiro
           - PRIORIDADE 2: Processar próxima história não alocada (na ordem de schedule_order)
           - Buscar desenvolvedores disponíveis no período da história
           - Se há disponíveis: alocar para o com menos histórias
           - Se não há disponíveis: ajustar data da história (+incremento linear)
        5. Detectar ociosidade após todas as alocações

        **Critérios de Parada:**
        - Todas histórias alocadas → SUCESSO
        - Limite de iterações (1000) → PARAR (evitar loop infinito)

        Returns:
            Tupla (total_alocado, lista_de_warnings)

        Raises:
            NoDevelopersAvailableException: Se não há desenvolvedores cadastrados
        """
        # 0. SINCRONIZAR schedule_order com ordem ATUAL da tabela
        self._update_schedule_order_from_table()

        # 1. INICIALIZAÇÃO
        developers = self._developer_repository.find_all()
        if not developers:
            raise NoDevelopersAvailableException(
                "Nenhum desenvolvedor disponível para alocação"
            )

        config = self._configuration_repository.get()

        # 2. BUSCAR HISTÓRIAS ELEGÍVEIS
        all_stories = self._story_repository.find_all()
        eligible_stories = [
            s for s in all_stories
            if s.developer_id is None
            and s.start_date is not None
            and s.end_date is not None
            and s.story_point is not None
        ]

        if not eligible_stories:
            return 0, []  # Nada a alocar

        # 3. ORDENAR por schedule_order (ordem ATUAL da tabela)
        eligible_stories.sort(key=lambda s: s.schedule_order if s.schedule_order is not None else float('inf'))

        # 4. CRIAR FILA DE PENDENTES
        pending_queue = AllocationQueue()

        # 5. ITERAÇÃO PRINCIPAL
        allocated_count = 0
        max_iterations = 1000  # Evitar loop infinito
        iteration = 0
        processed_ids = set()  # Rastrear histórias já processadas

        while iteration < max_iterations:
            iteration += 1

            # **PRIORIDADE 1: Processar fila de pendentes PRIMEIRO**
            pending_story = pending_queue.pop_next()

            if pending_story is not None:
                story = pending_story.story
                attempts = pending_story.attempts
            else:
                # **PRIORIDADE 2: Pegar próxima história não alocada**
                story = self._get_next_unallocated_story(eligible_stories, processed_ids)

                if story is None:
                    # Todas histórias foram processadas
                    break

                attempts = 0
                processed_ids.add(story.id)

            # Buscar histórias atualizadas (podem ter sido alocadas em iterações anteriores)
            all_stories = self._story_repository.find_all()

            # 6. TENTAR ALOCAR DESENVOLVEDOR
            available_devs = self._get_available_developers(
                story.start_date,  # type: ignore
                story.end_date,  # type: ignore
                all_stories,
                developers
            )

            if not available_devs:
                # **NÃO HÁ DEV DISPONÍVEL → AJUSTAR DATA DA HISTÓRIA**

                # Calcular incremento linear
                increment = self._calculate_linear_increment(attempts)

                # Ajustar data de início (adicionar dias úteis)
                self._adjust_story_dates(story, increment, config)

                # Incrementar tentativas
                attempts += 1

                # Adicionar de volta à fila de pendentes
                pending_queue.add(story, attempts)

                # Salvar alteração de data
                self._story_repository.save(story)

                continue  # Próxima iteração

            # **HÁ DEV DISPONÍVEL → ALOCAR**

            # Ordenar devs por balanceamento + alfabético
            sorted_devs = self._load_balancer.sort_by_load_and_name(
                available_devs, all_stories
            )

            # Selecionar primeiro (menos histórias + alfabético)
            selected_dev = sorted_devs[0]

            # Alocar
            story.allocate_developer(selected_dev.id)
            self._story_repository.save(story)

            allocated_count += 1

        # 7. DETECTAR OCIOSIDADE
        all_stories = self._story_repository.find_all()
        warnings = self._idleness_detector.detect_idleness(all_stories)

        return allocated_count, warnings

    def _update_schedule_order_from_table(self) -> None:
        """
        Atualiza schedule_order de todas as histórias baseado na ordem ATUAL da tabela.

        Este método sincroniza schedule_order com a ordem visual da tabela (ordenada por priority),
        permitindo que mudanças manuais de prioridade sejam refletidas na alocação.

        Chamado automaticamente no início de execute() antes da alocação.
        """
        # 1. Buscar TODAS as histórias ordenadas por priority (ordem da tabela)
        all_stories = self._story_repository.find_all()

        # 2. Atualizar schedule_order = índice na ordem atual
        for index, story in enumerate(all_stories):
            story.schedule_order = index
            self._story_repository.save(story)

    def _get_next_unallocated_story(
        self,
        stories: List[Story],
        processed_ids: set
    ) -> Optional[Story]:
        """
        Retorna próxima história não alocada na ordem da tabela (schedule_order).

        Args:
            stories: Lista de histórias ordenadas por schedule_order
            processed_ids: IDs de histórias já processadas

        Returns:
            Próxima história não alocada ou None se todas foram processadas
        """
        for story in stories:
            if story.id not in processed_ids and story.developer_id is None:
                return story
        return None

    def _get_available_developers(
        self,
        start_date: date,
        end_date: date,
        all_stories: List[Story],
        developers: List[Developer]
    ) -> List[Developer]:
        """
        Retorna desenvolvedores disponíveis no período.

        Um desenvolvedor está disponível se NÃO tem histórias
        alocadas com período sobreposto.

        Args:
            start_date: Data de início do período
            end_date: Data de fim do período
            all_stories: Todas as histórias
            developers: Lista de desenvolvedores

        Returns:
            Lista de desenvolvedores disponíveis
        """
        available = []

        for dev in developers:
            # Buscar histórias deste desenvolvedor
            dev_stories = [
                s for s in all_stories
                if s.developer_id == dev.id
                and s.start_date is not None
                and s.end_date is not None
            ]

            # Verificar se há sobreposição
            has_overlap = False
            for story in dev_stories:
                if self._periods_overlap(
                    start_date, end_date,
                    story.start_date,  # type: ignore
                    story.end_date  # type: ignore
                ):
                    has_overlap = True
                    break

            if not has_overlap:
                available.append(dev)

        return available

    def _calculate_linear_increment(self, attempts: int) -> int:
        """
        Calcula incremento linear de dias.

        Formula: attempts + 1

        Args:
            attempts: Número de tentativas anteriores

        Returns:
            Número de dias a incrementar

        Examples:
            >>> _calculate_linear_increment(0)
            1
            >>> _calculate_linear_increment(1)
            2
            >>> _calculate_linear_increment(3)
            4
        """
        return attempts + 1

    def _adjust_story_dates(
        self,
        story: Story,
        days_to_add: int,
        config: Configuration
    ) -> None:
        """
        Ajusta datas da história adicionando dias ÚTEIS.

        Usa o ScheduleCalculator para adicionar dias úteis corretamente
        (considerando apenas segunda a sexta).

        Args:
            story: História a ajustar
            days_to_add: Número de dias úteis a adicionar
            config: Configuração (não usado atualmente)
        """
        if story.start_date is None:
            return

        # Usar método do ScheduleCalculator para adicionar dias úteis
        new_start = self._schedule_calculator.add_workdays(
            story.start_date,
            days_to_add
        )

        # Calcular nova data de fim mantendo duração
        if story.duration:
            new_end = self._schedule_calculator.add_workdays(
                new_start,
                story.duration
            )
        else:
            # Se não tem duração, manter intervalo
            if story.end_date is None:
                return

            # Calcular número de dias úteis entre start e end
            workdays = self._count_workdays(story.start_date, story.end_date)
            new_end = self._schedule_calculator.add_workdays(new_start, workdays)

        story.start_date = new_start
        story.end_date = new_end

    def _count_workdays(self, start: date, end: date) -> int:
        """
        Conta número de dias úteis entre duas datas.

        Args:
            start: Data inicial
            end: Data final

        Returns:
            Número de dias úteis
        """
        from datetime import timedelta

        if start > end:
            return 0

        current = start
        count = 0

        while current <= end:
            if current.weekday() < 5:  # Segunda a Sexta
                count += 1
            current = current + timedelta(days=1)

        return count

    def _periods_overlap(
        self,
        start1: date,
        end1: date,
        start2: date,
        end2: date
    ) -> bool:
        """
        Verifica se dois períodos se sobrepõem.

        Args:
            start1, end1: Período 1
            start2, end2: Período 2

        Returns:
            True se períodos se sobrepõem
        """
        return start1 <= end2 and start2 <= end1
