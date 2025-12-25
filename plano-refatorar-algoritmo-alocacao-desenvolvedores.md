# Plano de Refatoração: Algoritmo de Alocação Automática de Desenvolvedores

## Sumário Executivo

Este documento identifica oportunidades de melhoria no algoritmo de alocação automática de desenvolvedores (`AllocateDevelopersUseCase`), focando em simplicidade, eficiência e manutenibilidade, preservando todas as funcionalidades existentes.

**Arquivos analisados:**
- `algoritmo-alocacao-desenvolvedores.md` - Documentação do algoritmo
- `backlog_manager/application/use_cases/schedule/allocate_developers.py` - Implementação principal
- `backlog_manager/domain/services/developer_load_balancer.py` - Balanceamento de carga
- `backlog_manager/domain/services/backlog_sorter.py` - Ordenação topológica
- `backlog_manager/domain/services/idleness_detector.py` - Detecção de ociosidade

---

## Melhorias de Alta Prioridade

### 1. Eliminar Chamadas Redundantes ao Repositório

**Prioridade**: Alta

**Descrição**: O algoritmo executa múltiplas chamadas a `story_repository.find_all()` e `story_repository.save()` desnecessárias. Em `execute()`:
- Linha 143: `all_stories = self._story_repository.find_all()`
- Linha 192: `all_stories = self._story_repository.find_all()` (pós-ondas)
- Linha 202: `all_stories = self._story_repository.find_all()` (detecção de ociosidade)

Além disso, `_update_schedule_order_from_table()` salva cada história individualmente (N saves).

**Código problemático** (`allocate_developers.py:354-369`):
```python
def _update_schedule_order_from_table(self) -> None:
    all_stories = self._story_repository.find_all()
    for index, story in enumerate(all_stories):
        story.schedule_order = index
        self._story_repository.save(story)  # N saves individuais
```

**Proposta de Implementação**:

1. **Adicionar método `save_batch()` ao repositório** (`sqlite_story_repository.py`):
```python
def save_batch(self, stories: List[Story]) -> None:
    """Salva múltiplas histórias em uma única transação."""
    with self._connection:
        for story in stories:
            self._connection.execute(
                """UPDATE stories SET
                   developer_id = ?, start_date = ?, end_date = ?,
                   duration_in_days = ?, schedule_order = ?, updated_at = ?
                   WHERE id = ?""",
                (story.developer_id, story.start_date, story.end_date,
                 story.duration_in_days, story.schedule_order,
                 datetime.now().isoformat(), story.id)
            )
```

2. **Manter lista em memória durante execução** (`allocate_developers.py`):
```python
def execute(self) -> AllocationResult:
    # Carregar uma única vez no início
    self._stories_cache: Dict[str, Story] = {
        s.id: s for s in self._story_repository.find_all()
    }

    # ... processamento usando self._stories_cache ...

    # Salvar tudo no final
    self._story_repository.save_batch(list(self._stories_cache.values()))
```

3. **Refatorar métodos internos** para usar cache em vez de repositório:
   - `_update_schedule_order_from_table()` → opera no cache
   - `_allocate_wave()` → opera no cache
   - `_ensure_dependencies_finished()` → opera no cache

**Arquivos a modificar**:
- `backlog_manager/infrastructure/database/repositories/sqlite_story_repository.py`
- `backlog_manager/application/interfaces/repositories/story_repository.py` (interface)
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Ganhos**:
- Redução de I/O de banco de dados em ~60-70%
- Menor tempo de execução em backlogs grandes
- Redução de locks no banco SQLite

**Tradeoffs**:
- Requer implementação de `save_batch()` no repositório
- Necessita manter consistência entre lista em memória e banco
- Em caso de erro, todas as alterações são perdidas (mitigado pelo UnitOfWork)

**Testes necessários**:
- [ ] Teste unitário: `save_batch()` salva todas as histórias corretamente
- [ ] Teste unitário: Cache é populado corretamente no início
- [ ] Teste integração: Resultado final igual ao comportamento atual
- [ ] Teste performance: Medir redução de tempo com backlog de 100+ histórias

**Complexidade de Implementação**: Baixa

---

### 2. Unificar Cálculo de Dias Úteis

**Prioridade**: Alta

**Descrição**: Existem três implementações diferentes para cálculo de dias úteis:

1. `AllocateDevelopersUseCase._count_workdays()` - Não considera feriados
2. `IdlenessDetector._calculate_workday_gap()` - Não considera feriados
3. `ScheduleCalculator.add_workdays()` - Considera feriados brasileiros

Isso causa inconsistência: o cronograma considera feriados, mas a detecção de ociosidade não.

**Código problemático** (`allocate_developers.py:517-541`):
```python
def _count_workdays(self, start: date, end: date) -> int:
    # NÃO considera feriados brasileiros
    while current <= end:
        if current.weekday() < 5:  # Apenas segunda a sexta
            count += 1
```

**Proposta de Implementação**:

1. **Adicionar método `count_workdays()` ao ScheduleCalculator** (`schedule_calculator.py`):
```python
def count_workdays(self, start: date, end: date) -> int:
    """
    Conta dias úteis entre duas datas (inclusive).
    Considera fins de semana e feriados brasileiros.

    Args:
        start: Data inicial
        end: Data final

    Returns:
        Número de dias úteis no intervalo
    """
    if start > end:
        return 0

    count = 0
    current = start
    while current <= end:
        if self._is_workday(current):
            count += 1
        current += timedelta(days=1)
    return count

def _is_workday(self, d: date) -> bool:
    """Verifica se a data é dia útil (não é fim de semana nem feriado)."""
    return d.weekday() < 5 and d not in self._holidays
```

2. **Refatorar `AllocateDevelopersUseCase`** - Remover `_count_workdays()` e usar ScheduleCalculator:
```python
# Antes:
workdays = self._count_workdays(story.start_date, story.end_date)

# Depois:
workdays = self._schedule_calculator.count_workdays(story.start_date, story.end_date)
```

3. **Refatorar `IdlenessDetector`** - Injetar ScheduleCalculator:
```python
class IdlenessDetector:
    def __init__(self, schedule_calculator: ScheduleCalculator):
        self._schedule_calculator = schedule_calculator

    def _calculate_workday_gap(self, start: date, end: date) -> int:
        return self._schedule_calculator.count_workdays(start, end)
```

**Arquivos a modificar**:
- `backlog_manager/domain/services/schedule_calculator.py` - Adicionar `count_workdays()` e `_is_workday()`
- `backlog_manager/application/use_cases/schedule/allocate_developers.py` - Remover `_count_workdays()`
- `backlog_manager/domain/services/idleness_detector.py` - Injetar ScheduleCalculator
- `backlog_manager/presentation/utils/di_container.py` - Atualizar injeção de dependências

**Ganhos**:
- Consistência entre cálculos de cronograma e ociosidade
- Eliminação de código duplicado (~30 linhas)
- Correção de bug: gaps de ociosidade em feriados são reportados incorretamente

**Tradeoffs**:
- Requer refatoração do `ScheduleCalculator` para expor método de contagem
- Pode mudar warnings de ociosidade existentes (comportamento mais correto)
- IdlenessDetector passa a ter dependência do ScheduleCalculator

**Testes necessários**:
- [ ] Teste unitário: `count_workdays()` retorna 0 para intervalo inválido
- [ ] Teste unitário: `count_workdays()` exclui fins de semana
- [ ] Teste unitário: `count_workdays()` exclui feriados brasileiros
- [ ] Teste unitário: `_is_workday()` funciona corretamente
- [ ] Teste integração: Warnings de ociosidade não incluem feriados

**Complexidade de Implementação**: Baixa

---

### 3. Corrigir Inconsistência no IdlenessWarning para Deadlock

**Prioridade**: Alta

**Descrição**: O `IdlenessWarning` dataclass define atributos específicos, mas o uso em deadlock passa atributos incompatíveis:

**Definição** (`idleness_detector.py:9-15`):
```python
@dataclass
class IdlenessWarning:
    developer_id: str
    gap_days: int
    story_before_id: str
    story_after_id: str
    idle_start: date
    idle_end: date
```

**Uso problemático** (`allocate_developers.py:342-348`):
```python
deadlock_warning = IdlenessWarning(
    developer_name=f"Onda {wave}",  # Atributo errado!
    idle_period_start=None,          # Atributo errado!
    idle_period_end=None,            # Atributo errado!
    idle_days=0,                     # Atributo errado!
    message=f"Deadlock na onda..."   # Atributo errado!
)
```

**Proposta de Implementação**:

1. **Criar `DeadlockWarning`** (`idleness_detector.py` ou novo arquivo `allocation_warnings.py`):
```python
from dataclasses import dataclass
from typing import List

@dataclass
class DeadlockWarning:
    """Warning emitido quando o algoritmo detecta situação sem progresso."""
    wave: int
    unallocated_story_ids: List[str]
    message: str

    def __str__(self) -> str:
        return f"Deadlock na onda {self.wave}: {self.message}"
```

2. **Atualizar `AllocationResult`** para aceitar ambos os tipos:
```python
from typing import Union

WarningType = Union[IdlenessWarning, DeadlockWarning]

@dataclass
class AllocationResult:
    success: bool
    allocated_count: int
    warnings: List[WarningType]
    errors: List[str]
```

3. **Corrigir uso em `allocate_developers.py`**:
```python
# Antes (incorreto):
deadlock_warning = IdlenessWarning(developer_name=f"Onda {wave}", ...)

# Depois (correto):
deadlock_warning = DeadlockWarning(
    wave=wave,
    unallocated_story_ids=[s.id for s in unallocated],
    message=f"Não foi possível alocar {len(unallocated)} histórias após {MAX_ITERATIONS} iterações"
)
```

**Arquivos a modificar**:
- `backlog_manager/domain/services/idleness_detector.py` - Adicionar `DeadlockWarning`
- `backlog_manager/application/use_cases/schedule/allocate_developers.py` - Usar classe correta
- `backlog_manager/presentation/controllers/schedule_controller.py` - Tratar novo tipo de warning

**Ganhos**:
- Correção de bug de runtime (TypeError em produção)
- Type safety com mypy
- Código mais robusto
- Separação clara entre tipos de warnings

**Tradeoffs**:
- Adiciona novo dataclass ao sistema
- UI precisa tratar novo tipo de warning

**Testes necessários**:
- [ ] Teste unitário: `DeadlockWarning` criado corretamente
- [ ] Teste unitário: `AllocationResult` aceita ambos os tipos de warning
- [ ] Teste integração: Deadlock gera warning do tipo correto
- [ ] Teste UI: Warnings são exibidos corretamente na interface

**Complexidade de Implementação**: Baixa

---

### 4. Otimizar Busca de Dependências com Dicionário

**Prioridade**: Alta

**Descrição**: As buscas de dependências usam busca linear O(n) repetidamente:

**Código problemático** (`allocate_developers.py:579-581`):
```python
for dep_id in story.dependencies:
    dep_story = next((s for s in all_stories if s.id == dep_id), None)  # O(n)
```

Com N histórias e M dependências por história, a complexidade é O(N*M*N) = O(N²M).

**Proposta de Implementação**:

1. **Criar dicionário no início do método `execute()`**:
```python
def execute(self) -> AllocationResult:
    all_stories = self._story_repository.find_all()

    # Criar mapa para busca O(1)
    self._story_map: Dict[str, Story] = {story.id: story for story in all_stories}

    # Resto do algoritmo usa self._story_map
```

2. **Criar método auxiliar para buscar dependências**:
```python
def _get_dependency_stories(self, story: Story) -> List[Story]:
    """
    Retorna lista de histórias que são dependências da história fornecida.

    Args:
        story: História para buscar dependências

    Returns:
        Lista de Stories que são pré-requisitos (pode estar vazia)
    """
    dependencies = []
    for dep_id in story.dependencies:
        dep_story = self._story_map.get(dep_id)
        if dep_story:
            dependencies.append(dep_story)
        else:
            # Log warning: dependência não encontrada
            logger.warning(f"Dependência {dep_id} não encontrada para {story.id}")
    return dependencies
```

3. **Refatorar locais que fazem busca linear**:

```python
# ANTES (múltiplos locais no código):
for dep_id in story.dependencies:
    dep_story = next((s for s in all_stories if s.id == dep_id), None)
    if dep_story and dep_story.end_date:
        # ...

# DEPOIS:
for dep_story in self._get_dependency_stories(story):
    if dep_story.end_date:
        # ...
```

4. **Locais a refatorar** (buscar por `next((s for s in`):
   - `_ensure_dependencies_finished()` - linha ~580
   - `_final_dependency_check()` - linha ~620
   - `_get_latest_dependency_end_date()` - linha ~650
   - `_can_allocate_story()` - linha ~480

**Arquivos a modificar**:
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Análise de Complexidade**:

| Operação | Antes | Depois |
|----------|-------|--------|
| Buscar 1 dependência | O(N) | O(1) |
| Buscar M dependências | O(N*M) | O(M) |
| Processar N histórias com M deps cada | O(N²*M) | O(N*M) |

Para backlog com 100 histórias e média de 2 dependências:
- Antes: ~20.000 comparações
- Depois: ~200 lookups

**Ganhos**:
- Redução de complexidade de O(N²) para O(N)
- Melhoria significativa para backlogs grandes (100+ histórias)
- Código mais idiomático e legível
- Detecção de dependências inválidas (log warning)

**Tradeoffs**:
- Necessita criar dicionário no início do método (~0.1ms para 100 histórias)
- Overhead de memória: ~8KB para 100 histórias (referências)
- Dicionário precisa ser atualizado se histórias forem adicionadas durante execução

**Testes necessários**:
- [ ] Teste unitário: `_story_map` é criado corretamente
- [ ] Teste unitário: `_get_dependency_stories()` retorna histórias corretas
- [ ] Teste unitário: Dependência inexistente gera log warning
- [ ] Teste performance: Comparar tempo de execução antes/depois com 100+ histórias

**Complexidade de Implementação**: Baixa

---

## Melhorias de Média Prioridade

### 5. Priorização por Proprietário de Dependência

**Prioridade**: Média

**Objetivo**: Alterar o critério de balanceamento de carga para priorizar a continuidade do trabalho do desenvolvedor nas histórias dependentes.

**Mudança no Algoritmo de Alocação**:
- **Critério Atual**: Primeiro critério de alocação baseado em balanceamento de carga (distribuição uniforme de histórias)
- **Novo Critério**: Priorizar a alocação do desenvolvedor que trabalhou na história de origem da dependência

**Exemplo Prático**:
Quando uma história H2 depende de uma história H1:
1. Identificar o desenvolvedor que implementou H1
2. **Priorizar** este desenvolvedor para H2 (se disponível)
3. Apenas usar balanceamento de carga como critério secundário

**Proposta de Implementação Detalhada**:

1. **Criar novo método no `DeveloperLoadBalancer`** (`developer_load_balancer.py`):

```python
def get_developer_for_story(
    self,
    story: Story,
    story_map: Dict[str, Story],
    available_developers: List[int],
    all_stories: List[Story]
) -> Optional[int]:
    """
    Seleciona desenvolvedor para uma história usando critérios em ordem:
    1. Proprietário de dependência (se disponível)
    2. Balanceamento de carga (fallback)

    Args:
        story: História a ser alocada
        story_map: Mapa de ID -> Story para busca O(1)
        available_developers: IDs de desenvolvedores disponíveis no período
        all_stories: Todas as histórias (para calcular carga)

    Returns:
        ID do desenvolvedor selecionado ou None se nenhum disponível
    """
    if not available_developers:
        return None

    # Critério 1: Priorizar proprietário de dependência
    dependency_owner = self._get_dependency_owner(
        story, story_map, available_developers
    )
    if dependency_owner:
        return dependency_owner

    # Critério 2: Fallback para balanceamento de carga
    return self.get_developer_with_lowest_load(available_developers, all_stories)


def _get_dependency_owner(
    self,
    story: Story,
    story_map: Dict[str, Story],
    available_developers: List[int]
) -> Optional[int]:
    """
    Busca desenvolvedor que implementou alguma dependência da história.

    Regras:
    - Se houver múltiplas dependências, usa a primeira com desenvolvedor disponível
    - Ordem de prioridade: dependências na ordem em que aparecem na lista

    Returns:
        ID do desenvolvedor ou None se nenhum disponível
    """
    for dep_id in story.dependencies:
        dep_story = story_map.get(dep_id)
        if dep_story and dep_story.developer_id:
            if dep_story.developer_id in available_developers:
                return dep_story.developer_id
    return None
```

2. **Atualizar `AllocateDevelopersUseCase`** para usar novo método:

```python
# ANTES (allocate_developers.py):
developer_id = self._load_balancer.get_developer_with_lowest_load(
    available_developers, all_stories
)

# DEPOIS:
developer_id = self._load_balancer.get_developer_for_story(
    story=story,
    story_map=self._story_map,
    available_developers=available_developers,
    all_stories=list(self._story_map.values())
)
```

3. **Tratamento de múltiplas dependências**:

```python
def _get_dependency_owner_weighted(
    self,
    story: Story,
    story_map: Dict[str, Story],
    available_developers: List[int],
    all_stories: List[Story]
) -> Optional[int]:
    """
    Versão alternativa: considera TODAS as dependências e
    escolhe o desenvolvedor que implementou mais delas.
    """
    dev_counts: Dict[int, int] = {}

    for dep_id in story.dependencies:
        dep_story = story_map.get(dep_id)
        if dep_story and dep_story.developer_id in available_developers:
            dev_id = dep_story.developer_id
            dev_counts[dev_id] = dev_counts.get(dev_id, 0) + 1

    if not dev_counts:
        return None

    # Desenvolvedor com mais dependências implementadas
    # Desempate: menor carga atual
    max_count = max(dev_counts.values())
    candidates = [d for d, c in dev_counts.items() if c == max_count]

    if len(candidates) == 1:
        return candidates[0]

    # Desempate por carga
    return self._get_developer_with_lowest_load_from_list(candidates, all_stories)
```

**Diagrama de Decisão**:

```
┌─────────────────────────────────┐
│     História a ser alocada      │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│   Tem dependências alocadas?    │
└───────────────┬─────────────────┘
                │
        ┌───────┴───────┐
        │ Sim           │ Não
        ▼               ▼
┌───────────────┐ ┌─────────────────┐
│ Dev da dep.   │ │ Balanceamento   │
│ disponível?   │ │ de carga        │
└───────┬───────┘ └─────────────────┘
        │
  ┌─────┴─────┐
  │ Sim       │ Não
  ▼           ▼
┌───────────┐ ┌─────────────────┐
│ Alocar    │ │ Balanceamento   │
│ dev. dep. │ │ de carga        │
└───────────┘ └─────────────────┘
```

**Arquivos a modificar**:
- `backlog_manager/domain/services/developer_load_balancer.py` - Novo método
- `backlog_manager/application/use_cases/schedule/allocate_developers.py` - Usar novo método

**Ganhos**:
- Redução de overhead de transferência de conhecimento
- Maior continuidade e contexto do desenvolvedor
- Minimização de retrabalho por falta de contexto
- Histórias relacionadas tendem a ficar com o mesmo desenvolvedor

**Tradeoffs**:
- Pode causar desbalanceamento temporário de carga
- Desenvolvedor com muitas dependências pode ficar sobrecarregado
- Necessita validação de disponibilidade antes de priorizar

**Testes necessários**:
- [ ] Teste unitário: `_get_dependency_owner()` retorna dev correto quando disponível
- [ ] Teste unitário: `_get_dependency_owner()` retorna None quando dev não disponível
- [ ] Teste unitário: `get_developer_for_story()` faz fallback para balanceamento
- [ ] Teste unitário: Múltiplas dependências - escolhe primeiro disponível
- [ ] Teste integração: Histórias dependentes ficam com mesmo dev quando possível
- [ ] Teste integração: Balanceamento ainda funciona para histórias sem dependências

**Métricas para validação**:
- Percentual de histórias alocadas ao proprietário da dependência
- Distribuição de carga antes/depois da mudança
- Número de "handoffs" entre desenvolvedores em uma feature

**Complexidade de Implementação**: Média

**Pré-requisitos**:
- Melhoria 4 (dicionário para busca O(1)) deve ser implementada primeiro

---

### 6. Cache de Disponibilidade por Período

**Prioridade**: Média

**Descrição**: `_get_available_developers()` recalcula disponibilidade iterando sobre todas as histórias para cada desenvolvedor, em cada tentativa de alocação. Para N histórias e D desenvolvedores, isso é O(N*D) por tentativa.

**Proposta de Implementação**:

1. **Criar classe `DeveloperScheduleCache`**:

```python
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Set, Tuple

@dataclass
class OccupiedPeriod:
    """Período em que um desenvolvedor está ocupado."""
    start_date: date
    end_date: date
    story_id: str


class DeveloperScheduleCache:
    """
    Cache de períodos ocupados por desenvolvedor.
    Permite verificação rápida de disponibilidade.
    """

    def __init__(self):
        # developer_id -> lista de períodos ocupados (ordenada por start_date)
        self._schedules: Dict[int, List[OccupiedPeriod]] = {}

    def initialize(self, stories: List[Story]) -> None:
        """Inicializa cache a partir das histórias existentes."""
        self._schedules.clear()
        for story in stories:
            if story.developer_id and story.start_date and story.end_date:
                self.add_allocation(
                    developer_id=story.developer_id,
                    start_date=story.start_date,
                    end_date=story.end_date,
                    story_id=story.id
                )

    def add_allocation(
        self,
        developer_id: int,
        start_date: date,
        end_date: date,
        story_id: str
    ) -> None:
        """Adiciona nova alocação ao cache."""
        if developer_id not in self._schedules:
            self._schedules[developer_id] = []

        period = OccupiedPeriod(start_date, end_date, story_id)
        periods = self._schedules[developer_id]

        # Inserir mantendo ordem por start_date (busca binária)
        insert_idx = self._find_insert_position(periods, start_date)
        periods.insert(insert_idx, period)

    def is_available(
        self,
        developer_id: int,
        start_date: date,
        end_date: date
    ) -> bool:
        """
        Verifica se desenvolvedor está disponível no período.
        Complexidade: O(log K) onde K = número de alocações do dev.
        """
        if developer_id not in self._schedules:
            return True

        periods = self._schedules[developer_id]
        if not periods:
            return True

        # Busca binária para encontrar período que pode sobrepor
        idx = self._find_overlap_candidate(periods, start_date)

        # Verificar períodos adjacentes
        for i in range(max(0, idx - 1), min(len(periods), idx + 2)):
            period = periods[i]
            if self._periods_overlap(start_date, end_date, period.start_date, period.end_date):
                return False

        return True

    def get_available_developers(
        self,
        all_developer_ids: List[int],
        start_date: date,
        end_date: date
    ) -> List[int]:
        """Retorna lista de desenvolvedores disponíveis no período."""
        return [
            dev_id for dev_id in all_developer_ids
            if self.is_available(dev_id, start_date, end_date)
        ]

    @staticmethod
    def _periods_overlap(s1: date, e1: date, s2: date, e2: date) -> bool:
        """Verifica se dois períodos se sobrepõem."""
        return s1 <= e2 and s2 <= e1

    def _find_insert_position(self, periods: List[OccupiedPeriod], start: date) -> int:
        """Busca binária para posição de inserção."""
        left, right = 0, len(periods)
        while left < right:
            mid = (left + right) // 2
            if periods[mid].start_date < start:
                left = mid + 1
            else:
                right = mid
        return left

    def _find_overlap_candidate(self, periods: List[OccupiedPeriod], start: date) -> int:
        """Busca binária para candidato a sobreposição."""
        return self._find_insert_position(periods, start)
```

2. **Integrar no `AllocateDevelopersUseCase`**:

```python
def execute(self) -> AllocationResult:
    all_stories = self._story_repository.find_all()

    # Inicializar cache de disponibilidade
    self._schedule_cache = DeveloperScheduleCache()
    self._schedule_cache.initialize(all_stories)

    # ... durante alocação ...

    # Verificar disponibilidade (O(log K) em vez de O(N))
    available = self._schedule_cache.get_available_developers(
        all_developer_ids, story.start_date, story.end_date
    )

    # Após alocar, atualizar cache
    self._schedule_cache.add_allocation(
        developer_id=story.developer_id,
        start_date=story.start_date,
        end_date=story.end_date,
        story_id=story.id
    )
```

**Análise de Complexidade**:

| Operação | Antes | Depois |
|----------|-------|--------|
| Verificar 1 dev | O(N) | O(log K) |
| Verificar D devs | O(N*D) | O(D*log K) |
| Total para N histórias | O(N²*D) | O(N*D*log K) |

Onde K = média de histórias por desenvolvedor.

Para backlog com 100 histórias, 5 devs, média 20 histórias/dev:
- Antes: ~50.000 verificações
- Depois: ~2.500 verificações

**Ganhos**:
- Verificação de disponibilidade em O(log K) onde K = histórias do dev
- Significativo para times grandes (10+ devs) com backlogs extensos
- Estrutura reutilizável para outras funcionalidades

**Tradeoffs**:
- Complexidade adicional de código (~100 linhas)
- Necessita manter estrutura sincronizada
- Pode não valer a pena para backlogs pequenos (<50 histórias)
- Overhead de memória: ~1KB por desenvolvedor

**Testes necessários**:
- [ ] Teste unitário: `initialize()` popula corretamente
- [ ] Teste unitário: `is_available()` detecta sobreposição
- [ ] Teste unitário: `add_allocation()` mantém ordem
- [ ] Teste unitário: Busca binária funciona em edge cases
- [ ] Teste performance: Comparar antes/depois com 100+ histórias

**Complexidade de Implementação**: Alta

**Quando implementar**: Apenas se backlog típico > 50 histórias ou time > 5 desenvolvedores

---

### 7. Simplificar Sincronização de schedule_order

**Prioridade**: Média

**Descrição**: O método `_update_schedule_order_from_table()` sincroniza `schedule_order` com a ordem de `priority`, mas depois a alocação ordena diretamente por `priority`:

```python
# Sincroniza schedule_order (linha 131)
self._update_schedule_order_from_table()

# Mas depois ordena por priority (linha 171)
wave_stories.sort(key=lambda s: s.priority)
```

Se `schedule_order` não é usado para ordenação durante alocação, a sincronização pode ser desnecessária ou pode haver funcionalidade duplicada.

**Análise de Impacto Necessária**:

Antes de implementar, verificar todos os usos de `schedule_order`:

```bash
# Buscar usos no código
grep -r "schedule_order" backlog_manager/
```

**Locais potenciais de uso**:
1. `main_window.py` - Ordenação da tabela na UI
2. `export_to_excel.py` - Ordem no arquivo exportado
3. `sqlite_story_repository.py` - ORDER BY na query

**Proposta de Implementação**:

Atualizar `schedule_order` apenas uma vez no final da alocação:

```python
def execute(self) -> AllocationResult:
    # ... alocação ...

    # Atualizar schedule_order apenas uma vez, no final
    sorted_stories = sorted(all_stories, key=lambda s: s.priority)
    for idx, story in enumerate(sorted_stories):
        story.schedule_order = idx

    # Salvar em batch (Melhoria 1)
    self._story_repository.save_batch(all_stories)
```

**Refatoração necessária**:
1. Remover chamada a `_update_schedule_order_from_table()` no início de `execute()`
2. Adicionar atualização de `schedule_order` no final, antes do `save_batch()`
3. Verificar que UI e export continuam funcionando

**Ganhos**:
- Eliminação de N saves desnecessários no início
- Código mais simples e direto
- Menor tempo de execução

**Tradeoffs**:
- Requer análise de impacto completa antes de implementar
- Pode afetar comportamento de outras funcionalidades (UI, exports)

**Testes necessários**:
- [ ] Verificar todos os usos de `schedule_order` no código
- [ ] Teste integração: UI exibe histórias na ordem correta
- [ ] Teste integração: Export Excel mantém ordem esperada
- [ ] Teste: Remover chamada e verificar se testes existentes quebram

**Complexidade de Implementação**: Baixa (após análise de impacto)

---

### 8. Extrair Lógica de Ajuste de Datas para Método Único

**Prioridade**: Média

**Descrição**: A lógica de ajuste de datas está duplicada em três lugares:
1. `_adjust_story_dates()`
2. `_ensure_dependencies_finished()`
3. `_final_dependency_check()`

Todos seguem o mesmo padrão:
```python
new_start = self._schedule_calculator.add_workdays(base_date, offset)
if story.duration:
    new_end = self._schedule_calculator.add_workdays(new_start, story.duration - 1)
else:
    workdays = self._count_workdays(story.start_date, story.end_date)
    new_end = self._schedule_calculator.add_workdays(new_start, max(0, workdays - 1))
```

**Proposta de Implementação**:

1. **Criar método unificado** (`allocate_developers.py`):

```python
def _recalculate_story_dates(
    self,
    story: Story,
    new_start_date: date
) -> Tuple[date, date]:
    """
    Recalcula datas de início e fim de uma história.

    Mantém a duração original da história, apenas movendo
    o período para começar na nova data.

    Args:
        story: História a ter datas recalculadas
        new_start_date: Nova data de início

    Returns:
        Tupla (new_start, new_end) com as novas datas

    Raises:
        ValueError: Se história não tem duração definida
    """
    # Garantir que começa em dia útil
    adjusted_start = self._schedule_calculator.get_next_workday(new_start_date)

    # Calcular duração em dias úteis
    if story.duration_in_days:
        duration = story.duration_in_days
    elif story.start_date and story.end_date:
        duration = self._schedule_calculator.count_workdays(
            story.start_date, story.end_date
        )
    else:
        raise ValueError(f"História {story.id} não tem duração definida")

    # Calcular nova data de fim
    new_end = self._schedule_calculator.add_workdays(
        adjusted_start,
        max(0, duration - 1)
    )

    return adjusted_start, new_end


def _update_story_dates(self, story: Story, new_start: date) -> None:
    """Atualiza datas da história in-place."""
    start, end = self._recalculate_story_dates(story, new_start)
    story.start_date = start
    story.end_date = end
```

2. **Refatorar métodos existentes**:

```python
# _adjust_story_dates() - ANTES:
def _adjust_story_dates(self, story: Story, new_start: date) -> None:
    new_start = self._schedule_calculator.add_workdays(base_date, offset)
    if story.duration:
        new_end = self._schedule_calculator.add_workdays(new_start, story.duration - 1)
    # ... código duplicado ...

# _adjust_story_dates() - DEPOIS:
def _adjust_story_dates(self, story: Story, new_start: date) -> None:
    self._update_story_dates(story, new_start)
```

3. **Locais a refatorar**:
   - `_adjust_story_dates()` → usar `_update_story_dates()`
   - `_ensure_dependencies_finished()` → usar `_recalculate_story_dates()`
   - `_final_dependency_check()` → usar `_recalculate_story_dates()`

**Arquivos a modificar**:
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Ganhos**:
- Eliminação de código duplicado (~30 linhas)
- Único ponto de manutenção para cálculo de datas
- Facilita correção de bugs
- Melhor testabilidade (método isolado)

**Tradeoffs**:
- Refatoração de três métodos existentes
- Necessita garantir que todos os casos são cobertos

**Testes necessários**:
- [ ] Teste unitário: `_recalculate_story_dates()` mantém duração
- [ ] Teste unitário: Ajuste para dia útil funciona
- [ ] Teste unitário: História sem duração levanta exceção
- [ ] Teste integração: Comportamento igual ao anterior

**Complexidade de Implementação**: Baixa

---

## Melhorias de Baixa Prioridade

### 9. Mover Import para Nível de Módulo

**Prioridade**: Baixa

**Descrição**: Import de `timedelta` está dentro do método `_count_workdays()`:

```python
def _count_workdays(self, start: date, end: date) -> int:
    from datetime import timedelta  # Import dentro do método
```

**Ganhos**:
- Conformidade com PEP 8
- Micro-otimização (evita lookup em cada chamada)
- Consistência com resto do código

**Tradeoffs**: Nenhum

**Complexidade de Implementação**: Trivial

---

### 10. Adicionar Métricas de Performance

**Prioridade**: Baixa

**Descrição**: O algoritmo não registra métricas de execução (tempo total, iterações por onda, histórias processadas por segundo).

**Proposta de Implementação**:

```python
import time
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)

@dataclass
class AllocationMetrics:
    """Métricas de execução do algoritmo de alocação."""
    total_time_ms: float = 0.0
    stories_processed: int = 0
    waves_processed: int = 0
    iterations_per_wave: List[int] = field(default_factory=list)
    conflicts_resolved: int = 0
    fallback_allocations: int = 0  # Alocações por balanceamento (sem dep owner)

    def log_summary(self) -> None:
        logger.info(
            f"Alocação concluída: {self.stories_processed} histórias em "
            f"{self.total_time_ms:.1f}ms ({self.waves_processed} ondas)"
        )
        if self.iterations_per_wave:
            avg_iterations = sum(self.iterations_per_wave) / len(self.iterations_per_wave)
            logger.debug(f"Média de iterações por onda: {avg_iterations:.1f}")


class AllocateDevelopersUseCase:
    def execute(self) -> AllocationResult:
        metrics = AllocationMetrics()
        start_time = time.perf_counter()

        # ... algoritmo ...

        metrics.total_time_ms = (time.perf_counter() - start_time) * 1000
        metrics.stories_processed = len(allocated_stories)
        metrics.log_summary()

        return AllocationResult(..., metrics=metrics)
```

**Métricas a coletar**:
- Tempo total de execução (ms)
- Número de histórias processadas
- Número de ondas processadas
- Iterações por onda
- Conflitos resolvidos
- Alocações por fallback (balanceamento)

**Ganhos**:
- Visibilidade para debugging de performance
- Dados para otimizações futuras
- Monitoramento em produção

**Tradeoffs**:
- Overhead mínimo de logging (~1ms)
- Adiciona ~30 linhas de código

**Complexidade de Implementação**: Baixa

---

### 11. Tornar MAX_ITERATIONS Configurável

**Prioridade**: Baixa

**Descrição**: `MAX_ITERATIONS = 1000` é hardcoded no método `_allocate_wave()`. Para casos extremos, pode ser insuficiente ou excessivo.

**Proposta de Implementação**:

```python
# Em configuration.py ou constants.py
DEFAULT_MAX_ITERATIONS = 1000

# Em allocate_developers.py
class AllocateDevelopersUseCase:
    def __init__(
        self,
        ...,
        max_iterations: int = DEFAULT_MAX_ITERATIONS
    ):
        self._max_iterations = max_iterations

    def _allocate_wave(self, wave: int, wave_stories: List[Story]) -> ...:
        iterations = 0
        while iterations < self._max_iterations:
            # ...
```

**Ganhos**:
- Flexibilidade para diferentes cenários
- Permite ajuste sem modificar código
- Facilita testes com valores menores

**Tradeoffs**:
- Mais um parâmetro de configuração
- Valor padrão (1000) é adequado para maioria dos casos

**Complexidade de Implementação**: Trivial

---

### 12. Melhorar Detecção de Deadlock

**Prioridade**: Baixa

**Descrição**: A detecção atual usa heurística simples:
```python
if not allocation_made and len(adjusted_stories_this_iteration) == 0:
```

Isso pode falhar em edge cases onde histórias são ajustadas mas ainda não podem ser alocadas por outros motivos.

**Edge cases não detectados**:
1. Histórias ajustadas mas sem desenvolvedor disponível em nenhuma data futura
2. Loop infinito de ajustes entre duas histórias com dependência mútua indireta
3. Todos os desenvolvedores indisponíveis por conflitos cruzados

**Proposta de Implementação**:

```python
def _detect_deadlock(
    self,
    wave: int,
    iteration: int,
    unallocated: List[Story],
    previous_state: Set[Tuple[str, date]]
) -> Optional[DeadlockWarning]:
    """
    Detecta situação de deadlock usando múltiplos critérios.

    Args:
        wave: Número da onda atual
        iteration: Número da iteração atual
        unallocated: Histórias ainda não alocadas
        previous_state: Estado anterior (story_id, start_date)

    Returns:
        DeadlockWarning se deadlock detectado, None caso contrário
    """
    # Critério 1: Excedeu limite de iterações
    if iteration >= self._max_iterations:
        return DeadlockWarning(
            wave=wave,
            unallocated_story_ids=[s.id for s in unallocated],
            message=f"Limite de {self._max_iterations} iterações excedido"
        )

    # Critério 2: Estado não mudou (mesmas histórias nas mesmas datas)
    current_state = {(s.id, s.start_date) for s in unallocated}
    if current_state == previous_state:
        return DeadlockWarning(
            wave=wave,
            unallocated_story_ids=[s.id for s in unallocated],
            message="Nenhum progresso detectado: estado idêntico à iteração anterior"
        )

    # Critério 3: Nenhum desenvolvedor disponível para nenhuma história
    if self._no_developer_available_for_any(unallocated):
        return DeadlockWarning(
            wave=wave,
            unallocated_story_ids=[s.id for s in unallocated],
            message="Nenhum desenvolvedor disponível para histórias pendentes"
        )

    return None


def _no_developer_available_for_any(self, stories: List[Story]) -> bool:
    """Verifica se não há desenvolvedor disponível para nenhuma história."""
    for story in stories:
        if story.start_date and story.end_date:
            available = self._schedule_cache.get_available_developers(
                self._all_developer_ids,
                story.start_date,
                story.end_date
            )
            if available:
                return False
    return True
```

**Ganhos**:
- Detecção mais precisa de situações sem progresso
- Mensagens de erro mais informativas
- Identifica causa raiz do deadlock

**Tradeoffs**:
- Lógica mais complexa (~40 linhas adicionais)
- Overhead de comparação de estados

**Testes necessários**:
- [ ] Teste unitário: Detecta limite de iterações
- [ ] Teste unitário: Detecta estado idêntico
- [ ] Teste unitário: Detecta falta de desenvolvedores
- [ ] Teste integração: Não gera falsos positivos

**Complexidade de Implementação**: Média

---

## Resumo de Impacto

| Melhoria | Prioridade | Complexidade | Impacto Performance | Impacto Manutenibilidade |
|----------|------------|--------------|---------------------|--------------------------|
| 1. Eliminar chamadas redundantes | Alta | Baixa | +++ | ++ |
| 2. Unificar cálculo dias úteis | Alta | Baixa | + | +++ |
| 3. Corrigir IdlenessWarning | Alta | Baixa | - | +++ |
| 4. Otimizar busca dependências | Alta | Baixa | ++ | ++ |
| 5. Priorização por proprietário de dependência | Média | Média | - | ++ |
| 6. Cache de disponibilidade | Média | Alta | +++ | + |
| 7. Simplificar schedule_order | Média | Baixa | ++ | ++ |
| 8. Extrair lógica ajuste datas | Média | Baixa | - | +++ |
| 9. Mover import | Baixa | Trivial | - | + |
| 10. Métricas de performance | Baixa | Baixa | - | ++ |
| 11. MAX_ITERATIONS configurável | Baixa | Trivial | - | + |
| 12. Melhorar detecção deadlock | Baixa | Média | - | ++ |

**Legenda**: +++ = Alto, ++ = Médio, + = Baixo, - = Nenhum

---

## Ordem de Implementação Sugerida

### Fase 1: Quick Wins (1-2 dias)
1. Melhoria 3: Corrigir IdlenessWarning (bug crítico)
2. Melhoria 9: Mover import
3. Melhoria 4: Otimizar busca dependências
4. Melhoria 2: Unificar cálculo dias úteis

### Fase 2: Otimizações de I/O (2-3 dias)
5. Melhoria 1: Eliminar chamadas redundantes
6. Melhoria 7: Simplificar schedule_order

### Fase 3: Refatorações Estruturais (2-3 dias)
7. Melhoria 8: Extrair lógica ajuste datas
8. Melhoria 5: Priorização por proprietário de dependência

### Fase 4: Melhorias Incrementais (1-2 dias)
9. Melhoria 10: Métricas de performance
10. Melhoria 11: MAX_ITERATIONS configurável
11. Melhoria 12: Melhorar detecção deadlock

### Fase 5: Opcional (complexidade alta)
12. Melhoria 6: Cache de disponibilidade

---

## Dependências entre Melhorias

```
┌─────────────────────────────────────────────────────────────────┐
│                    GRAFO DE DEPENDÊNCIAS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   [1] Eliminar chamadas     [2] Unificar dias úteis             │
│   redundantes                      │                             │
│         │                          │                             │
│         │                          ▼                             │
│         │               [8] Extrair lógica datas                 │
│         │                                                        │
│         ▼                                                        │
│   [4] Dicionário busca ─────────► [5] Priorização por           │
│   dependências                     proprietário                  │
│         │                                                        │
│         │                                                        │
│         ▼                                                        │
│   [6] Cache disponibilidade                                      │
│         │                                                        │
│         ▼                                                        │
│   [12] Detecção deadlock                                         │
│                                                                  │
│                                                                  │
│   [3] Corrigir IdlenessWarning  (independente)                  │
│   [7] Simplificar schedule_order (independente - requer análise)│
│   [9] Mover import              (independente)                  │
│   [10] Métricas performance     (independente)                  │
│   [11] MAX_ITERATIONS config    (independente)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Dependências obrigatórias**:
- Melhoria 5 depende de Melhoria 4 (dicionário para busca O(1))
- Melhoria 8 depende de Melhoria 2 (método `count_workdays` unificado)
- Melhoria 12 pode usar Melhoria 6 (cache de disponibilidade)

**Melhorias independentes** (podem ser feitas em qualquer ordem):
- Melhoria 3: Corrigir IdlenessWarning
- Melhoria 7: Simplificar schedule_order
- Melhoria 9: Mover import
- Melhoria 10: Métricas de performance
- Melhoria 11: MAX_ITERATIONS configurável

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Regressão em cálculo de datas | Média | Alto | Testes de integração extensivos, comparar resultados antes/depois |
| Inconsistência no cache de histórias | Baixa | Alto | UnitOfWork garante atomicidade, testes de concorrência |
| Mudança de comportamento visível na UI | Média | Médio | Documentar mudanças, comunicar usuários, período de transição |
| Performance pior em backlogs pequenos | Baixa | Baixo | Benchmarks antes/depois, manter implementação simples para casos pequenos |
| Warnings de ociosidade diferentes | Alta | Baixo | Esperado (correção de bug), documentar nova lógica |
| Desbalanceamento por priorização de dependência | Média | Médio | Monitorar métricas de distribuição, ajustar se necessário |

**Estratégia de rollback**:
- Manter branch com código atual
- Feature flags para novas funcionalidades (opcional)
- Testes A/B com backlog real antes de deploy

---

## Checklist de Pré-requisitos

Antes de iniciar a implementação:

### Ambiente
- [ ] Branch de feature criado a partir de main
- [ ] Ambiente de desenvolvimento configurado
- [ ] Testes existentes passando (baseline)

### Documentação
- [ ] CLAUDE.md atualizado com novas estruturas
- [ ] Comentários em código existente entendidos

### Dados de Teste
- [ ] Backlog de teste com 50+ histórias
- [ ] Backlog de teste com dependências complexas
- [ ] Backlog de teste com múltiplos desenvolvedores

### Ferramentas
- [ ] Coverage configurado para novas classes
- [ ] Benchmark script para medir performance

---

## Considerações Finais

As melhorias propostas mantêm **100% das funcionalidades existentes**:
- Processamento por ondas
- Respeito a dependências
- Verificação de disponibilidade
- Balanceamento de carga
- Detecção de ociosidade
- Detecção de deadlock

O foco é em:
- **Correção de bugs** (IdlenessWarning incompatível)
- **Redução de complexidade** (eliminação de código duplicado)
- **Melhoria de performance** (menos I/O, busca O(1))
- **Manutenibilidade** (código mais limpo e testável)
- **Continuidade de conhecimento** (priorização por proprietário de dependência)

---

**Data**: 2025-12-25
**Versão**: 2.0 - Detalhamento completo com propostas de implementação
