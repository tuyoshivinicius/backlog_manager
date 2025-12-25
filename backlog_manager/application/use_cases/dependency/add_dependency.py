"""Caso de uso para adicionar dependência."""
import logging

from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.domain.exceptions.domain_exceptions import StoryNotFoundException
from backlog_manager.domain.services.cycle_detector import CycleDetector
from backlog_manager.domain.services.wave_dependency_validator import WaveDependencyValidator

logger = logging.getLogger(__name__)


class AddDependencyUseCase:
    """
    Caso de uso para adicionar dependência entre histórias.

    Responsabilidades:
    - Validar que ambas histórias existem
    - Simular adição e detectar ciclos
    - Validar regras de dependência de onda
    - Adicionar dependência se válido
    """

    def __init__(
        self, story_repository: StoryRepository, cycle_detector: CycleDetector, wave_validator: WaveDependencyValidator
    ):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            cycle_detector: Detector de ciclos
            wave_validator: Validador de dependências de onda
        """
        self._story_repository = story_repository
        self._cycle_detector = cycle_detector
        self._wave_validator = wave_validator

    def execute(self, story_id: str, depends_on_id: str) -> None:
        """
        Adiciona dependência entre histórias.

        Args:
            story_id: ID da história dependente
            depends_on_id: ID da história da qual depende

        Raises:
            StoryNotFoundException: Se alguma história não existe
            CyclicDependencyException: Se criaria ciclo (com caminho)
            InvalidWaveDependencyException: Se violar regra de onda (dependência em onda posterior)
        """
        logger.info(f"Adicionando dependência: '{story_id}' depende de '{depends_on_id}'")

        # 1. Buscar histórias
        story = self._story_repository.find_by_id(story_id)
        depends_on = self._story_repository.find_by_id(depends_on_id)

        if story is None:
            logger.error(f"História dependente não encontrada: id='{story_id}'")
            raise StoryNotFoundException(story_id)

        if depends_on is None:
            logger.error(f"História de dependência não encontrada: id='{depends_on_id}'")
            raise StoryNotFoundException(depends_on_id)

        # 2. Carregar features para validar ondas
        self._story_repository.load_feature(story)
        self._story_repository.load_feature(depends_on)
        logger.debug(f"Validando onda: '{story_id}' (wave={story.wave}) <- '{depends_on_id}' (wave={depends_on.wave})")

        # 3. Validar regra de onda (dependência deve estar em onda <= história)
        self._wave_validator.validate(story, depends_on)
        logger.debug("Validação de onda bem-sucedida")

        # 4. Buscar todas dependências atuais
        all_stories = self._story_repository.find_all()
        dependencies_map = {s.id: s.dependencies.copy() for s in all_stories}

        # 5. Simular adição da nova dependência
        if depends_on_id not in dependencies_map[story_id]:
            dependencies_map[story_id].append(depends_on_id)
            logger.debug(f"Simulando adição de dependência: '{story_id}' <- '{depends_on_id}'")

        # 6. Detectar ciclo (lança CyclicDependencyException se encontrar)
        logger.debug("Detectando ciclos no grafo de dependências")
        if self._cycle_detector.has_cycle(dependencies_map):
            logger.warning("Ciclo detectado! Buscando caminho do ciclo...")
            self._cycle_detector.find_cycle_path(dependencies_map)

        logger.debug("Nenhum ciclo detectado")

        # 7. Se válido, adicionar dependência
        story.add_dependency(depends_on_id)
        self._story_repository.save(story)
        logger.info(f"Dependência adicionada com sucesso: '{story_id}' depende de '{depends_on_id}'")
