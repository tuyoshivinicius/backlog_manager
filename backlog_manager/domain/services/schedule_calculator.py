"""Serviço para cálculo de cronograma de histórias."""
from datetime import date, timedelta
from math import ceil

from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.domain.entities.story import Story

# Feriados nacionais brasileiros (lista fixa)
BRAZILIAN_HOLIDAYS = frozenset(
    [
        date(2025, 1, 1),  # Ano Novo
        date(2025, 4, 21),  # Tiradentes
        date(2025, 5, 1),  # Dia do Trabalho
        date(2025, 9, 7),  # Independência
        date(2025, 10, 12),  # Nossa Senhora Aparecida
        date(2025, 11, 2),  # Finados
        date(2025, 11, 15),  # Proclamação da República
        date(2025, 12, 25),  # Natal
        date(2026, 1, 1),  # Ano Novo
        date(2026, 4, 21),  # Tiradentes
        date(2026, 5, 1),  # Dia do Trabalho
        date(2026, 9, 7),  # Independência
        date(2026, 10, 12),  # Nossa Senhora Aparecida
        date(2026, 11, 2),  # Finados
        date(2026, 11, 15),  # Proclamação da República
        date(2026, 12, 25),  # Natal
    ]
)


class ScheduleCalculator:
    """
    Serviço para calcular cronograma (datas e durações) de histórias.

    Calcula:
    - Duração em dias úteis baseada em Story Points e velocidade
    - Datas de início e fim considerando apenas dias úteis (seg-sex)
    - Sequenciamento: histórias do mesmo dev executam em sequência
    - Barreira de onda: histórias de onda N só iniciam após onda N-1 terminar

    Barreira de Onda (Wave Barrier):
    - Ondas são agrupamentos de histórias por feature.wave
    - Histórias de onda 2 só podem iniciar após TODAS as histórias de onda 1 terminarem
    - Wave 0 (histórias sem feature) não bloqueia outras ondas
    - Suporta ondas não contíguas (ex: 1, 3, 5 sem 2, 4)
    """

    def calculate(
        self, stories: list[Story], config: Configuration, start_date: date | None = None
    ) -> list[Story]:
        """
        Calcula cronograma completo para lista de histórias.

        Args:
            stories: Histórias ordenadas (deve estar em ordem topológica)
            config: Configuração com velocidade do time
            start_date: Data de início do projeto (padrão: hoje)

        Returns:
            Lista de histórias com datas e durações calculadas
        """
        if not stories:
            return []

        if start_date is None:
            start_date = date.today()

        # Garantir que start_date seja um dia útil
        start_date = self._ensure_workday(start_date)

        # Rastrear última data de fim por desenvolvedor
        dev_last_end_date: dict[str, date] = {}

        # Rastrear última data de fim por onda (wave barrier)
        wave_last_end_date: dict[int, date] = {}

        # Mapear histórias por ID para consulta rápida
        story_map: dict[str, Story] = {s.id: s for s in stories}

        # Processar cada história
        for story in stories:
            # Calcular duração em dias úteis baseada em SP e velocidade
            story.duration = self._calculate_duration(story.story_point.value, config)

            # Determinar data de início considerando:
            # 1. Última história do desenvolvedor (se houver)
            # 2. Dependências (histórias das quais esta depende)

            earliest_start = start_date

            # Verificar barreira de onda (wave barrier)
            # Histórias de onda N só podem iniciar após todas as histórias
            # de ondas anteriores (1 a N-1) terminarem. Wave 0 não bloqueia.
            current_wave = story.wave
            if current_wave > 0:
                # Buscar ondas anteriores (excluindo wave 0)
                prev_waves = [w for w in wave_last_end_date.keys() if 0 < w < current_wave]
                if prev_waves:
                    prev_wave = max(prev_waves)
                    wave_barrier = self._next_workday(wave_last_end_date[prev_wave])
                    earliest_start = max(earliest_start, wave_barrier)

            # Verificar última história do desenvolvedor
            if story.developer_id and story.developer_id in dev_last_end_date:
                earliest_start = max(
                    earliest_start, self._next_workday(dev_last_end_date[story.developer_id])
                )

            # Verificar dependências - história só pode começar
            # após TODAS as dependências terminarem
            if story.dependencies:
                for dep_id in story.dependencies:
                    # Buscar história da qual depende
                    dep_story = story_map.get(dep_id)
                    if dep_story and dep_story.end_date:
                        # Começar no próximo dia útil após a dependência terminar
                        dep_next_day = self._next_workday(dep_story.end_date)
                        earliest_start = max(earliest_start, dep_next_day)

            # Garantir que earliest_start seja um dia útil
            earliest_start = self._ensure_workday(earliest_start)

            story.start_date = earliest_start

            # Calcular data de fim (start_date + duration - 1 em dias úteis)
            # Duration de 1 dia: end_date = start_date (mesmo dia)
            # Duration de 4 dias: end_date = start_date + 3 dias úteis
            story.end_date = self.add_workdays(story.start_date, story.duration - 1)

            # Atualizar última data de fim do desenvolvedor
            if story.developer_id:
                dev_last_end_date[story.developer_id] = story.end_date

            # Atualizar última data de fim da onda
            if current_wave not in wave_last_end_date or story.end_date > wave_last_end_date[current_wave]:
                wave_last_end_date[current_wave] = story.end_date

        return stories

    def _calculate_duration(self, story_points: int, config: Configuration) -> int:
        """
        Calcula duração em dias úteis baseada em story points.

        Fórmula: ceil(story_points / velocity_per_day)

        Args:
            story_points: Pontos da história
            config: Configuração com velocidade

        Returns:
            Duração em dias úteis
        """
        velocity_per_day = config.velocity_per_day
        duration = ceil(story_points / velocity_per_day)
        return max(1, duration)  # Mínimo 1 dia

    def add_workdays(self, start: date, workdays: int) -> date:
        """
        Adiciona dias úteis a uma data.

        Considera apenas segunda a sexta como dias úteis, excluindo feriados.

        Args:
            start: Data inicial
            workdays: Número de dias úteis a adicionar

        Returns:
            Data final após adicionar dias úteis
        """
        if workdays == 0:
            return start

        current = start
        days_added = 0

        while days_added < workdays:
            current = current + timedelta(days=1)
            if self._is_workday(current):  # Segunda a Sexta E não feriado
                days_added += 1

        return current

    def _is_workday(self, date_to_check: date) -> bool:
        """
        Verifica se a data é um dia útil.

        Dia útil = segunda a sexta E não é feriado nacional.

        Args:
            date_to_check: Data a verificar

        Returns:
            True se é dia útil
        """
        return date_to_check.weekday() < 5 and date_to_check not in BRAZILIAN_HOLIDAYS

    def _ensure_workday(self, date_to_check: date) -> date:
        """
        Garante que a data seja um dia útil.

        Se a data for fim de semana ou feriado, avança para o próximo dia útil.

        Args:
            date_to_check: Data a verificar

        Returns:
            Data que é dia útil (segunda a sexta, não feriado)
        """
        while not self._is_workday(date_to_check):
            date_to_check = date_to_check + timedelta(days=1)

        return date_to_check

    def _next_workday(self, after_date: date) -> date:
        """
        Retorna o próximo dia útil após uma data.

        Args:
            after_date: Data de referência

        Returns:
            Próximo dia útil (não fim de semana, não feriado)
        """
        next_day = after_date + timedelta(days=1)

        # Se cair no fim de semana ou feriado, avançar para próximo dia útil
        while not self._is_workday(next_day):
            next_day = next_day + timedelta(days=1)

        return next_day

    def is_workday(self, date_to_check: date) -> bool:
        """
        Verifica se a data é um dia útil (método público).

        Dia útil = segunda a sexta E não é feriado nacional brasileiro.

        Args:
            date_to_check: Data a verificar

        Returns:
            True se é dia útil
        """
        return self._is_workday(date_to_check)

    def count_workdays(self, start: date, end: date) -> int:
        """
        Conta o número de dias úteis entre duas datas (inclusivo).

        Considera apenas segunda a sexta, excluindo feriados nacionais brasileiros.

        Args:
            start: Data inicial (inclusiva)
            end: Data final (inclusiva)

        Returns:
            Número de dias úteis no intervalo
        """
        if start > end:
            return 0

        current = start
        count = 0

        while current <= end:
            if self._is_workday(current):
                count += 1
            current = current + timedelta(days=1)

        return count

    def count_workdays_between(self, start: date, end: date) -> int:
        """
        Conta o número de dias úteis ENTRE duas datas (exclusivo).

        Útil para calcular gaps de ociosidade entre histórias.
        Não inclui nem start nem end no cálculo.

        Args:
            start: Data inicial (exclusiva - dia seguinte conta)
            end: Data final (exclusiva - dia anterior conta)

        Returns:
            Número de dias úteis entre as datas
        """
        if end <= start:
            return 0

        # Contar de start+1 até end-1
        current = start + timedelta(days=1)
        count = 0

        while current < end:
            if self._is_workday(current):
                count += 1
            current = current + timedelta(days=1)

        return count
