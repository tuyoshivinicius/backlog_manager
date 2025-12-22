"""Serviço para cálculo de cronograma de histórias."""
from datetime import date, timedelta
from math import ceil

from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.domain.entities.story import Story


class ScheduleCalculator:
    """
    Serviço para calcular cronograma (datas e durações) de histórias.

    Calcula:
    - Duração em dias úteis baseada em Story Points e velocidade
    - Datas de início e fim considerando apenas dias úteis (seg-sex)
    - Sequenciamento: histórias do mesmo dev executam em sequência
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

        # Rastrear última data de fim por desenvolvedor
        dev_last_end_date: dict[str, date] = {}

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

            story.start_date = earliest_start

            # Calcular data de fim (start_date + duration - 1 em dias úteis)
            # Duration de 1 dia: end_date = start_date (mesmo dia)
            # Duration de 4 dias: end_date = start_date + 3 dias úteis
            story.end_date = self.add_workdays(story.start_date, story.duration - 1)

            # Atualizar última data de fim do desenvolvedor
            if story.developer_id:
                dev_last_end_date[story.developer_id] = story.end_date

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

        Considera apenas segunda a sexta como dias úteis.

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
            # 0 = Segunda, 6 = Domingo
            if current.weekday() < 5:  # Segunda a Sexta
                days_added += 1

        return current

    def _next_workday(self, after_date: date) -> date:
        """
        Retorna o próximo dia útil após uma data.

        Args:
            after_date: Data de referência

        Returns:
            Próximo dia útil
        """
        next_day = after_date + timedelta(days=1)

        # Se cair no fim de semana, avançar para segunda
        while next_day.weekday() >= 5:  # Sábado ou Domingo
            next_day = next_day + timedelta(days=1)

        return next_day
