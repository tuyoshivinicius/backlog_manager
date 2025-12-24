"""Caso de uso para importar backlog de Excel."""
from typing import Set

from backlog_manager.application.dto.backlog_dto import BacklogDTO
from backlog_manager.application.dto.converters import story_to_dto, dto_to_story
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.application.interfaces.services.excel_service import ExcelService
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.services.cycle_detector import CycleDetector
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


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

    def _merge_stories(
        self,
        existing: Story,
        imported: StoryDTO,
        columns_present: Set[str]
    ) -> Story:
        """
        Atualiza história existente preservando campos calculados.

        Regras de merge:
        - SEMPRE preserva: start_date, end_date, duration (campos calculados)
        - Se coluna presente na planilha → atualiza
        - Se coluna ausente na planilha → preserva valor existente

        Args:
            existing: História existente no banco
            imported: DTO importado da planilha
            columns_present: Set de campos presentes na planilha

        Returns:
            História atualizada (merge inteligente)
        """
        # Converter story_point se presente
        story_point = existing.story_point
        if "story_point" in columns_present and imported.story_point is not None:
            story_point = StoryPoint(imported.story_point)
        elif "story_point" in columns_present and imported.story_point is None:
            story_point = None

        # Converter status se presente
        status = existing.status
        if "status" in columns_present:
            status = StoryStatus.from_string(imported.status)

        # Atualizar apenas campos presentes na planilha (exceto calculados)
        return Story(
            id=existing.id,
            feature=imported.feature if "feature" in columns_present else existing.feature,
            name=imported.name if "nome" in columns_present else existing.name,
            story_point=story_point,
            status=status,
            priority=imported.priority if "prioridade" in columns_present else existing.priority,
            developer_id=imported.developer_id if "desenvolvedor" in columns_present else existing.developer_id,
            dependencies=imported.dependencies if "deps" in columns_present else existing.dependencies,
            # Campos calculados SEMPRE preservados
            start_date=existing.start_date,
            end_date=existing.end_date,
            duration=existing.duration,
        )

    def execute(self, file_path: str, clear_existing: bool = False) -> BacklogDTO:
        """
        Importa histórias de arquivo Excel com suporte a UPDATE e INSERT.

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

        # 2. Buscar histórias existentes no banco
        existing_stories = self._story_repository.find_all()
        existing_stories_dict = {s.id: s for s in existing_stories}

        # 3. Delegar leitura para ExcelService (NOVA ASSINATURA: retorna 3 valores)
        imported_stories_dto, stats, columns_present = self._excel_service.import_stories(
            file_path,
            existing_ids=set(existing_stories_dict.keys()) if not clear_existing else set()
        )

        # Adicionar estatísticas de UPDATE/INSERT
        stats["historias_criadas"] = 0
        stats["historias_atualizadas"] = 0

        # 4. Processar cada DTO importado
        processed_stories = []

        for dto in imported_stories_dto:
            try:
                # Verificar se história já existe (modo UPDATE ou INSERT)
                if dto.id in existing_stories_dict and not clear_existing:
                    # UPDATE: merge inteligente preservando campos calculados
                    existing_story = existing_stories_dict[dto.id]
                    updated_story = self._merge_stories(existing_story, dto, columns_present)
                    processed_stories.append(updated_story)
                    stats["historias_atualizadas"] += 1
                else:
                    # INSERT: criar nova história
                    new_story = dto_to_story(dto)
                    processed_stories.append(new_story)
                    stats["historias_criadas"] += 1

            except ValueError as e:
                # Entidade rejeitou (validação falhou)
                stats["ignoradas_invalidas"] += 1
                stats["warnings"].append(f"História {dto.id}: {str(e)}")

        # 5. Validar dependências (ciclos) - APENAS se houver histórias com dependências
        stories_with_deps = [s for s in processed_stories if s.dependencies]

        if stories_with_deps:
            # Criar lista temporária com todas as histórias (existentes + processadas)
            # Filtrar histórias existentes que NÃO foram atualizadas
            unchanged_existing = [
                s for s in existing_stories
                if s.id not in {ps.id for ps in processed_stories}
            ]
            all_stories_for_validation = unchanged_existing + processed_stories

            # Converter lista de histórias para dict de dependências {story_id: [deps]}
            dependencies_dict = {
                story.id: story.dependencies.copy()
                for story in all_stories_for_validation
            }

            # Verificar cada história com dependências
            stories_to_remove = []
            for story in stories_with_deps:
                # Verificar se essa história causaria um ciclo
                if self._cycle_detector.has_cycle(dependencies_dict):
                    stories_to_remove.append(story)
                    stats["ignoradas_invalidas"] += 1
                    stats["warnings"].append(
                        f"História {story.id}: dependências criariam ciclo - ignorada"
                    )
                    # Reverter estatística de criação/atualização
                    if story.id in existing_stories_dict:
                        stats["historias_atualizadas"] -= 1
                    else:
                        stats["historias_criadas"] -= 1

                    # Atualizar dict após remover história
                    if story.id in dependencies_dict:
                        del dependencies_dict[story.id]

            # Remover histórias que causam ciclos
            for story in stories_to_remove:
                processed_stories.remove(story)

        # 6. Persistir histórias processadas
        for story in processed_stories:
            self._story_repository.save(story)

        # 7. Calcular metadados (proteger contra story_point None)
        total_sp = sum(
            s.story_point.value for s in processed_stories
            if s.story_point is not None
        )

        # Duração será calculada por CalculateScheduleUseCase
        duration_days = 0

        # 8. Retornar BacklogDTO com estatísticas
        return BacklogDTO(
            stories=[story_to_dto(s) for s in processed_stories],
            total_count=len(processed_stories),
            total_story_points=total_sp,
            estimated_duration_days=duration_days,
            import_stats=stats  # Estatísticas da importação (com UPDATE/INSERT)
        )
