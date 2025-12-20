"""Caso de uso para adicionar dependência."""
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import StoryNotFoundException
from backlog_manager.domain.services.cycle_detector import CycleDetector


class AddDependencyUseCase:
    """
    Caso de uso para adicionar dependência entre histórias.

    Responsabilidades:
    - Validar que ambas histórias existem
    - Simular adição e detectar ciclos
    - Adicionar dependência se válido
    """

    def __init__(self, story_repository: StoryRepository, cycle_detector: CycleDetector):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            cycle_detector: Detector de ciclos
        """
        self._story_repository = story_repository
        self._cycle_detector = cycle_detector

    def execute(self, story_id: str, depends_on_id: str) -> None:
        """
        Adiciona dependência entre histórias.

        Args:
            story_id: ID da história dependente
            depends_on_id: ID da história da qual depende

        Raises:
            StoryNotFoundException: Se alguma história não existe
            CyclicDependencyException: Se criaria ciclo (com caminho)
        """
        # 1. Buscar histórias
        story = self._story_repository.find_by_id(story_id)
        depends_on = self._story_repository.find_by_id(depends_on_id)

        if story is None:
            raise StoryNotFoundException(story_id)

        if depends_on is None:
            raise StoryNotFoundException(depends_on_id)

        # 2. Buscar todas dependências atuais
        all_stories = self._story_repository.find_all()
        dependencies_map = {s.id: s.dependencies.copy() for s in all_stories}

        # 3. Simular adição da nova dependência
        if depends_on_id not in dependencies_map[story_id]:
            dependencies_map[story_id].append(depends_on_id)

        # 4. Detectar ciclo (lança CyclicDependencyException se encontrar)
        if self._cycle_detector.has_cycle(dependencies_map):
            self._cycle_detector.find_cycle_path(dependencies_map)

        # 5. Se válido, adicionar dependência
        story.add_dependency(depends_on_id)
        self._story_repository.save(story)
