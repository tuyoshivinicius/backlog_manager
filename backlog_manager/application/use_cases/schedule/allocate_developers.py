"""Caso de uso para alocar desenvolvedores."""
import logging
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
from backlog_manager.domain.services.backlog_sorter import BacklogSorter
from backlog_manager.domain.services.developer_load_balancer import DeveloperLoadBalancer
from backlog_manager.domain.services.idleness_detector import IdlenessDetector, IdlenessWarning
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator

logger = logging.getLogger(__name__)


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
        """
        self._story_repository = story_repository
        self._developer_repository = developer_repository
        self._configuration_repository = configuration_repository
        self._load_balancer = load_balancer
        self._idleness_detector = idleness_detector
        self._schedule_calculator = schedule_calculator
        self._backlog_sorter = backlog_sorter

    def execute(self) -> Tuple[int, List[IdlenessWarning]]:
        """
        Aloca desenvolvedores processando onda por onda.

        **ALGORITMO (Processamento por Onda):**

        0. Atualiza schedule_order baseado na ordem atual da tabela (priority)
        1. Valida desenvolvedores (lança exceção se nenhum)
        2. Agrupa histórias por onda
        3. Para cada onda (em ordem crescente):
           - Aloca histórias da onda usando _allocate_wave()
           - Se deadlock na onda: emite warning e prossegue para próxima
        4. Detecta ociosidade após todas as alocações

        **Vantagens do processamento por onda:**
        - Garante que histórias de ondas anteriores são priorizadas
        - Deadlock em uma onda não bloqueia ondas posteriores
        - Permite rastreamento de progresso por onda
        - Alinhado com estratégia de entrega incremental

        Returns:
            Tupla (total_alocado, lista_de_warnings)

        Raises:
            NoDevelopersAvailableException: Se não há desenvolvedores cadastrados
        """
        logger.info("Iniciando alocação de desenvolvedores (processamento por onda)")

        # 0. SINCRONIZAR schedule_order com ordem ATUAL da tabela
        self._update_schedule_order_from_table()

        # 1. VALIDAÇÕES
        developers = self._developer_repository.find_all()
        if not developers:
            raise NoDevelopersAvailableException("Nenhum desenvolvedor disponível para alocação")

        logger.info(f"Encontrados {len(developers)} desenvolvedores disponíveis")

        config = self._configuration_repository.get()

        # 2. PREPARAR: buscar todas histórias e agrupar por onda
        all_stories = self._story_repository.find_all()

        # Carregar features para acessar waves
        for story in all_stories:
            self._story_repository.load_feature(story)

        # Identificar ondas únicas e ordenar
        waves = sorted(set(s.wave for s in all_stories if s.feature is not None))

        if not waves:
            logger.warning("Nenhuma história com feature definida encontrada")
            return 0, []

        logger.info(f"Encontradas {len(waves)} ondas para processar: {waves}")

        # 3. CONTEXTO GLOBAL de alocação (compartilhado entre ondas)
        adjusted_stories_global: Set[str] = set()  # Histórias já ajustadas (qualquer onda)
        total_allocated = 0
        all_warnings: List[IdlenessWarning] = []

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

        # 5. VALIDAÇÃO FINAL: Re-verificar e ajustar dependências
        logger.info("Validação final: verificando dependências")
        all_stories = self._story_repository.find_all()
        for story in all_stories:
            self._story_repository.load_feature(story)

        violations_fixed = self._final_dependency_check(all_stories, config)
        if violations_fixed > 0:
            logger.info(f"Validação final: {violations_fixed} histórias ajustadas para respeitar dependências")

        # 6. DETECTAR OCIOSIDADE após todas as alocações
        logger.info("Detectando períodos de ociosidade")
        all_stories = self._story_repository.find_all()
        idleness_warnings = self._idleness_detector.detect_idleness(all_stories)
        all_warnings.extend(idleness_warnings)

        logger.info(
            f"Alocação concluída: {total_allocated} histórias alocadas, "
            f"{len(all_warnings)} warnings detectados"
        )

        return total_allocated, all_warnings

    def _allocate_wave(
        self,
        wave: int,
        wave_stories: List[Story],
        developers: List[Developer],
        all_stories: List[Story],
        adjusted_stories_global: Set[str],
        config: Configuration,
    ) -> Tuple[int, List[IdlenessWarning]]:
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
        warnings: List[IdlenessWarning] = []
        max_iterations = 1000

        # Contexto local da onda (flags de ajuste)
        adjusted_stories_last_iteration: Set[str] = set()

        # Loop principal de alocação (semelhante ao algoritmo original)
        for iteration in range(max_iterations):
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
                    self._story_repository.save(story)

                # Verificar disponibilidade de desenvolvedores
                available_devs = self._get_available_developers(
                    story.start_date,  # type: ignore
                    story.end_date,  # type: ignore
                    all_stories,
                    developers,
                )

                if available_devs:
                    # HÁ DEV DISPONÍVEL - ALOCAR
                    sorted_devs = self._load_balancer.sort_by_load_random_tiebreak(
                        available_devs, all_stories
                    )

                    selected_dev = sorted_devs[0]
                    story.allocate_developer(selected_dev.id)
                    self._story_repository.save(story)

                    allocated_count += 1
                    allocation_made = True

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
                            self._story_repository.save(story)
                            logger.debug(f"História {story.id} (wave={wave}): data ajustada +1 dia")
                    else:
                        # Nunca foi ajustada: ajustar pela primeira vez
                        self._adjust_story_dates(story, 1, config)
                        adjusted_stories_global.add(story.id)
                        adjusted_stories_this_iteration.add(story.id)
                        self._story_repository.save(story)
                        logger.debug(f"História {story.id} (wave={wave}): data ajustada +1 dia")

            # Atualizar flag "última iteração" para próxima rodada
            adjusted_stories_last_iteration = adjusted_stories_this_iteration.copy()

            # DETECÇÃO DE DEADLOCK (nenhum progresso nesta iteração)
            if not allocation_made and len(adjusted_stories_this_iteration) == 0:
                # Deadlock: nenhuma alocação e nenhum ajuste
                logger.warning(
                    f"Deadlock detectado na onda {wave}: nenhuma história pode ser alocada. "
                    f"Prosseguindo para próxima onda."
                )
                # Criar warning de deadlock
                deadlock_warning = IdlenessWarning(
                    developer_name=f"Onda {wave}",
                    idle_period_start=None,  # type: ignore
                    idle_period_end=None,  # type: ignore
                    idle_days=0,
                    message=f"Deadlock na onda {wave}: {len(unallocated_stories)} histórias não puderam ser alocadas",
                )
                warnings.append(deadlock_warning)
                break  # Sair do loop e prosseguir para próxima onda

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

        # Buscar a data de término mais tarde entre todas as dependências
        latest_dep_end = None

        for dep_id in story.dependencies:
            # Buscar dependência na lista
            dep_story = next((s for s in all_stories if s.id == dep_id), None)

            if dep_story and dep_story.end_date:
                if latest_dep_end is None or dep_story.end_date > latest_dep_end:
                    latest_dep_end = dep_story.end_date

        # Se não há dependências com datas, não precisa ajustar
        if latest_dep_end is None:
            return False

        # Se a história já inicia após a última dependência, está OK
        if story.start_date > latest_dep_end:
            return False

        # AJUSTAR: História deve iniciar no dia útil SEGUINTE ao fim da última dependência
        # Adicionar 1 dia útil ao fim da dependência
        new_start = self._schedule_calculator.add_workdays(latest_dep_end, 1)

        # Calcular nova data de fim mantendo a duração
        if story.duration:
            new_end = self._schedule_calculator.add_workdays(new_start, story.duration - 1)
        else:
            # Manter o intervalo original
            if story.end_date:
                workdays = self._count_workdays(story.start_date, story.end_date)
                new_end = self._schedule_calculator.add_workdays(new_start, max(0, workdays - 1))
            else:
                return False

        # Atualizar datas
        old_start = story.start_date
        story.start_date = new_start
        story.end_date = new_end

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
            if not story.start_date or not story.dependencies:
                continue

            # Verificar cada dependência
            latest_dep_end = None

            for dep_id in story.dependencies:
                dep_story = next((s for s in all_stories if s.id == dep_id), None)

                if dep_story and dep_story.end_date:
                    if latest_dep_end is None or dep_story.end_date > latest_dep_end:
                        latest_dep_end = dep_story.end_date

            # Se não há dependências com datas, pular
            if latest_dep_end is None:
                continue

            # Verificar se há violação (história inicia antes ou no mesmo dia que dependência termina)
            if story.start_date <= latest_dep_end:
                # VIOLAÇÃO DETECTADA - Ajustar
                old_start = story.start_date
                new_start = self._schedule_calculator.add_workdays(latest_dep_end, 1)

                # Calcular nova data de fim mantendo a duração
                if story.duration:
                    new_end = self._schedule_calculator.add_workdays(new_start, story.duration - 1)
                else:
                    if story.end_date:
                        workdays = self._count_workdays(story.start_date, story.end_date)
                        new_end = self._schedule_calculator.add_workdays(new_start, max(0, workdays - 1))
                    else:
                        continue

                story.start_date = new_start
                story.end_date = new_end

                self._story_repository.save(story)
                violations_fixed += 1

                logger.info(
                    f"Violação corrigida: {story.id} ajustada de {old_start} para {new_start} "
                    f"(dependência termina em {latest_dep_end})"
                )

        return violations_fixed
