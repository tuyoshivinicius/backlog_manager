"""Caso de uso para importar backlog de Excel."""
from backlog_manager.application.dto.backlog_dto import BacklogDTO
from backlog_manager.application.dto.converters import story_to_dto, dto_to_story
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.application.interfaces.services.excel_service import ExcelService
from backlog_manager.domain.services.cycle_detector import CycleDetector


class ImportFromExcelUseCase:
    """
    Caso de uso para importar histórias de arquivo Excel.

    Responsabilidades:
    - Delegar leitura para ExcelService (com validação de duplicatas e deps)
    - Converter DTOs → Story entities
    - Validar dados (feito pela entidade Story)
    - Validar ciclos em dependências
    - Persistir histórias válidas
    - Retornar BacklogDTO com histórias importadas e estatísticas
    """

    def __init__(
        self,
        story_repository: StoryRepository,
        excel_service: ExcelService,
        cycle_detector: "CycleDetector | None" = None
    ):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            excel_service: Serviço de Excel (adaptor)
            cycle_detector: Detector de ciclos (opcional, criado automaticamente se None)
        """
        self._story_repository = story_repository
        self._excel_service = excel_service
        self._cycle_detector = cycle_detector or CycleDetector()

    def execute(self, file_path: str, clear_existing: bool = False) -> BacklogDTO:
        """
        Importa histórias de arquivo Excel.

        Args:
            file_path: Caminho do arquivo Excel
            clear_existing: Se True, limpa backlog existente antes de importar

        Returns:
            BacklogDTO com histórias importadas e estatísticas

        Raises:
            FileNotFoundError: Se arquivo não existe
            ValueError: Se dados inválidos no Excel (cabeçalho incorreto)
        """
        # 1. Limpar backlog se solicitado
        if clear_existing:
            all_stories = self._story_repository.find_all()
            for story in all_stories:
                self._story_repository.delete(story.id)

        # 2. Buscar IDs existentes no banco (para validação de duplicatas)
        existing_stories = self._story_repository.find_all()
        existing_ids = {s.id for s in existing_stories}

        # 3. Delegar leitura para ExcelService (NOVA ASSINATURA: retorna tupla)
        imported_stories_dto, stats = self._excel_service.import_stories(
            file_path,
            existing_ids=existing_ids if not clear_existing else set()
        )

        # 4. CORRIGIR BUG: Converter DTOs → Story entities
        imported_stories = []
        for dto in imported_stories_dto:
            try:
                story = dto_to_story(dto)
                imported_stories.append(story)
            except ValueError as e:
                # Entidade rejeitou (validação falhou)
                stats["ignoradas_invalidas"] += 1
                stats["warnings"].append(f"História {dto.id}: {str(e)}")

        # 5. Validar dependências (ciclos) - APENAS se houver histórias com dependências
        stories_with_deps = [s for s in imported_stories if s.dependencies]

        if stories_with_deps:
            # Criar lista temporária com todas as histórias (existentes + novas)
            all_stories_for_validation = list(existing_stories) + imported_stories

            # Converter lista de histórias para dict de dependências {story_id: [deps]}
            dependencies_dict = {
                story.id: story.dependencies.copy()
                for story in all_stories_for_validation
            }

            # Verificar cada história com dependências
            for story in stories_with_deps:
                # Verificar se criar essa história causaria um ciclo
                if self._cycle_detector.has_cycle(dependencies_dict):
                    # Remover história que causaria ciclo
                    imported_stories.remove(story)
                    stats["ignoradas_invalidas"] += 1
                    stats["warnings"].append(
                        f"História {story.id}: dependências criariam ciclo - ignorada"
                    )
                    # Atualizar dict após remover história
                    if story.id in dependencies_dict:
                        del dependencies_dict[story.id]

        # 6. Persistir histórias válidas (verificar se não existem no banco se clear_existing=False)
        for story in imported_stories:
            # Se clear_existing=False, verificar se já existe
            if not clear_existing and story.id in existing_ids:
                stats["ignoradas_invalidas"] += 1
                stats["warnings"].append(
                    f"História {story.id}: já existe no banco - ignorada"
                )
                continue

            self._story_repository.save(story)

        # 7. Calcular metadados (CORRIGIR BUG: proteger contra story_point None)
        total_sp = sum(
            s.story_point.value for s in imported_stories
            if s.story_point is not None
        )

        # Duração será calculada por CalculateScheduleUseCase
        duration_days = 0

        # 8. Retornar BacklogDTO com estatísticas
        return BacklogDTO(
            stories=[story_to_dto(s) for s in imported_stories],
            total_count=len(imported_stories),
            total_story_points=total_sp,
            estimated_duration_days=duration_days,
            import_stats=stats  # NOVO: estatísticas da importação
        )
