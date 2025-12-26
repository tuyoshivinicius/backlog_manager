"""Caso de uso para alocar desenvolvedores."""
import logging
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Set, Tuple

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
from backlog_manager.domain.services.backlog_sorter import BacklogSorter
from backlog_manager.domain.services.developer_load_balancer import DeveloperLoadBalancer
from backlog_manager.domain.services.idleness_detector import (
    AllocationWarning,
    DeadlockWarning,
    IdlenessDetector,
    IdlenessWarning,
)
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator

logger = logging.getLogger(__name__)

# Constante configurável para limite de iterações
DEFAULT_MAX_ITERATIONS = 1000


@dataclass
class AllocationMetrics:
    """Métricas de performance da alocação de desenvolvedores."""

    total_time_seconds: float = 0.0
    stories_processed: int = 0
    stories_allocated: int = 0
    waves_processed: int = 0
    total_iterations: int = 0
    iterations_per_wave: Dict[int, int] = field(default_factory=dict)
    allocations_by_dependency_owner: int = 0
    allocations_by_load_balancing: int = 0
    deadlocks_detected: int = 0
    date_adjustments: int = 0

    def __str__(self) -> str:
        """Retorna representação legível das métricas."""
        return (
            f"AllocationMetrics("
            f"time={self.total_time_seconds:.2f}s, "
            f"stories={self.stories_allocated}/{self.stories_processed}, "
            f"waves={self.waves_processed}, "
            f"iterations={self.total_iterations}, "
            f"by_dep_owner={self.allocations_by_dependency_owner}, "
            f"by_load_bal={self.allocations_by_load_balancing}, "
            f"deadlocks={self.deadlocks_detected}, "
            f"adjustments={self.date_adjustments})"
        )


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
        backlog_sorter: BacklogSorter,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
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
            backlog_sorter: Serviço de ordenação topológica
            max_iterations: Limite máximo de iterações por onda (padrão: 1000)
        """
        self._story_repository = story_repository
        self._developer_repository = developer_repository
        self._configuration_repository = configuration_repository
        self._load_balancer = load_balancer
        self._idleness_detector = idleness_detector
        self._schedule_calculator = schedule_calculator
        self._backlog_sorter = backlog_sorter
        self._max_iterations = max_iterations

    def execute(self) -> Tuple[int, List[AllocationWarning], AllocationMetrics]:
        """
        Aloca desenvolvedores processando onda por onda.

        **ALGORITMO (Processamento por Onda):**

        1. Valida desenvolvedores (lança exceção se nenhum)
        2. Carrega todas as histórias UMA VEZ (cache em memória)
        3. Agrupa histórias por onda
        4. Para cada onda (em ordem crescente):
           - Aloca histórias da onda usando _allocate_wave()
           - Se deadlock na onda: emite warning e prossegue para próxima
        5. Validação final de dependências
        6. Atualiza schedule_order baseado na ordem final
        7. Salva TODAS as histórias modificadas em batch (única transação)
        8. Detecta ociosidade

        **Vantagens do processamento por onda:**
        - Garante que histórias de ondas anteriores são priorizadas
        - Deadlock em uma onda não bloqueia ondas posteriores
        - Permite rastreamento de progresso por onda
        - Alinhado com estratégia de entrega incremental

        **Otimizações de I/O (Fase 2):**
        - Apenas 1 chamada a find_all() no início
        - Todas as operações usam cache em memória
        - Apenas 1 chamada a save_batch() no final

        Returns:
            Tupla (total_alocado, lista_de_warnings, métricas)

        Raises:
            NoDevelopersAvailableException: Se não há desenvolvedores cadastrados
        """
        # INICIAR COLETA DE MÉTRICAS
        start_time = time.perf_counter()
        self._metrics = AllocationMetrics()

        logger.info("Iniciando alocação de desenvolvedores (processamento por onda)")

        # 1. VALIDAÇÕES
        developers = self._developer_repository.find_all()
        if not developers:
            raise NoDevelopersAvailableException("Nenhum desenvolvedor disponível para alocação")

        logger.info(f"Encontrados {len(developers)} desenvolvedores disponíveis")

        config = self._configuration_repository.get()

        # Armazenar critério de alocação e max_idle_days para uso durante o algoritmo
        self._allocation_criteria = config.allocation_criteria
        self._max_idle_days = config.max_idle_days
        logger.info(
            f"Critério de alocação configurado: {self._allocation_criteria.value}, "
            f"max_idle_days: {self._max_idle_days}"
        )

        # 2. PREPARAR: buscar todas histórias UMA ÚNICA VEZ (cache em memória)
        all_stories = self._story_repository.find_all()

        # Carregar features para acessar waves
        for story in all_stories:
            self._story_repository.load_feature(story)

        # Criar mapa para busca O(1) de histórias por ID
        self._story_map: Dict[str, Story] = {story.id: story for story in all_stories}

        # Set para rastrear histórias modificadas (para save_batch no final)
        self._modified_stories: Set[str] = set()

        # Identificar ondas únicas e ordenar
        waves = sorted(set(s.wave for s in all_stories if s.feature is not None))

        if not waves:
            logger.warning("Nenhuma história com feature definida encontrada")
            self._metrics.total_time_seconds = time.perf_counter() - start_time
            return 0, [], self._metrics

        # Métricas: total de histórias e ondas
        self._metrics.stories_processed = len(all_stories)
        self._metrics.waves_processed = len(waves)

        logger.info(f"Encontradas {len(waves)} ondas para processar: {waves}")

        # 3. CONTEXTO GLOBAL de alocação (compartilhado entre ondas)
        adjusted_stories_global: Set[str] = set()  # Histórias já ajustadas (qualquer onda)
        total_allocated = 0
        all_warnings: List[AllocationWarning] = []

        # 4. PROCESSAR onda por onda
        for wave in waves:
            logger.info(f"Processando onda {wave}")

            # Filtrar histórias desta onda
            wave_stories = [s for s in all_stories if s.wave == wave]

            # Ordenar por prioridade (simples)
            wave_stories.sort(key=lambda s: s.priority)

            logger.info(f"Onda {wave}: {len(wave_stories)} histórias a processar")

            # Alocar histórias desta onda
            allocated, wave_warnings = self._allocate_wave(
                wave=wave,
                wave_stories=wave_stories,
                developers=developers,
                all_stories=all_stories,
                adjusted_stories_global=adjusted_stories_global,
                config=config,
            )

            total_allocated += allocated
            all_warnings.extend(wave_warnings)

            logger.info(f"Onda {wave} concluída: {allocated} histórias alocadas")

        # 5. VALIDAÇÃO FINAL: Re-verificar e ajustar dependências (usa cache em memória)
        logger.info("Validação final: verificando dependências")
        violations_fixed = self._final_dependency_check(all_stories, config)
        if violations_fixed > 0:
            logger.info(f"Validação final: {violations_fixed} histórias ajustadas para respeitar dependências")

        # 5.5 RESOLVER CONFLITOS DE ALOCAÇÃO (proteção adicional)
        # Detecta e resolve histórias do mesmo desenvolvedor com períodos sobrepostos.
        # Esta é uma camada defensiva que garante consistência mesmo se algum bug
        # anterior criar conflitos.
        logger.info("Validação final: resolvendo conflitos de alocação")
        conflicts_resolved = self._resolve_allocation_conflicts(all_stories, developers)
        if conflicts_resolved > 0:
            logger.warning(
                f"Validação final: {conflicts_resolved} conflitos de alocação resolvidos"
            )

        # 6. ATUALIZAR schedule_order baseado na ordem final (antes de salvar)
        self._update_schedule_order_in_memory(all_stories)

        # 7. SALVAR todas as histórias modificadas em batch (única transação)
        stories_to_save = [s for s in all_stories if s.id in self._modified_stories]
        if stories_to_save:
            logger.info(f"Salvando {len(stories_to_save)} histórias modificadas em batch")
            self._story_repository.save_batch(stories_to_save)

        # 8. DETECTAR OCIOSIDADE após todas as alocações (usa cache em memória)
        logger.info("Detectando períodos de ociosidade")

        # 8.1 Ociosidade DENTRO das ondas (limitada por max_idle_days)
        within_wave_warnings = self._idleness_detector.detect_idleness(all_stories)
        all_warnings.extend(within_wave_warnings)
        logger.debug(f"Ociosidade dentro das ondas: {len(within_wave_warnings)} warnings")

        # 8.2 Ociosidade ENTRE ondas (permitida, apenas informativo)
        between_waves_infos = self._idleness_detector.detect_between_waves_idleness(all_stories)
        all_warnings.extend(between_waves_infos)
        logger.debug(f"Ociosidade entre ondas: {len(between_waves_infos)} infos")

        # FINALIZAR MÉTRICAS
        self._metrics.total_time_seconds = time.perf_counter() - start_time
        self._metrics.stories_allocated = total_allocated

        # Logar métricas de performance
        logger.info(
            f"Alocação concluída: {total_allocated} histórias alocadas, "
            f"{len(all_warnings)} warnings detectados"
        )
        logger.info(f"Métricas de performance: {self._metrics}")

        return total_allocated, all_warnings, self._metrics

    def _allocate_wave(
        self,
        wave: int,
        wave_stories: List[Story],
        developers: List[Developer],
        all_stories: List[Story],
        adjusted_stories_global: Set[str],
        config: Configuration,
    ) -> Tuple[int, List[AllocationWarning]]:
        """
        Aloca desenvolvedores para histórias de uma onda específica.

        Implementa algoritmo de alocação com ajuste de datas quando necessário.
        Se encontrar deadlock (nenhum progresso possível), emite warning e retorna.

        Args:
            wave: Número da onda sendo processada
            wave_stories: Histórias desta onda (ordenadas por priority)
            developers: Lista de todos os desenvolvedores
            all_stories: Lista de todas as histórias (para verificar conflitos)
            adjusted_stories_global: Set de IDs de histórias já ajustadas (compartilhado)
            config: Configuração do sistema

        Returns:
            Tupla (histórias_alocadas, lista_de_warnings)
        """
        logger.debug(f"_allocate_wave: Iniciando alocação para onda {wave}")

        allocated_count = 0
        warnings: List[AllocationWarning] = []
        wave_iterations = 0

        # Contexto local da onda (flags de ajuste)
        adjusted_stories_last_iteration: Set[str] = set()

        # Loop principal de alocação (semelhante ao algoritmo original)
        for iteration in range(self._max_iterations):
            wave_iterations += 1
            adjusted_stories_this_iteration: Set[str] = set()

            # Listar histórias não alocadas DESTA ONDA
            unallocated_stories = self._get_unallocated_stories_from_list(wave_stories)

            if not unallocated_stories:
                logger.debug(f"Onda {wave}: Todas as histórias foram alocadas")
                break  # Todas desta onda foram alocadas

            # Flag para detectar se houve progresso nesta iteração
            allocation_made = False

            # Verificar se há histórias que NÃO foram ajustadas na última iteração
            stories_not_adjusted_last = [
                s for s in unallocated_stories if s.id not in adjusted_stories_last_iteration
            ]
            has_unadjusted_stories = len(stories_not_adjusted_last) > 0

            # Iterar sobre cada história
            for story in unallocated_stories:
                # IMPORTANTE: Antes de buscar devs, garantir que história respeita dependências
                # Ajustar start_date se necessário para aguardar dependências terminarem
                deps_adjusted = self._ensure_dependencies_finished(story, all_stories, config)
                if deps_adjusted:
                    logger.debug(f"História {story.id}: data ajustada para aguardar dependências")
                    self._modified_stories.add(story.id)  # Marcar como modificada

                # Verificar disponibilidade de desenvolvedores
                available_devs = self._get_available_developers(
                    story.start_date,  # type: ignore
                    story.end_date,  # type: ignore
                    all_stories,
                    developers,
                )

                if available_devs:
                    # HÁ DEV DISPONÍVEL - ALOCAR
                    # Verificar se há "dono" de dependência (para métricas)
                    dependency_owner = self._load_balancer.get_dependency_owner(
                        story, self._story_map, available_devs
                    )

                    # Usa get_developer_for_story que considera:
                    # - Critério de alocação (LOAD_BALANCING ou DEPENDENCY_OWNER)
                    # - Limite de ociosidade (max_idle_days) DENTRO DA MESMA ONDA
                    selected_dev = self._load_balancer.get_developer_for_story(
                        story,
                        self._story_map,
                        available_devs,
                        all_stories,
                        allocation_criteria=self._allocation_criteria,
                        new_story_start_date=story.start_date,
                        max_idle_days=self._max_idle_days,
                        current_wave=wave,  # Ociosidade só é verificada na mesma onda
                    )

                    if selected_dev is None:
                        # Fallback para o primeiro disponível (não deveria acontecer)
                        selected_dev = available_devs[0]

                    story.allocate_developer(selected_dev.id)
                    self._modified_stories.add(story.id)  # Marcar como modificada

                    allocated_count += 1
                    allocation_made = True

                    # Métricas: rastrear tipo de alocação
                    if dependency_owner and selected_dev.id == dependency_owner.id:
                        self._metrics.allocations_by_dependency_owner += 1
                    else:
                        self._metrics.allocations_by_load_balancing += 1

                    logger.debug(
                        f"História {story.id} (wave={wave}) alocada para desenvolvedor {selected_dev.name}"
                    )

                    # Reiniciar loop (buscar lista atualizada)
                    break

                else:
                    # NÃO HÁ DEV - AJUSTAR DATAS
                    already_adjusted_ever = story.id in adjusted_stories_global

                    if already_adjusted_ever:
                        # Já foi ajustada alguma vez
                        adjusted_last_iteration = story.id in adjusted_stories_last_iteration

                        if adjusted_last_iteration and has_unadjusted_stories:
                            # Pular para dar prioridade às outras
                            continue
                        else:
                            # Ajustar novamente
                            self._adjust_story_dates(story, 1, config)
                            adjusted_stories_global.add(story.id)
                            adjusted_stories_this_iteration.add(story.id)
                            self._modified_stories.add(story.id)  # Marcar como modificada
                            self._metrics.date_adjustments += 1  # Métrica
                            logger.debug(f"História {story.id} (wave={wave}): data ajustada +1 dia")
                    else:
                        # Nunca foi ajustada: ajustar pela primeira vez
                        self._adjust_story_dates(story, 1, config)
                        adjusted_stories_global.add(story.id)
                        adjusted_stories_this_iteration.add(story.id)
                        self._modified_stories.add(story.id)  # Marcar como modificada
                        self._metrics.date_adjustments += 1  # Métrica
                        logger.debug(f"História {story.id} (wave={wave}): data ajustada +1 dia")

            # Atualizar flag "última iteração" para próxima rodada
            adjusted_stories_last_iteration = adjusted_stories_this_iteration.copy()

            # DETECÇÃO DE DEADLOCK (nenhum progresso nesta iteração)
            deadlock_warning = self._detect_deadlock(
                wave, allocation_made, adjusted_stories_this_iteration, unallocated_stories
            )
            if deadlock_warning:
                warnings.append(deadlock_warning)
                self._metrics.deadlocks_detected += 1
                break  # Sair do loop e prosseguir para próxima onda

        # Atualizar métricas de iterações
        self._metrics.iterations_per_wave[wave] = wave_iterations
        self._metrics.total_iterations += wave_iterations

        return allocated_count, warnings

    def _detect_deadlock(
        self,
        wave: int,
        allocation_made: bool,
        adjusted_this_iteration: Set[str],
        unallocated_stories: List[Story],
    ) -> Optional[DeadlockWarning]:
        """
        Detecta situação de deadlock e retorna warning se detectado.

        Um deadlock ocorre quando:
        1. Nenhuma alocação foi feita nesta iteração E
        2. Nenhuma história teve sua data ajustada

        Isso significa que o algoritmo não pode fazer mais progresso:
        - Todas as histórias não alocadas já foram ajustadas
        - Nenhum desenvolvedor está disponível nos períodos atuais
        - O algoritmo ficaria em loop infinito sem esta detecção

        Args:
            wave: Número da onda sendo processada
            allocation_made: True se alguma alocação foi feita nesta iteração
            adjusted_this_iteration: Set de IDs de histórias ajustadas nesta iteração
            unallocated_stories: Lista de histórias não alocadas

        Returns:
            DeadlockWarning se deadlock detectado, None caso contrário
        """
        # Condição de deadlock: sem progresso (sem alocação E sem ajuste)
        if allocation_made or len(adjusted_this_iteration) > 0:
            return None

        # Deadlock detectado
        logger.warning(
            f"Deadlock detectado na onda {wave}: nenhuma história pode ser alocada. "
            f"Prosseguindo para próxima onda."
        )

        return DeadlockWarning(
            wave=wave,
            unallocated_story_ids=[s.id for s in unallocated_stories],
            message=f"{len(unallocated_stories)} histórias não puderam ser alocadas",
        )

    def _update_schedule_order_in_memory(self, all_stories: List[Story]) -> None:
        """
        Atualiza schedule_order de todas as histórias baseado na ordem atual (priority).

        Este método sincroniza schedule_order com a ordem visual da tabela (ordenada por priority),
        permitindo que mudanças manuais de prioridade sejam refletidas na alocação.

        Opera em memória - as histórias são marcadas como modificadas para
        serem salvas em batch posteriormente.

        Args:
            all_stories: Lista de todas as histórias (será ordenada por priority)
        """
        # Ordenar por priority para definir schedule_order
        sorted_stories = sorted(all_stories, key=lambda s: s.priority)

        # Atualizar schedule_order = índice na ordem atual
        for index, story in enumerate(sorted_stories):
            if story.schedule_order != index:
                story.schedule_order = index
                self._modified_stories.add(story.id)

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

    def _get_unallocated_stories_from_list(self, stories: List[Story]) -> List[Story]:
        """
        Retorna histórias elegíveis para alocação de uma lista específica.

        Similar a _get_unallocated_stories(), mas opera em uma lista passada
        (usado para filtrar histórias de uma onda específica).

        Elegível se:
        - Não tem desenvolvedor
        - Tem datas definidas
        - Tem story point definido

        Já assume que a lista está ordenada corretamente.

        Args:
            stories: Lista de histórias para filtrar

        Returns:
            Lista filtrada de histórias elegíveis (mantém ordem original)
        """
        return [
            s
            for s in stories
            if s.developer_id is None
            and s.start_date is not None
            and s.end_date is not None
            and s.story_point is not None
        ]

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

    def _calculate_new_end_date(self, story: Story, new_start: date) -> Optional[date]:
        """
        Calcula a nova data de fim da história baseada na nova data de início.

        Mantém a duração original da história. Se a história tem `duration`,
        usa esse valor. Senão, calcula a duração original em dias úteis.

        Args:
            story: História para calcular nova data de fim
            new_start: Nova data de início

        Returns:
            Nova data de fim, ou None se não for possível calcular
        """
        if story.duration:
            # Duration - 1 porque add_workdays usa offset semantics
            return self._schedule_calculator.add_workdays(new_start, story.duration - 1)
        elif story.start_date and story.end_date:
            # Calcular duração original em dias úteis
            workdays = self._schedule_calculator.count_workdays(story.start_date, story.end_date)
            return self._schedule_calculator.add_workdays(new_start, max(0, workdays - 1))
        else:
            return None

    def _update_story_dates(self, story: Story, new_start: date) -> bool:
        """
        Atualiza as datas de início e fim da história in-place.

        Calcula a nova data de fim mantendo a duração original.

        Args:
            story: História a atualizar
            new_start: Nova data de início

        Returns:
            True se as datas foram atualizadas, False se não foi possível
        """
        new_end = self._calculate_new_end_date(story, new_start)
        if new_end is None:
            return False

        story.start_date = new_start
        story.end_date = new_end
        return True

    def _adjust_story_dates(self, story: Story, days_to_add: int, config: Configuration) -> None:
        """
        Ajusta datas da história adicionando dias ÚTEIS.

        Usa o ScheduleCalculator para adicionar dias úteis corretamente
        (considerando apenas segunda a sexta e feriados).

        Args:
            story: História a ajustar
            days_to_add: Número de dias úteis a adicionar
            config: Configuração (não usado atualmente)
        """
        if story.start_date is None:
            return

        # Calcular nova data de início
        new_start = self._schedule_calculator.add_workdays(story.start_date, days_to_add)

        # Atualizar datas mantendo duração
        self._update_story_dates(story, new_start)

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

    def _get_dependency_stories(self, story: Story) -> List[Story]:
        """
        Retorna lista de histórias que são dependências da história fornecida.

        Usa o mapa `_story_map` para busca O(1) em vez de busca linear.

        Args:
            story: História para buscar dependências

        Returns:
            Lista de Stories que são pré-requisitos (pode estar vazia)
        """
        dependencies = []
        for dep_id in story.dependencies:
            dep_story = self._story_map.get(dep_id)
            if dep_story:
                dependencies.append(dep_story)
            else:
                logger.warning(f"Dependência {dep_id} não encontrada para história {story.id}")
        return dependencies

    def _get_latest_dependency_end_date(self, story: Story) -> Optional[date]:
        """
        Retorna a data de término mais tardia entre todas as dependências.

        Args:
            story: História para verificar dependências

        Returns:
            Data de término mais tardia ou None se não há dependências com datas
        """
        latest_end = None
        for dep_story in self._get_dependency_stories(story):
            if dep_story.end_date:
                if latest_end is None or dep_story.end_date > latest_end:
                    latest_end = dep_story.end_date
        return latest_end

    def _ensure_dependencies_finished(
        self, story: Story, all_stories: List[Story], config: Configuration
    ) -> bool:
        """
        Garante que a história só inicia após todas as dependências terminarem.

        Se alguma dependência termina DEPOIS da data de início da história,
        ajusta a data de início para o dia útil SEGUINTE ao fim da última dependência.

        Args:
            story: História a verificar
            all_stories: Lista de todas as histórias (para buscar dependências)
            config: Configuração do sistema

        Returns:
            True se as datas foram ajustadas, False caso contrário
        """
        if not story.dependencies or not story.start_date:
            return False

        # Buscar a data de término mais tarde entre todas as dependências (O(1) lookup)
        latest_dep_end = self._get_latest_dependency_end_date(story)

        # Se não há dependências com datas, não precisa ajustar
        if latest_dep_end is None:
            return False

        # Se a história já inicia após a última dependência, está OK
        if story.start_date > latest_dep_end:
            return False

        # AJUSTAR: História deve iniciar no dia útil SEGUINTE ao fim da última dependência
        old_start = story.start_date
        new_start = self._schedule_calculator.add_workdays(latest_dep_end, 1)

        # Atualizar datas usando método reutilizável
        if not self._update_story_dates(story, new_start):
            return False

        logger.info(
            f"História {story.id}: ajustada de {old_start} para {new_start} "
            f"(última dependência termina em {latest_dep_end})"
        )

        return True

    def _final_dependency_check(
        self, all_stories: List[Story], config: Configuration
    ) -> int:
        """
        Faz uma verificação final de todas as dependências e ajusta datas se necessário.

        Este método é executado após todas as ondas serem processadas para garantir
        que nenhuma violação de dependência passou despercebida durante a alocação.

        Processa histórias em ordem topológica para garantir que dependências sejam
        ajustadas antes de seus dependentes.

        IMPORTANTE: Histórias já alocadas são PULADAS para evitar criar conflitos
        de período com outras histórias do mesmo desenvolvedor. Ajustar datas de
        histórias alocadas pode mover a história para um período onde o desenvolvedor
        já está ocupado.

        Args:
            all_stories: Lista de todas as histórias
            config: Configuração do sistema

        Returns:
            Número de histórias que tiveram suas datas ajustadas
        """
        # Ordenar histórias topologicamente (dependências primeiro)
        sorted_stories = self._backlog_sorter.sort(all_stories)

        violations_fixed = 0

        for story in sorted_stories:
            # IMPORTANTE: Pular histórias já alocadas para evitar criar conflitos
            # de período. Se uma história alocada tiver sua data ajustada, ela pode
            # passar a sobrepor com outra história do mesmo desenvolvedor.
            if story.developer_id is not None:
                logger.debug(
                    f"História {story.id}: pulando _final_dependency_check (já alocada para dev {story.developer_id})"
                )
                continue

            if not story.start_date or not story.dependencies:
                continue

            # Buscar data de término mais tarde entre dependências (O(1) lookup)
            latest_dep_end = self._get_latest_dependency_end_date(story)

            # Se não há dependências com datas, pular
            if latest_dep_end is None:
                continue

            # Verificar se há violação (história inicia antes ou no mesmo dia que dependência termina)
            if story.start_date <= latest_dep_end:
                # VIOLAÇÃO DETECTADA - Ajustar
                old_start = story.start_date
                new_start = self._schedule_calculator.add_workdays(latest_dep_end, 1)

                # Atualizar datas usando método reutilizável
                if not self._update_story_dates(story, new_start):
                    continue

                self._modified_stories.add(story.id)  # Marcar como modificada
                violations_fixed += 1

                logger.info(
                    f"Violação corrigida: {story.id} ajustada de {old_start} para {new_start} "
                    f"(dependência termina em {latest_dep_end})"
                )

        return violations_fixed

    def _resolve_allocation_conflicts(
        self,
        all_stories: List[Story],
        developers: List[Developer],
    ) -> int:
        """
        Detecta e resolve conflitos de alocação (períodos sobrepostos).

        Executa após _final_dependency_check como camada adicional de proteção.
        Para cada desenvolvedor, verifica se há histórias com períodos sobrepostos
        e ajusta as datas da história posterior para começar após a anterior.

        Este método é uma proteção defensiva para garantir que não existam
        conflitos de período, independentemente de como foram criados.

        Args:
            all_stories: Lista de todas as histórias
            developers: Lista de todos os desenvolvedores

        Returns:
            Número de conflitos resolvidos
        """
        conflicts_resolved = 0
        max_passes = 100  # Limite de segurança para evitar loop infinito

        for pass_num in range(max_passes):
            conflict_found_in_pass = False

            for dev in developers:
                # Buscar histórias alocadas para este desenvolvedor
                dev_stories = [
                    s for s in all_stories
                    if s.developer_id == dev.id
                    and s.start_date is not None
                    and s.end_date is not None
                ]

                if len(dev_stories) < 2:
                    continue

                # Ordenar por data de início
                dev_stories.sort(key=lambda s: (s.start_date, s.id))  # type: ignore

                # Verificar sobreposições entre histórias consecutivas
                for i in range(len(dev_stories) - 1):
                    current = dev_stories[i]
                    next_story = dev_stories[i + 1]

                    if self._periods_overlap(
                        current.start_date,  # type: ignore
                        current.end_date,  # type: ignore
                        next_story.start_date,  # type: ignore
                        next_story.end_date,  # type: ignore
                    ):
                        # CONFLITO DETECTADO!
                        # Ajustar next_story para começar após current terminar
                        old_start = next_story.start_date
                        new_start = self._schedule_calculator.add_workdays(
                            current.end_date, 1  # type: ignore
                        )

                        if self._update_story_dates(next_story, new_start):
                            self._modified_stories.add(next_story.id)
                            conflicts_resolved += 1
                            conflict_found_in_pass = True

                            logger.warning(
                                f"Conflito de alocação resolvido: {next_story.id} ajustada de "
                                f"{old_start} para {new_start} (sobrepunha com {current.id} "
                                f"do dev {dev.name})"
                            )

            # Se não encontrou conflitos nesta passada, terminamos
            if not conflict_found_in_pass:
                break

        if conflicts_resolved > 0:
            logger.info(
                f"_resolve_allocation_conflicts: {conflicts_resolved} conflitos resolvidos "
                f"em {pass_num + 1} passadas"
            )

        return conflicts_resolved
