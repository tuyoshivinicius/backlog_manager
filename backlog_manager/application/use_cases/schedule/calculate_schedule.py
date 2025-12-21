"""Caso de uso para calcular cronograma completo."""
from datetime import date

from backlog_manager.application.dto.backlog_dto import BacklogDTO
from backlog_manager.application.dto.converters import story_to_dto
from backlog_manager.application.interfaces.repositories.configuration_repository import ConfigurationRepository
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.services.backlog_sorter import BacklogSorter
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator


class CalculateScheduleUseCase:
    """
    Caso de uso para calcular cronograma completo do backlog.

    Responsabilidades:
    - Buscar histórias e configuração
    - Ordenar backlog (dependências + prioridade)
    - Calcular cronograma (datas e durações)
    - Persistir atualizações
    - Retornar backlog ordenado com metadados
    """

    def __init__(
        self,
        story_repository: StoryRepository,
        configuration_repository: ConfigurationRepository,
        backlog_sorter: BacklogSorter,
        schedule_calculator: ScheduleCalculator,
    ):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            configuration_repository: Repositório de configuração
            backlog_sorter: Serviço de ordenação
            schedule_calculator: Serviço de cálculo de cronograma
        """
        self._story_repository = story_repository
        self._configuration_repository = configuration_repository
        self._backlog_sorter = backlog_sorter
        self._schedule_calculator = schedule_calculator

    def execute(self, start_date: date | None = None) -> BacklogDTO:
        """
        Calcula cronograma completo do backlog.

        Args:
            start_date: Data de início do projeto (opcional)
                       Precedência: 1) start_date passado, 2) roadmap_start_date da config, 3) date.today()

        Returns:
            BacklogDTO com histórias ordenadas e cronograma calculado

        Raises:
            CyclicDependencyException: Se houver ciclo nas dependências
        """
        # 1. Buscar dados
        stories = self._story_repository.find_all()
        config = self._configuration_repository.get()

        if not stories:
            return BacklogDTO(stories=[], total_count=0, total_story_points=0, estimated_duration_days=0)

        # 1.1. Limpar todos os desenvolvedores (reset completo)
        for story in stories:
            if story.developer_id:
                story.deallocate_developer()
                self._story_repository.save(story)

        # 2. Ordenar backlog (valida ciclos internamente)
        sorted_stories = self._backlog_sorter.sort(stories)

        # 3. Determinar data de início efetiva
        # Precedência: 1) parâmetro passado, 2) config roadmap_start_date, 3) date.today()
        effective_start_date = start_date or config.roadmap_start_date or date.today()

        # 4. Calcular cronograma (datas e durações)
        scheduled_stories = self._schedule_calculator.calculate(sorted_stories, config, effective_start_date)

        # 5. Atualizar prioridades E schedule_order baseado na ordem
        for index, story in enumerate(scheduled_stories):
            story.priority = index
            story.schedule_order = index  # Sincronizar schedule_order com a ordem calculada
            self._story_repository.save(story)

        # 6. Calcular metadados
        total_sp = sum(s.story_point.value for s in scheduled_stories)

        # Calcular duração total (da primeira história à última)
        if scheduled_stories and scheduled_stories[0].start_date and scheduled_stories[-1].end_date:
            first_start = scheduled_stories[0].start_date
            last_end = scheduled_stories[-1].end_date
            duration_days = (last_end - first_start).days + 1
        else:
            duration_days = 0

        # 7. Retornar BacklogDTO
        return BacklogDTO(
            stories=[story_to_dto(s) for s in scheduled_stories],
            total_count=len(scheduled_stories),
            total_story_points=total_sp,
            estimated_duration_days=duration_days,
        )
