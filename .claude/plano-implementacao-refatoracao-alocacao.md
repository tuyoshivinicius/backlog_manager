# Plano Faseado de Implementação: Refatoração do Algoritmo de Alocação

**Baseado em**: `plano-refatorar-algoritmo-alocacao-desenvolvedores.md` v2.0
**Data**: 2025-12-25

---

## Visão Geral

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROADMAP DE IMPLEMENTAÇÃO                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FASE 1          FASE 2          FASE 3          FASE 4          FASE 5     │
│  Correções       Otimização      Refatoração     Melhorias        Opcional   │
│  Críticas        de I/O          Estrutural      Incrementais               │
│                                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐   │
│  │ M3, M9  │───►│ M1, M7  │───►│ M2, M8  │───►│ M10,M11 │───►│   M6    │   │
│  │ M4      │    │         │    │ M4→M5   │    │ M12     │    │         │   │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘   │
│                                                                              │
│  Crítico         Alto            Médio           Baixo          Opcional    │
│  ~1 dia          ~2 dias         ~3 dias         ~2 dias        ~3 dias     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Total estimado**: 8-11 dias (Fases 1-4) + 3 dias opcionais (Fase 5)

---

## Fase 1: Correções Críticas e Quick Wins

**Objetivo**: Corrigir bugs críticos e aplicar melhorias triviais que não afetam comportamento.

**Duração estimada**: 1 dia

### Tarefas

#### 1.1 Melhoria 3: Corrigir IdlenessWarning (CRÍTICO)

**Arquivos**:
- `backlog_manager/domain/services/idleness_detector.py`
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`
- `backlog_manager/presentation/controllers/schedule_controller.py`

**Passos**:
1. [ ] Criar dataclass `DeadlockWarning` em `idleness_detector.py`
2. [ ] Atualizar tipo `AllocationResult.warnings` para `List[Union[IdlenessWarning, DeadlockWarning]]`
3. [ ] Substituir uso incorreto de `IdlenessWarning` em `allocate_developers.py`
4. [ ] Atualizar `schedule_controller.py` para tratar novo tipo de warning
5. [ ] Executar testes existentes para garantir que não quebrou

**Testes**:
- [ ] `test_deadlock_warning_creation`: DeadlockWarning é criado corretamente
- [ ] `test_allocation_result_accepts_both_warnings`: AllocationResult aceita ambos os tipos

**Critério de Aceite**: Nenhum TypeError em runtime quando deadlock ocorre.

---

#### 1.2 Melhoria 9: Mover Import para Nível de Módulo

**Arquivos**:
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Passos**:
1. [ ] Mover `from datetime import timedelta` para topo do arquivo
2. [ ] Remover import duplicado de dentro do método `_count_workdays()`
3. [ ] Verificar se não há outros imports dentro de métodos

**Critério de Aceite**: Todos os imports estão no topo do arquivo.

---

#### 1.3 Melhoria 4: Otimizar Busca de Dependências com Dicionário

**Arquivos**:
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Passos**:
1. [ ] Adicionar atributo `self._story_map: Dict[str, Story]` à classe
2. [ ] Criar dicionário no início de `execute()`: `self._story_map = {s.id: s for s in all_stories}`
3. [ ] Criar método `_get_dependency_stories(self, story: Story) -> List[Story]`
4. [ ] Substituir todas as ocorrências de `next((s for s in all_stories if s.id == dep_id), None)` por `self._story_map.get(dep_id)`
5. [ ] Adicionar log warning para dependências não encontradas

**Locais para refatorar** (buscar por `next((s for s in`):
- [ ] `_ensure_dependencies_finished()`
- [ ] `_final_dependency_check()`
- [ ] `_get_latest_dependency_end_date()`
- [ ] `_can_allocate_story()`

**Testes**:
- [ ] `test_story_map_created_correctly`: Dicionário é criado com todas as histórias
- [ ] `test_get_dependency_stories_returns_correct`: Retorna histórias corretas
- [ ] `test_missing_dependency_logs_warning`: Dependência inexistente gera log

**Critério de Aceite**: Nenhuma busca linear O(n) para dependências.

---

### Checkpoint Fase 1

```bash
# Executar todos os testes
./.venv/Scripts/python.exe -m pytest tests/ -v

# Verificar type hints
./.venv/Scripts/python.exe -m mypy backlog_manager/

# Testar aplicação manualmente
./.venv/Scripts/python.exe -m backlog_manager.main
```

**Critérios de Aprovação**:
- [ ] Todos os testes passando
- [ ] Mypy sem erros
- [ ] Aplicação inicia e funciona normalmente
- [ ] Alocação de desenvolvedores funciona

---

## Fase 2: Otimização de I/O

**Objetivo**: Reduzir operações de banco de dados e melhorar performance.

**Duração estimada**: 2 dias

**Pré-requisito**: Fase 1 concluída

### Tarefas

#### 2.1 Melhoria 1: Eliminar Chamadas Redundantes ao Repositório

**Arquivos**:
- `backlog_manager/application/interfaces/repositories/story_repository.py`
- `backlog_manager/infrastructure/database/repositories/sqlite_story_repository.py`
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Passos**:

**Dia 1: Implementar save_batch()**
1. [ ] Adicionar método abstrato `save_batch(stories: List[Story])` à interface `StoryRepository`
2. [ ] Implementar `save_batch()` em `SQLiteStoryRepository`:
   ```python
   def save_batch(self, stories: List[Story]) -> None:
       with self._connection:
           for story in stories:
               self._connection.execute(...)
   ```
3. [ ] Escrever testes para `save_batch()`

**Dia 2: Refatorar AllocateDevelopersUseCase**
4. [ ] Modificar `execute()` para carregar histórias uma única vez no início
5. [ ] Usar `self._story_map` (já criado na Fase 1) como cache
6. [ ] Remover chamadas a `find_all()` no meio do algoritmo
7. [ ] Adicionar `save_batch()` no final de `execute()`
8. [ ] Refatorar `_update_schedule_order_from_table()` para operar no cache

**Testes**:
- [ ] `test_save_batch_saves_all_stories`: Todas as histórias são salvas
- [ ] `test_save_batch_single_transaction`: Operação é atômica
- [ ] `test_execute_single_find_all`: Apenas uma chamada a find_all()

**Critério de Aceite**:
- Apenas 1 chamada a `find_all()` por execução
- Apenas 1 chamada a `save_batch()` no final

---

#### 2.2 Melhoria 7: Simplificar Sincronização de schedule_order

**Arquivos**:
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Passos**:
1. [ ] Verificar usos de `schedule_order` no código:
   ```bash
   grep -r "schedule_order" backlog_manager/
   ```
2. [ ] Remover chamada a `_update_schedule_order_from_table()` no início de `execute()`
3. [ ] Adicionar atualização de `schedule_order` no final, antes de `save_batch()`:
   ```python
   sorted_stories = sorted(all_stories, key=lambda s: s.priority)
   for idx, story in enumerate(sorted_stories):
       story.schedule_order = idx
   ```
4. [ ] Testar que UI e export continuam funcionando

**Testes**:
- [ ] `test_schedule_order_updated_at_end`: schedule_order atualizado corretamente
- [ ] `test_ui_displays_correct_order`: UI exibe histórias na ordem correta
- [ ] `test_excel_export_correct_order`: Export mantém ordem

**Critério de Aceite**: `_update_schedule_order_from_table()` não é mais chamado separadamente.

---

### Checkpoint Fase 2

```bash
# Testes de performance
./.venv/Scripts/python.exe -c "
import time
from backlog_manager.presentation.di_container import DIContainer
container = DIContainer()
use_case = container.get_allocate_developers_use_case()
start = time.perf_counter()
use_case.execute()
print(f'Tempo: {(time.perf_counter() - start) * 1000:.1f}ms')
"
```

**Critérios de Aprovação**:
- [ ] Todos os testes passando
- [ ] Performance igual ou melhor que antes
- [ ] Aplicação funciona normalmente

---

## Fase 3: Refatoração Estrutural

**Objetivo**: Unificar lógicas duplicadas e implementar nova funcionalidade de priorização.

**Duração estimada**: 3 dias

**Pré-requisito**: Fases 1 e 2 concluídas

### Tarefas

#### 3.1 Melhoria 2: Unificar Cálculo de Dias Úteis

**Arquivos**:
- `backlog_manager/domain/services/schedule_calculator.py`
- `backlog_manager/domain/services/idleness_detector.py`
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`
- `backlog_manager/presentation/utils/di_container.py`

**Passos**:

**Dia 1: Implementar métodos no ScheduleCalculator**
1. [ ] Adicionar método `_is_workday(self, d: date) -> bool` ao `ScheduleCalculator`
2. [ ] Adicionar método `count_workdays(self, start: date, end: date) -> int`
3. [ ] Escrever testes unitários para os novos métodos

**Dia 2: Refatorar classes que usam cálculo de dias úteis**
4. [ ] Remover `_count_workdays()` de `AllocateDevelopersUseCase`
5. [ ] Substituir por chamadas a `self._schedule_calculator.count_workdays()`
6. [ ] Modificar `IdlenessDetector.__init__()` para receber `ScheduleCalculator`
7. [ ] Substituir `_calculate_workday_gap()` por chamada ao `ScheduleCalculator`
8. [ ] Atualizar `DIContainer` para injetar `ScheduleCalculator` no `IdlenessDetector`

**Testes**:
- [ ] `test_count_workdays_excludes_weekends`: Exclui fins de semana
- [ ] `test_count_workdays_excludes_holidays`: Exclui feriados brasileiros
- [ ] `test_is_workday_returns_false_for_holiday`: Retorna False para feriado
- [ ] `test_idleness_detector_uses_schedule_calculator`: IdlenessDetector usa ScheduleCalculator

**Critério de Aceite**: Apenas uma implementação de cálculo de dias úteis no sistema.

---

#### 3.2 Melhoria 8: Extrair Lógica de Ajuste de Datas

**Arquivos**:
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Passos**:
1. [ ] Criar método `_recalculate_story_dates(story, new_start_date) -> Tuple[date, date]`
2. [ ] Criar método `_update_story_dates(story, new_start) -> None`
3. [ ] Refatorar `_adjust_story_dates()` para usar `_update_story_dates()`
4. [ ] Refatorar `_ensure_dependencies_finished()` para usar `_recalculate_story_dates()`
5. [ ] Refatorar `_final_dependency_check()` para usar `_recalculate_story_dates()`

**Testes**:
- [ ] `test_recalculate_story_dates_preserves_duration`: Mantém duração original
- [ ] `test_recalculate_story_dates_adjusts_to_workday`: Ajusta para dia útil
- [ ] `test_update_story_dates_modifies_in_place`: Atualiza história in-place

**Critério de Aceite**: Lógica de ajuste de datas em um único lugar.

---

#### 3.3 Melhoria 5: Priorização por Proprietário de Dependência

**Arquivos**:
- `backlog_manager/domain/services/developer_load_balancer.py`
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Passos**:

**Dia 3: Implementar nova lógica de alocação**
1. [ ] Adicionar método `_get_dependency_owner()` ao `DeveloperLoadBalancer`
2. [ ] Adicionar método `get_developer_for_story()` que:
   - Primeiro tenta alocar proprietário de dependência
   - Fallback para `get_developer_with_lowest_load()`
3. [ ] Atualizar `AllocateDevelopersUseCase` para usar `get_developer_for_story()` em vez de `get_developer_with_lowest_load()`
4. [ ] Passar `story_map` para o `DeveloperLoadBalancer`

**Testes**:
- [ ] `test_get_dependency_owner_returns_correct_dev`: Retorna dev correto
- [ ] `test_get_dependency_owner_returns_none_when_unavailable`: Retorna None se indisponível
- [ ] `test_get_developer_for_story_fallback`: Fallback para balanceamento funciona
- [ ] `test_dependent_stories_same_developer`: Histórias dependentes ficam com mesmo dev

**Critério de Aceite**:
- Histórias dependentes são preferencialmente alocadas ao mesmo desenvolvedor
- Balanceamento de carga ainda funciona como fallback

---

### Checkpoint Fase 3

```bash
# Testes completos
./.venv/Scripts/python.exe -m pytest tests/ -v --tb=short

# Teste manual de priorização
# 1. Criar história H1 alocada ao Dev A
# 2. Criar história H2 dependente de H1
# 3. Executar alocação
# 4. Verificar que H2 foi alocada ao Dev A
```

**Critérios de Aprovação**:
- [ ] Todos os testes passando
- [ ] Priorização por dependência funcionando
- [ ] Balanceamento de carga como fallback

---

## Fase 4: Melhorias Incrementais

**Objetivo**: Adicionar funcionalidades de suporte e melhorar observabilidade.

**Duração estimada**: 2 dias

**Pré-requisito**: Fases 1-3 concluídas

### Tarefas

#### 4.1 Melhoria 10: Adicionar Métricas de Performance

**Arquivos**:
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Passos**:
1. [ ] Criar dataclass `AllocationMetrics`
2. [ ] Adicionar coleta de métricas em `execute()`:
   - Tempo total de execução
   - Número de histórias processadas
   - Número de ondas
   - Iterações por onda
   - Alocações por fallback (balanceamento)
3. [ ] Adicionar logging de métricas no final
4. [ ] Incluir `metrics` no `AllocationResult`

**Testes**:
- [ ] `test_metrics_collected`: Métricas são coletadas
- [ ] `test_metrics_logged`: Métricas são logadas

**Critério de Aceite**: Métricas de execução disponíveis no log.

---

#### 4.2 Melhoria 11: Tornar MAX_ITERATIONS Configurável

**Arquivos**:
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`
- `backlog_manager/presentation/utils/di_container.py`

**Passos**:
1. [ ] Adicionar constante `DEFAULT_MAX_ITERATIONS = 1000`
2. [ ] Modificar `__init__()` para aceitar parâmetro `max_iterations`
3. [ ] Substituir hardcoded `1000` por `self._max_iterations`
4. [ ] Atualizar `DIContainer` se necessário

**Testes**:
- [ ] `test_max_iterations_configurable`: Parâmetro é respeitado
- [ ] `test_default_max_iterations`: Valor padrão é 1000

**Critério de Aceite**: MAX_ITERATIONS pode ser configurado via parâmetro.

---

#### 4.3 Melhoria 12: Melhorar Detecção de Deadlock

**Arquivos**:
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Passos**:
1. [ ] Criar método `_detect_deadlock()` com três critérios:
   - Limite de iterações excedido
   - Estado não mudou entre iterações
   - Nenhum desenvolvedor disponível
2. [ ] Criar método auxiliar `_no_developer_available_for_any()`
3. [ ] Substituir heurística simples atual por `_detect_deadlock()`
4. [ ] Melhorar mensagens de erro

**Testes**:
- [ ] `test_detect_deadlock_iteration_limit`: Detecta limite de iterações
- [ ] `test_detect_deadlock_no_progress`: Detecta estado idêntico
- [ ] `test_detect_deadlock_no_developers`: Detecta falta de desenvolvedores

**Critério de Aceite**: Detecção de deadlock mais precisa com mensagens informativas.

---

### Checkpoint Fase 4

```bash
# Verificar logs de métricas
BACKLOG_MANAGER_LOG_LEVEL=DEBUG ./.venv/Scripts/python.exe -m backlog_manager.main

# Testes completos
./.venv/Scripts/python.exe -m pytest tests/ -v
```

**Critérios de Aprovação**:
- [ ] Todos os testes passando
- [ ] Métricas aparecendo no log
- [ ] Detecção de deadlock mais precisa

---

## Fase 5: Otimização Opcional (Alta Complexidade)

**Objetivo**: Implementar otimização avançada de performance.

**Duração estimada**: 3 dias

**Pré-requisito**: Fases 1-4 concluídas

**Quando implementar**: Apenas se backlog típico > 50 histórias ou time > 5 desenvolvedores

### Tarefas

#### 5.1 Melhoria 6: Cache de Disponibilidade por Período

**Arquivos**:
- Novo: `backlog_manager/domain/services/developer_schedule_cache.py`
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Passos**:

**Dia 1: Implementar DeveloperScheduleCache**
1. [ ] Criar dataclass `OccupiedPeriod`
2. [ ] Criar classe `DeveloperScheduleCache` com:
   - `initialize(stories)` - popula cache inicial
   - `add_allocation(dev_id, start, end, story_id)` - adiciona alocação
   - `is_available(dev_id, start, end)` - verifica disponibilidade O(log K)
   - `get_available_developers(dev_ids, start, end)` - retorna disponíveis
3. [ ] Implementar busca binária para inserção e verificação

**Dia 2: Testes extensivos**
4. [ ] Escrever testes unitários completos
5. [ ] Testar edge cases (períodos adjacentes, sobreposição parcial)
6. [ ] Benchmarks de performance

**Dia 3: Integrar no AllocateDevelopersUseCase**
7. [ ] Inicializar cache no início de `execute()`
8. [ ] Substituir `_get_available_developers()` por cache
9. [ ] Atualizar cache após cada alocação
10. [ ] Testar integração completa

**Testes**:
- [ ] `test_cache_initialize_populates`: Cache é populado corretamente
- [ ] `test_is_available_detects_overlap`: Detecta sobreposição
- [ ] `test_add_allocation_maintains_order`: Mantém ordem cronológica
- [ ] `test_binary_search_edge_cases`: Busca binária em casos limite
- [ ] `test_performance_improvement`: Performance melhor que antes

**Critério de Aceite**:
- Verificação de disponibilidade em O(log K)
- Performance 10x melhor para backlogs grandes

---

### Checkpoint Fase 5

```bash
# Benchmark comparativo
./.venv/Scripts/python.exe -c "
import time
# Executar com cache vs sem cache
# Comparar tempos
"
```

**Critérios de Aprovação**:
- [ ] Todos os testes passando
- [ ] Performance significativamente melhor para backlogs grandes
- [ ] Nenhuma regressão para backlogs pequenos

---

## Resumo do Plano

| Fase | Melhorias | Duração | Risco | Prioridade |
|------|-----------|---------|-------|------------|
| 1 | M3, M9, M4 | 1 dia | Baixo | Crítica |
| 2 | M1, M7 | 2 dias | Médio | Alta |
| 3 | M2, M8, M5 | 3 dias | Médio | Alta |
| 4 | M10, M11, M12 | 2 dias | Baixo | Média |
| 5 | M6 | 3 dias | Alto | Opcional |

**Total**: 8-11 dias (excluindo Fase 5)

---

## Critérios de Sucesso Global

Ao final de todas as fases:

- [ ] **Funcionalidade**: 100% das funcionalidades existentes preservadas
- [ ] **Testes**: Cobertura >= 90% para código novo
- [ ] **Performance**: Igual ou melhor que baseline
- [ ] **Qualidade**: Mypy e flake8 sem erros
- [ ] **Documentação**: CLAUDE.md atualizado

---

**Data**: 2025-12-25
**Versão**: 1.0
