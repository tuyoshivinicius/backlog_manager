"""Caso de uso para alocar desenvolvedores."""
from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository


class NoDevelopersAvailableException(Exception):
    """Lançada quando não há desenvolvedores disponíveis."""

    pass


class AllocateDevelopersUseCase:
    """
    Caso de uso para alocar desenvolvedores em histórias.

    Usa estratégia round-robin para distribuir histórias
    igualmente entre desenvolvedores disponíveis.

    Responsabilidades:
    - Buscar histórias não alocadas
    - Buscar desenvolvedores disponíveis
    - Distribuir usando round-robin
    - Persistir alocações
    """

    def __init__(self, story_repository: StoryRepository, developer_repository: DeveloperRepository):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            developer_repository: Repositório de desenvolvedores
        """
        self._story_repository = story_repository
        self._developer_repository = developer_repository

    def execute(self) -> int:
        """
        Aloca desenvolvedores nas histórias não alocadas.

        Returns:
            Número de histórias alocadas

        Raises:
            NoDevelopersAvailableException: Se não há desenvolvedores
        """
        # 1. Buscar histórias sem desenvolvedor
        all_stories = self._story_repository.find_all()
        unallocated_stories = [s for s in all_stories if s.developer_id is None]

        if not unallocated_stories:
            return 0

        # 2. Buscar desenvolvedores
        developers = self._developer_repository.find_all()

        if not developers:
            raise NoDevelopersAvailableException("Nenhum desenvolvedor disponível para alocação")

        # 3. Distribuir round-robin
        allocated_count = 0

        for index, story in enumerate(unallocated_stories):
            # Selecionar desenvolvedor (round-robin)
            developer_index = index % len(developers)
            developer = developers[developer_index]

            # Alocar
            story.allocate_developer(developer.id)
            self._story_repository.save(story)
            allocated_count += 1

        return allocated_count
