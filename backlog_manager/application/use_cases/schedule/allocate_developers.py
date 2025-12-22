"""Caso de uso para alocar desenvolvedores."""
from datetime import date
from typing import List, Set, Tuple

from backlog_manager.application.interfaces.repositories.configuration_repository import (
    ConfigurationRepository,
)
from backlog_manager.application.interfaces.repositories.developer_repository import (
    DeveloperRepository,
)
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.domain.entities.developer import Developer
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.services.developer_load_balancer import DeveloperLoadBalancer
from backlog_manager.domain.services.idleness_detector import IdlenessDetector, IdlenessWarning
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator


class NoDevelopersAvailableException(Exception):
    """Lançada quando não há desenvolvedores disponíveis."""

    pass


class AllocateDevelopersUseCase:
    """
    Caso de uso para alocar desenvolvedores em histórias.

    **ALGORITMO - RF-ALOC-001 (Lista Simples com Flag de Ajuste Único):**

    Estratégia:
    0. Sincroniza schedule_order com ordem ATUAL da tabela (priority)
    1. Loop contínuo até não haver mais histórias não alocadas:
       - Lista histórias não alocadas
       - Itera sequencialmente sobre cada história
       - Se há dev disponível: aloca e REINICIA lista
       - Se não há dev disponível:
         * Se já foi ajustada (flag): pula para próxima
         * Se não foi ajustada: ajusta +1 dia e marca flag
    2. Balanceia carga entre desenvolvedores (menos histórias + desempate aleatório)
    3. Detecta e reporta gaps de ociosidade

    Diferenças do algoritmo anterior:
    - SEM fila de pendentes: lista simples que reinicia após cada alocação
    - Incremento ÚNICO: cada história só pode ter data ajustada UMA vez (+1 dia)
    - Desempate ALEATÓRIO: entre devs com mesma carga (antes era alfabético)
    - Flag temporária: controla se história já foi ajustada (não persiste no banco)

    O campo schedule_order:
    - É atualizado AUTOMATICAMENTE no início de cada alocação
    - Reflete a ordem ATUAL da tabela (ordenada por priority)
    - Permite que mudanças manuais de prioridade sejam respeitadas
    - Garante que alocação usa ordem visual da tabela

    Responsabilidades:
    - Sincronizar schedule_order com tabela
    - Buscar histórias não alocadas
    - Ordenar por schedule_order
    - Buscar desenvolvedores disponíveis
    - Distribuir com balanceamento de carga (desempate aleatório)
    - Ajustar datas (+1 dia) quando não há disponibilidade (máx 1x por história)
    - Detectar deadlock (quando nenhuma história pode ser alocada)
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
        schedule_calculator: ScheduleCalculator,
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
        Aloca desenvolvedores usando algoritmo RF-ALOC-001.

        **ALGORITMO (Lista Simples com Flag de Ajuste Único):**

        0. Atualiza schedule_order baseado na ordem atual da tabela (priority)
        1. Valida desenvolvedores (lança exceção se nenhum)
        2. Cria contexto: adjusted_stories = set() (flag de ajuste)
        3. Loop principal (máx 1000 iterações):
           - Lista histórias não alocadas (com datas definidas)
           - Se lista vazia: PARAR (todas alocadas)
           - Para cada história:
             * Busca desenvolvedores disponíveis
             * Se há dev: aloca (desempate aleatório) e REINICIA lista
             * Se não há dev:
               - Se já foi ajustada: PULA
               - Se não foi ajustada: +1 dia útil e marca flag
           - Se nenhuma alocação nesta iteração: BREAK (deadlock)
        4. Detecta ociosidade após todas as alocações

        **Critérios de Parada:**
        - Todas histórias alocadas → SUCESSO
        - Nenhuma história pode ser alocada (deadlock) → PARAR
        - Limite de iterações (1000) → PARAR (evitar loop infinito)

        Returns:
            Tupla (total_alocado, lista_de_warnings)

        Raises:
            NoDevelopersAvailableException: Se não há desenvolvedores cadastrados
        """
        # 0. SINCRONIZAR schedule_order com ordem ATUAL da tabela
        self._update_schedule_order_from_table()

        # 1. VALIDAÇÕES
        developers = self._developer_repository.find_all()
        if not developers:
            raise NoDevelopersAvailableException("Nenhum desenvolvedor disponível para alocação")

        config = self._configuration_repository.get()

        # 2. CONTEXTO DE ALOCAÇÃO (flags de ajuste - RF-ALOC-007)
        adjusted_stories_ever: Set[str] = set()  # Flag permanente
        adjusted_stories_last_iteration: Set[str] = set()  # Flag volátil
        allocated_count = 0
        max_iterations = 1000

        # 3. LOOP PRINCIPAL
        for iteration in range(max_iterations):
            # Resetar flag "desta iteração"
            adjusted_stories_this_iteration: Set[str] = set()
            # 4. LISTAR histórias não alocadas
            all_stories = self._story_repository.find_all()
            unallocated_stories = self._get_unallocated_stories(all_stories)

            if not unallocated_stories:
                break  # Todas alocadas

            # 5. FLAG para detectar se houve alocação nesta iteração
            allocation_made = False

            # 5.1. VERIFICAR se há histórias que NÃO foram ajustadas na última iteração
            # (para decidir se devemos pular ou não)
            stories_not_adjusted_last = [
                s for s in unallocated_stories if s.id not in adjusted_stories_last_iteration
            ]
            has_unadjusted_stories = len(stories_not_adjusted_last) > 0

            # 6. ITERAR sobre cada história
            for story in unallocated_stories:
                # 7. VERIFICAR disponibilidade
                available_devs = self._get_available_developers(
                    story.start_date,  # type: ignore
                    story.end_date,  # type: ignore
                    all_stories,
                    developers,
                )

                if available_devs:
                    # 8. HÁ DEV DISPONÍVEL - ALOCAR
                    # Ordenar com desempate aleatório
                    sorted_devs = self._load_balancer.sort_by_load_random_tiebreak(
                        available_devs, all_stories
                    )

                    # Alocar primeiro
                    selected_dev = sorted_devs[0]
                    story.allocate_developer(selected_dev.id)
                    self._story_repository.save(story)

                    allocated_count += 1
                    allocation_made = True

                    # 9. REINICIAR (vai buscar lista atualizada)
                    break  # Sai do for, volta ao while

                else:
                    # 10. NÃO HÁ DEV - VERIFICAR FLAGS (RF-ALOC-006 a RF-ALOC-009)

                    already_adjusted_ever = story.id in adjusted_stories_ever

                    if already_adjusted_ever:
                        # Já foi ajustada alguma vez
                        adjusted_last_iteration = story.id in adjusted_stories_last_iteration

                        if adjusted_last_iteration and has_unadjusted_stories:
                            # Ajustada na iteração anterior E há outras histórias não ajustadas:
                            # PULAR para dar prioridade às outras (RF-ALOC-009)
                            continue
                        else:
                            # Não foi na última iteração OU não há outras histórias:
                            # AJUSTAR (RF-ALOC-008)
                            self._adjust_story_dates(story, 1, config)
                            adjusted_stories_ever.add(story.id)
                            adjusted_stories_this_iteration.add(story.id)
                            self._story_repository.save(story)
                    else:
                        # Nunca foi ajustada: AJUSTAR pela primeira vez (RF-ALOC-008)
                        self._adjust_story_dates(story, 1, config)
                        adjusted_stories_ever.add(story.id)
                        adjusted_stories_this_iteration.add(story.id)
                        self._story_repository.save(story)

            # FIM do loop de histórias

            # Atualizar flag "última iteração" para próxima rodada (RF-ALOC-007)
            adjusted_stories_last_iteration = adjusted_stories_this_iteration.copy()

            # 11. DETECÇÃO DE DEADLOCK REAL (RF-ALOC-010)
            if not allocation_made and len(adjusted_stories_this_iteration) == 0:
                # Nenhuma alocação E nenhum ajuste de data nesta iteração
                # DEADLOCK REAL: não há progresso possível
                break

        # 12. DETECTAR OCIOSIDADE
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
        # 1. Buscar TODAS as histórias ordenadas by priority (ordem da tabela)
        all_stories = self._story_repository.find_all()

        # 2. Atualizar schedule_order = índice na ordem atual
        for index, story in enumerate(all_stories):
            story.schedule_order = index
            self._story_repository.save(story)

    def _get_unallocated_stories(self, all_stories: List[Story]) -> List[Story]:
        """
        Retorna histórias elegíveis para alocação.

        Elegível se:
        - Não tem desenvolvedor
        - Tem datas definidas
        - Tem story point definido

        Ordenadas por schedule_order.

        Args:
            all_stories: Lista de todas as histórias

        Returns:
            Lista ordenada de histórias elegíveis
        """
        eligible = [
            s
            for s in all_stories
            if s.developer_id is None
            and s.start_date is not None
            and s.end_date is not None
            and s.story_point is not None
        ]

        # Ordenar por schedule_order
        eligible.sort(
            key=lambda s: s.schedule_order if s.schedule_order is not None else float("inf")
        )

        return eligible

    def _get_available_developers(
        self,
        start_date: date,
        end_date: date,
        all_stories: List[Story],
        developers: List[Developer],
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
                s
                for s in all_stories
                if s.developer_id == dev.id and s.start_date is not None and s.end_date is not None
            ]

            # Verificar se há sobreposição
            has_overlap = False
            for story in dev_stories:
                if self._periods_overlap(
                    start_date,
                    end_date,
                    story.start_date,  # type: ignore
                    story.end_date,  # type: ignore
                ):
                    has_overlap = True
                    break

            if not has_overlap:
                available.append(dev)

        return available

    def _adjust_story_dates(self, story: Story, days_to_add: int, config: Configuration) -> None:
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
        new_start = self._schedule_calculator.add_workdays(story.start_date, days_to_add)

        # Calcular nova data de fim mantendo duração
        if story.duration:
            # Duration - 1 porque add_workdays usa offset semantics
            new_end = self._schedule_calculator.add_workdays(new_start, story.duration - 1)
        else:
            # Se não tem duração, manter intervalo
            if story.end_date is None:
                return

            # Calcular número de dias úteis entre start e end
            workdays = self._count_workdays(story.start_date, story.end_date)
            # Workdays já é a contagem de dias no intervalo, usar -1 para offset
            new_end = self._schedule_calculator.add_workdays(new_start, max(0, workdays - 1))

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

    def _periods_overlap(self, start1: date, end1: date, start2: date, end2: date) -> bool:
        """
        Verifica se dois períodos se sobrepõem.

        Args:
            start1, end1: Período 1
            start2, end2: Período 2

        Returns:
            True se períodos se sobrepõem
        """
        return start1 <= end2 and start2 <= end1
