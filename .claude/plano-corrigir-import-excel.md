# Plano: Corrigir Importacao de Excel para Features e Desenvolvedores

> **Data:** 2025-12-26
> **Status:** CONCLUIDO

---

## 1. Problema Identificado

### 1.1 Situacao Atual

O `ImportFromExcelUseCase` e o `OpenpyxlExcelService` **NAO importam corretamente**:

| Campo | Leitura | Processamento | Upsert | Status |
|-------|---------|---------------|--------|--------|
| Feature | Mapeado em COLUMN_ALIASES | NAO usa o valor | NAO | FALHA |
| Onda | Mapeado em COLUMN_ALIASES | NAO usa o valor | NAO | FALHA |
| Desenvolvedor | Le da planilha | Usa como string direto | NAO | PARCIAL |

### 1.2 Comportamento Atual vs Esperado

**Feature/Onda:**
```
ATUAL:
- Planilha: Feature="Core", Onda=1
- Codigo linha 300: feature_id="feature_default"
- Resultado: Todas as historias ficam com feature_default

ESPERADO:
- Planilha: Feature="Core", Onda=1
- Se Feature "Core" existe -> atualizar onda se diferente
- Se Feature "Core" NAO existe -> criar Feature(id=gerado, name="Core", wave=1)
- Historia fica com feature_id correto
```

**Desenvolvedor:**
```
ATUAL:
- Planilha: Desenvolvedor="AA"
- Codigo: developer_id = "AA" (string direta)
- Se Developer "AA" nao existe no banco -> historia tem FK invalida

ESPERADO:
- Planilha: Desenvolvedor="AA"
- Buscar Developer por nome "AA"
- Se existe -> usar seu ID
- Se NAO existe -> criar Developer(id=gerado, name="AA")
- Historia fica com developer_id valido
```

---

## 2. Arquivos a Modificar

1. `backlog_manager/application/use_cases/excel/import_from_excel.py`
   - Adicionar injecao de FeatureRepository e DeveloperRepository
   - Implementar logica de upsert para Features
   - Implementar logica de upsert para Developers

2. `backlog_manager/infrastructure/excel/openpyxl_excel_service.py`
   - Extrair e retornar valores de Feature e Onda no DTO
   - Extrair nome do desenvolvedor corretamente

3. `backlog_manager/application/dto/story_dto.py`
   - Verificar se DTO suporta feature_name e wave (JA SUPORTA!)

4. `backlog_manager/presentation/di_container.py`
   - Atualizar instanciacao do ImportFromExcelUseCase com novos repositories

5. Testes unitarios e de integracao

---

## 3. Solucao Proposta

### Fase 1: Modificar ExcelService para Retornar Feature e Onda

**Arquivo:** `openpyxl_excel_service.py`

```python
# Adicionar extracao de feature e onda na FASE 1 (linha ~220)
feature_value = self._extract_value(row, column_map, "feature")
onda_value = self._extract_value(row, column_map, "onda")

# Processar feature_name
feature_name = None
if feature_value and str(feature_value).strip():
    feature_name = str(feature_value).strip()

# Processar wave
wave = None
if onda_value is not None:
    try:
        wave = int(onda_value)
        if wave <= 0:
            wave = None
    except (ValueError, TypeError):
        wave = None

# Atualizar StoryDTO (linha ~296)
story_dto = StoryDTO(
    ...
    feature_id=None,  # Sera preenchido pelo UseCase
    feature_name=feature_name,  # NOVO
    wave=wave,  # NOVO
    ...
)
```

### Fase 2: Modificar ImportFromExcelUseCase para Upsert de Features

**Arquivo:** `import_from_excel.py`

```python
class ImportFromExcelUseCase:
    def __init__(
        self,
        story_repository: StoryRepository,
        excel_service: ExcelService,
        feature_repository: FeatureRepository,  # NOVO
        developer_repository: DeveloperRepository,  # NOVO
        cycle_detector: "CycleDetector | None" = None
    ):
        self._story_repository = story_repository
        self._excel_service = excel_service
        self._feature_repository = feature_repository  # NOVO
        self._developer_repository = developer_repository  # NOVO
        self._cycle_detector = cycle_detector or CycleDetector()

    def _upsert_feature(self, feature_name: str, wave: int) -> str:
        """
        Cria ou atualiza feature e retorna seu ID.

        Estrategia:
        1. Buscar feature por nome (case-insensitive)
        2. Se existe e onda diferente -> atualizar onda
        3. Se nao existe -> criar nova

        Returns:
            ID da feature (existente ou nova)
        """
        # Buscar todas as features
        all_features = self._feature_repository.find_all()

        # Procurar por nome (case-insensitive)
        existing = None
        for f in all_features:
            if f.name.lower() == feature_name.lower():
                existing = f
                break

        if existing:
            # Atualizar onda se diferente
            if existing.wave != wave:
                existing = Feature(id=existing.id, name=existing.name, wave=wave)
                self._feature_repository.save(existing)
                logger.info(f"Feature '{feature_name}' atualizada: onda {wave}")
            return existing.id
        else:
            # Criar nova feature
            new_id = self._generate_feature_id(feature_name)
            new_feature = Feature(id=new_id, name=feature_name, wave=wave)
            self._feature_repository.save(new_feature)
            logger.info(f"Feature '{feature_name}' criada com onda {wave}")
            return new_id

    def _generate_feature_id(self, name: str) -> str:
        """Gera ID unico para feature baseado no nome."""
        # Usar primeiras 3 letras + contador se necessario
        base = name[:3].upper()
        existing = self._feature_repository.find_by_id(base)
        if not existing:
            return base

        counter = 1
        while self._feature_repository.exists(f"{base}{counter}"):
            counter += 1
        return f"{base}{counter}"

    def _upsert_developer(self, developer_name: str) -> str:
        """
        Cria ou encontra desenvolvedor e retorna seu ID.

        Estrategia:
        1. Buscar desenvolvedor por nome (case-insensitive)
        2. Se existe -> retornar ID
        3. Se nao existe -> criar novo e retornar ID

        Returns:
            ID do desenvolvedor (existente ou novo)
        """
        # Buscar todos os desenvolvedores
        all_developers = self._developer_repository.find_all()

        # Procurar por nome (case-insensitive)
        for dev in all_developers:
            if dev.name.lower() == developer_name.lower():
                return dev.id

        # Criar novo desenvolvedor
        new_id = developer_name  # Usar nome como ID
        new_developer = Developer(id=new_id, name=developer_name)
        self._developer_repository.save(new_developer)
        logger.info(f"Desenvolvedor '{developer_name}' criado")
        return new_id
```

### Fase 3: Atualizar Processamento no execute()

```python
def execute(self, file_path: str, clear_existing: bool = False) -> BacklogDTO:
    # ... codigo existente ...

    # Adicionar estatisticas para features/developers
    stats["features_criadas"] = 0
    stats["features_atualizadas"] = 0
    stats["developers_criados"] = 0

    # Cache para evitar multiplas queries
    feature_cache: Dict[str, str] = {}  # nome -> id
    developer_cache: Dict[str, str] = {}  # nome -> id

    for dto in imported_stories_dto:
        try:
            # NOVO: Processar Feature
            feature_id = "feature_default"
            if dto.feature_name and dto.wave:
                cache_key = f"{dto.feature_name}:{dto.wave}"
                if cache_key in feature_cache:
                    feature_id = feature_cache[cache_key]
                else:
                    feature_id = self._upsert_feature(dto.feature_name, dto.wave)
                    feature_cache[cache_key] = feature_id

            dto.feature_id = feature_id

            # NOVO: Processar Developer
            if dto.developer_id:
                dev_name = dto.developer_id  # Na planilha e o nome, nao ID
                if dev_name in developer_cache:
                    dto.developer_id = developer_cache[dev_name]
                else:
                    dto.developer_id = self._upsert_developer(dev_name)
                    developer_cache[dev_name] = dto.developer_id

            # ... resto do processamento ...
```

### Fase 4: Atualizar DIContainer

**Arquivo:** `di_container.py`

```python
def get_import_from_excel_use_case(self) -> ImportFromExcelUseCase:
    return ImportFromExcelUseCase(
        story_repository=self._unit_of_work.stories,
        excel_service=self._excel_service,
        feature_repository=self._unit_of_work.features,  # NOVO
        developer_repository=self._unit_of_work.developers,  # NOVO
        cycle_detector=CycleDetector()
    )
```

### Fase 5: Adicionar Testes

```python
def test_import_creates_features_from_excel():
    """Deve criar features a partir das colunas Feature/Onda."""
    pass

def test_import_updates_existing_feature_wave():
    """Deve atualizar onda de feature existente."""
    pass

def test_import_creates_developers_from_excel():
    """Deve criar desenvolvedores inexistentes."""
    pass

def test_import_reuses_existing_developers():
    """Deve reutilizar desenvolvedores existentes."""
    pass
```

---

## 4. Fluxo de Importacao Atualizado

```
EXCEL                      USE CASE                    BANCO
------                     --------                    -----
Feature="Core"    ---->    _upsert_feature("Core", 1)
Onda=1                         |
                               v
                         Feature existe?
                               |
                    +----------+----------+
                    |                     |
                   SIM                   NAO
                    |                     |
              Onda diferente?       Criar Feature
                    |                     |
              Atualizar onda       Salvar no banco
                    |                     |
                    +----------+----------+
                               |
                         Retornar feature_id
                               |
                               v
Desenvolvedor="AA" ---->  _upsert_developer("AA")
                               |
                               v
                        Developer existe?
                               |
                    +----------+----------+
                    |                     |
                   SIM                   NAO
                    |                     |
              Retornar ID          Criar Developer
                    |                     |
                    +----------+----------+
                               |
                         Retornar developer_id
                               |
                               v
                    Story com feature_id e developer_id corretos
                               |
                               v
                        Salvar Story no banco
```

---

## 5. Consideracoes

### 5.1 Tratamento de Casos Especiais

| Caso | Tratamento |
|------|------------|
| Feature sem Onda | Usar onda padrao (1) |
| Onda sem Feature | Criar feature generica "Onda X" |
| Developer vazio | Manter developer_id = None |
| Feature vazia | Usar feature_default |

### 5.2 Ordem de Processamento

1. Primeiro processar todas as Features (evitar duplicatas)
2. Depois processar todos os Developers (evitar duplicatas)
3. Por ultimo processar Stories com IDs corretos

### 5.3 Cache para Performance

Usar dicionarios de cache para evitar queries repetidas:
- `feature_cache: Dict[str, str]` - nome:onda -> id
- `developer_cache: Dict[str, str]` - nome -> id

---

## 6. Checklist de Implementacao

- [ ] Fase 1: Modificar ExcelService para extrair Feature/Onda
- [ ] Fase 2: Adicionar _upsert_feature() no UseCase
- [ ] Fase 3: Adicionar _upsert_developer() no UseCase
- [ ] Fase 4: Atualizar execute() para usar upsert
- [ ] Fase 5: Atualizar DIContainer com novos repositories
- [ ] Fase 6: Adicionar testes unitarios
- [ ] Fase 7: Testar com dados reais

---

## 7. Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Features com mesmo nome e ondas diferentes | Media | Alto | Atualizar onda da existente |
| Developer ID conflito | Baixa | Medio | Usar nome como ID |
| Performance com muitas features | Baixa | Baixo | Cache em memoria |
| Ciclo de dependencias | Baixa | Medio | Validacao ja existente |

---

**Complexidade:** Media
**Tempo Estimado:** 4-6 horas
**Arquivos Afetados:** 4 principais + testes
