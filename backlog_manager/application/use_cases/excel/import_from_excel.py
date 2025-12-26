"""Caso de uso para importar backlog de Excel."""
import logging
import uuid
from typing import Dict, Optional, Set

from backlog_manager.application.dto.backlog_dto import BacklogDTO
from backlog_manager.application.dto.converters import story_to_dto, dto_to_story
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
from backlog_manager.application.interfaces.repositories.feature_repository import FeatureRepository
from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.application.interfaces.services.excel_service import ExcelService
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.entities.feature import Feature
from backlog_manager.domain.entities.developer import Developer
from backlog_manager.domain.services.cycle_detector import CycleDetector
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus

logger = logging.getLogger(__name__)


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
        cycle_detector: "CycleDetector | None" = None,
        feature_repository: "FeatureRepository | None" = None,
        developer_repository: "DeveloperRepository | None" = None,
    ):
        """
        Inicializa caso de uso.

        Args:
            story_repository: Repositório de histórias
            excel_service: Serviço de Excel (adaptor)
            cycle_detector: Detector de ciclos (opcional, criado automaticamente se None)
            feature_repository: Repositório de features (para upsert)
            developer_repository: Repositório de desenvolvedores (para upsert)
        """
        self._story_repository = story_repository
        self._excel_service = excel_service
        self._cycle_detector = cycle_detector or CycleDetector()
        self._feature_repository = feature_repository
        self._developer_repository = developer_repository
        # Cache para evitar queries repetidas durante importação
        self._feature_cache: Dict[str, str] = {}  # "nome:onda" -> feature_id
        self._developer_cache: Dict[str, str] = {}  # nome -> developer_id

    def _upsert_feature(self, feature_name: str, wave: int) -> str:
        """
        Cria ou encontra feature e retorna seu ID.

        Estratégia:
        1. Buscar feature por nome (case-insensitive)
        2. Se existe -> retornar ID (ignorando onda da planilha, pois onda é UNIQUE)
        3. Se não existe -> verificar se onda está disponível
           - Se disponível: criar nova feature
           - Se não disponível: encontrar próxima onda e criar

        Args:
            feature_name: Nome da feature
            wave: Número da onda desejada

        Returns:
            ID da feature (existente ou nova)
        """
        if self._feature_repository is None:
            return "feature_default"

        # Verificar cache primeiro (por nome apenas, já que onda pode variar)
        cache_key = feature_name.lower()
        if cache_key in self._feature_cache:
            return self._feature_cache[cache_key]

        # Buscar todas as features
        all_features = self._feature_repository.find_all()

        # Procurar por nome (case-insensitive)
        existing = None
        for f in all_features:
            if f.name.lower() == feature_name.lower():
                existing = f
                break

        if existing:
            # Feature já existe - usar ID existente (onda é propriedade da feature, não da planilha)
            if existing.wave != wave:
                logger.debug(
                    f"Feature '{feature_name}' já existe com onda {existing.wave} "
                    f"(planilha indica onda {wave}, ignorando)"
                )
            self._feature_cache[cache_key] = existing.id
            return existing.id
        else:
            # Feature não existe - verificar se onda está disponível
            used_waves = {f.wave for f in all_features}

            if wave in used_waves:
                # Onda já em uso por outra feature - encontrar próxima disponível
                new_wave = wave
                while new_wave in used_waves:
                    new_wave += 1
                logger.warning(
                    f"Onda {wave} já em uso. Feature '{feature_name}' criada com onda {new_wave}"
                )
                wave = new_wave

            # Criar nova feature
            new_id = self._generate_feature_id(feature_name)
            new_feature = Feature(id=new_id, name=feature_name, wave=wave)
            self._feature_repository.save(new_feature)
            logger.info(f"Feature '{feature_name}' criada com onda {wave}")
            self._feature_cache[cache_key] = new_id
            return new_id

    def _generate_feature_id(self, name: str) -> str:
        """
        Gera ID único para feature baseado no nome.

        Args:
            name: Nome da feature

        Returns:
            ID único para a feature
        """
        if self._feature_repository is None:
            return f"feat_{uuid.uuid4().hex[:8]}"

        # Usar primeiras 3 letras + contador se necessário
        base = name[:3].upper()
        if not self._feature_repository.exists(base):
            return base

        counter = 1
        while self._feature_repository.exists(f"{base}{counter}"):
            counter += 1
        return f"{base}{counter}"

    def _upsert_developer(self, developer_name: str) -> str:
        """
        Cria ou encontra desenvolvedor e retorna seu ID.

        Estratégia:
        1. Buscar desenvolvedor por nome (case-insensitive)
        2. Se existe -> retornar ID
        3. Se não existe -> criar novo e retornar ID

        Args:
            developer_name: Nome do desenvolvedor

        Returns:
            ID do desenvolvedor (existente ou novo)
        """
        if self._developer_repository is None:
            return developer_name  # Fallback: usar nome como ID

        # Verificar cache primeiro
        cache_key = developer_name.lower()
        if cache_key in self._developer_cache:
            return self._developer_cache[cache_key]

        # Buscar todos os desenvolvedores
        all_developers = self._developer_repository.find_all()

        # Procurar por nome (case-insensitive)
        for dev in all_developers:
            if dev.name.lower() == developer_name.lower():
                self._developer_cache[cache_key] = dev.id
                return dev.id

        # Criar novo desenvolvedor (usar nome como ID para simplicidade)
        new_id = developer_name
        new_developer = Developer(id=new_id, name=developer_name)
        self._developer_repository.save(new_developer)
        logger.info(f"Desenvolvedor '{developer_name}' criado")
        self._developer_cache[cache_key] = new_id
        return new_id

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

        # Determinar feature_id baseado na presença de colunas Feature/Onda
        feature_id = existing.feature_id
        if "feature" in columns_present and imported.feature_id:
            feature_id = imported.feature_id

        # Atualizar apenas campos presentes na planilha (exceto calculados)
        return Story(
            id=existing.id,
            component=imported.component if "component" in columns_present else existing.component,
            name=imported.name if "nome" in columns_present else existing.name,
            story_point=story_point,
            status=status,
            priority=imported.priority if "prioridade" in columns_present else existing.priority,
            developer_id=imported.developer_id if "desenvolvedor" in columns_present else existing.developer_id,
            dependencies=imported.dependencies if "deps" in columns_present else existing.dependencies,
            feature_id=feature_id,
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
        logger.info(f"Iniciando importação de Excel: file='{file_path}', clear_existing={clear_existing}")

        # Limpar cache no início da importação
        self._feature_cache.clear()
        self._developer_cache.clear()

        # 1. Limpar backlog se solicitado
        if clear_existing:
            all_stories = self._story_repository.find_all()
            logger.warning(f"Limpando {len(all_stories)} histórias existentes")
            for story in all_stories:
                self._story_repository.delete(story.id)

        # 2. Buscar histórias existentes no banco
        existing_stories = self._story_repository.find_all()
        existing_stories_dict = {s.id: s for s in existing_stories}
        logger.debug(f"Histórias existentes no banco: {len(existing_stories)}")

        # 3. Delegar leitura para ExcelService (NOVA ASSINATURA: retorna 3 valores)
        logger.debug("Lendo arquivo Excel")
        imported_stories_dto, stats, columns_present = self._excel_service.import_stories(
            file_path,
            existing_ids=set(existing_stories_dict.keys()) if not clear_existing else set()
        )
        logger.info(f"Lidas {len(imported_stories_dto)} histórias do Excel")

        # Adicionar estatísticas de UPDATE/INSERT e upsert
        stats["historias_criadas"] = 0
        stats["historias_atualizadas"] = 0
        stats["features_criadas"] = 0
        stats["features_atualizadas"] = 0
        stats["developers_criados"] = 0

        # 4. Processar cada DTO importado
        processed_stories = []

        for dto in imported_stories_dto:
            try:
                # NOVO: Processar Feature/Onda (upsert)
                if dto.feature_name and dto.wave:
                    feature_id = self._upsert_feature(dto.feature_name, dto.wave)
                    dto.feature_id = feature_id
                elif dto.feature_name and not dto.wave:
                    # Feature sem onda - usar onda padrão 1
                    feature_id = self._upsert_feature(dto.feature_name, 1)
                    dto.feature_id = feature_id
                    stats["warnings"].append(
                        f"História {dto.id}: Feature '{dto.feature_name}' sem onda - usando onda 1"
                    )
                # Se não tem feature_name, manter feature_id como None (já definido pelo ExcelService)

                # NOVO: Processar Developer (upsert)
                if dto.developer_id:
                    developer_name = dto.developer_id  # Na planilha é o nome, não ID
                    dto.developer_id = self._upsert_developer(developer_name)

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
        logger.info(f"Importação concluída: {stats['historias_criadas']} criadas, {stats['historias_atualizadas']} atualizadas, {stats['ignoradas_invalidas']} ignoradas")

        return BacklogDTO(
            stories=[story_to_dto(s) for s in processed_stories],
            total_count=len(processed_stories),
            total_story_points=total_sp,
            estimated_duration_days=duration_days,
            import_stats=stats  # Estatísticas da importação (com UPDATE/INSERT)
        )
