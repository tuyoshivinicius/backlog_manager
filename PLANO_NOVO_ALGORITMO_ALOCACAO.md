# Plano: Novo Algoritmo de Alocação de Desenvolvedores

## 🎯 Objetivo

Reformular completamente o algoritmo de alocação de desenvolvedores para:
- Processar histórias por ordem de `Início` (data)
- Ajustar dinamicamente a data de início quando não há dev disponível
- Usar incremento linear de dias nas tentativas
- Priorizar retorno a histórias pendentes
- Manter balanceamento de carga entre desenvolvedores

---

## 📊 Análise do Algoritmo Atual

### Implementação Existente

**Arquivo:** `allocate_developers.py`

**Características atuais:**
- ✅ Multi-ciclo (máx 100 ciclos)
- ✅ Balanceamento de carga (menor número de histórias)
- ✅ Detecção e minimização de ociosidade
- ✅ Pull de histórias não alocadas
- ✅ Realocação dinâmica de histórias já alocadas
- ❌ **NÃO ordena por data de início**
- ❌ **NÃO ajusta data de início quando não há dev disponível**
- ❌ **NÃO usa fila de pendentes com prioridade**
- ❌ **NÃO usa incremento linear**

**Fluxo atual:**
1. Busca histórias não alocadas (qualquer ordem)
2. Para cada história:
   - Seleciona melhor desenvolvedor (balanceamento + ociosidade)
   - Se nenhum disponível: ajusta datas do dev
   - Aloca imediatamente
3. Repete até alocar todas ou atingir limite

**Problema:** Não considera ordem temporal das histórias, pode criar gaps desnecessários

---

## 🆕 Especificação do Novo Algoritmo

### Diferenças Principais

| Aspecto | Algoritmo Atual | Novo Algoritmo |
|---------|----------------|----------------|
| **Ordenação** | Não ordena | **Ordena por Início ascendente** |
| **Sem dev disponível** | Ajusta datas do dev | **Ajusta data da história (+1 dia)** |
| **Fila de pendentes** | Não existe | **Fila com prioridade** |
| **Incremento** | Fixo (busca melhor fit) | **Linear (1, 2, 3, 4...)** |
| **Critério de parada** | Deadlock ou max ciclos | **Todas alocadas ou max tentativas** |

---

## 🏗️ Arquitetura da Solução

### Estruturas de Dados Necessárias

#### 1. **PendingStory** (Nova classe)
```python
@dataclass
class PendingStory:
    """Representa uma história pendente de alocação."""
    story: Story
    attempts: int = 0  # Número de tentativas de alocação

    def next_increment(self) -> int:
        """Calcula próximo incremento linear."""
        if self.attempts == 0:
            return 1
        return self.attempts + 1
```

#### 2. **AllocationQueue** (Nova classe auxiliar)
```python
class AllocationQueue:
    """Fila de histórias pendentes de alocação."""

    def __init__(self):
        self._pending: List[PendingStory] = []

    def add(self, story: Story, attempts: int = 0) -> None:
        """Adiciona história à fila de pendentes."""
        self._pending.append(PendingStory(story, attempts))

    def pop_next(self) -> Optional[PendingStory]:
        """Remove e retorna próxima história pendente."""
        if not self._pending:
            return None
        return self._pending.pop(0)

    def is_empty(self) -> bool:
        """Verifica se fila está vazia."""
        return len(self._pending) == 0

    def size(self) -> int:
        """Retorna tamanho da fila."""
        return len(self._pending)
```

---

## 🔄 Novo Fluxo do Algoritmo

### Pseudocódigo Detalhado

```pseudo
FUNÇÃO allocate_developers():
    # 1. INICIALIZAÇÃO
    stories = buscar_todas_historias()
    developers = buscar_todos_desenvolvedores()

    # Filtrar histórias elegíveis (com datas e story points)
    eligible_stories = [s for s in stories if s.tem_datas() and s.tem_story_point()]

    # ORDENAR por data de início (ASCENDENTE)
    eligible_stories.ordenar_por(inicio, ascendente)

    # Criar fila de pendentes
    pending_queue = AllocationQueue()

    # 2. ITERAÇÃO PRINCIPAL
    allocated_count = 0
    max_iterations = 1000  # Evitar loop infinito
    iteration = 0

    ENQUANTO (tem_historias_nao_alocadas() OR not pending_queue.is_empty()) AND iteration < max_iterations:
        iteration += 1

        # **PRIORIDADE 1: Processar fila de pendentes PRIMEIRO**
        pending_story = pending_queue.pop_next()

        SE pending_story != None:
            story = pending_story.story
            attempts = pending_story.attempts
        SENÃO:
            # **PRIORIDADE 2: Pegar próxima história não alocada (ordem de início)**
            story = pegar_proxima_nao_alocada(eligible_stories)
            SE story == None:
                BREAK  # Todas alocadas
            attempts = 0

        # 3. TENTAR ALOCAR DESENVOLVEDOR
        available_devs = buscar_devs_disponiveis(story.inicio, story.fim)

        SE available_devs.is_empty():
            # **NÃO HÁ DEV DISPONÍVEL → AJUSTAR DATA DA HISTÓRIA**

            # Calcular incremento linear
            increment = calcular_incremento_linear(attempts)

            # Ajustar data de início
            story.inicio += increment (dias úteis)

            # Recalcular data de fim
            story.fim = calcular_data_fim(story.inicio, story.duracao)

            # Incrementar tentativas
            attempts += 1

            # Adicionar de volta à fila de pendentes
            pending_queue.add(story, attempts)

            # Salvar alteração de data
            save(story)

            CONTINUAR  # Próxima iteração

        SENÃO:
            # **HÁ DEV DISPONÍVEL → ALOCAR**

            # Ordenar devs por balanceamento + alfabético
            available_devs = ordenar_desenvolvedores(available_devs, stories)

            # Selecionar primeiro (menos histórias)
            selected_dev = available_devs[0]

            # Alocar
            story.developer_id = selected_dev.id
            save(story)

            allocated_count += 1

    # 4. RETORNAR RESULTADOS
    warnings = detectar_ociosidade(stories)
    RETORNAR (allocated_count, warnings)


FUNÇÃO ordenar_desenvolvedores(devs, all_stories):
    """
    Ordena desenvolvedores por:
    1. Menor número de histórias alocadas
    2. Ordem alfabética (nome)
    """

    # Contar histórias por dev
    load_count = {}
    PARA cada dev in devs:
        count = contar_historias_alocadas(dev, all_stories)
        load_count[dev.id] = count

    # Ordenar por carga + alfabético
    devs_ordenados = sorted(
        devs,
        key=lambda d: (load_count[d.id], d.name)
    )

    RETORNAR devs_ordenados


FUNÇÃO calcular_incremento_linear(attempts):
    """
    Calcula incremento linear de dias.

    attempts=0 → +1 dia
    attempts=1 → +2 dias
    attempts=2 → +4 dias
    attempts=3 → +8 dias
    ...
    """
    SE attempts == 0:
        RETORNAR 1
    SENÃO:
        RETORNAR attempts + 1


FUNÇÃO buscar_devs_disponiveis(start_date, end_date):
    """
    Busca desenvolvedores disponíveis no período.

    Um dev está disponível se NÃO tem histórias
    com sobreposição de período.
    """
    available = []

    PARA cada dev in developers:
        dev_stories = buscar_historias_do_dev(dev)

        has_overlap = False
        PARA cada story in dev_stories:
            SE periodos_se_sobrepoe(story.inicio, story.fim, start_date, end_date):
                has_overlap = True
                BREAK

        SE not has_overlap:
            available.append(dev)

    RETORNAR available
```

---

## 📁 Arquivos a Modificar

### 1. **`allocate_developers.py`** (Modificação COMPLETA)

**Localização:** `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Mudanças principais:**
- ✅ Remover lógica de multi-ciclo com pull/realocação
- ✅ Adicionar ordenação por `start_date`
- ✅ Implementar `AllocationQueue` e `PendingStory`
- ✅ Implementar incremento linear
- ✅ Ajustar data da história (não do dev) quando não há disponibilidade
- ✅ Priorizar fila de pendentes

**Novo método execute():**
```python
def execute(self) -> Tuple[int, List[IdlenessWarning]]:
    """
    Aloca desenvolvedores usando novo algoritmo baseado em ordem de início.

    **NOVO ALGORITMO:**
    1. Ordena histórias por data de início (ascendente)
    2. Mantém fila de histórias pendentes
    3. Prioriza retorno a histórias pendentes
    4. Ajusta data de início da história quando não há dev disponível
    5. Usa incremento linear nas tentativas (1, 2, 3, 4...)
    6. Balanceia carga entre desenvolvedores

    Returns:
        Tupla (total_alocado, lista_de_warnings)

    Raises:
        NoDevelopersAvailableException: Se não há desenvolvedores
    """
    # Implementação conforme pseudocódigo acima
```

**Novos métodos auxiliares:**
```python
def _get_next_unallocated_story(
    self,
    stories: List[Story]
) -> Optional[Story]:
    """Retorna próxima história não alocada na ordem de início."""

def _get_available_developers(
    self,
    start_date: date,
    end_date: date,
    all_stories: List[Story],
    developers: List[Developer]
) -> List[Developer]:
    """Retorna desenvolvedores disponíveis no período."""

def _sort_developers_by_load(
    self,
    developers: List[Developer],
    all_stories: List[Story]
) -> List[Developer]:
    """Ordena devs por carga (menor) + ordem alfabética."""

def _calculate_exponential_increment(
    self,
    attempts: int
) -> int:
    """Calcula incremento linear: 2^attempts (mínimo 1)."""

def _adjust_story_dates(
    self,
    story: Story,
    days_to_add: int,
    config: Configuration
) -> None:
    """Ajusta datas da história adicionando dias úteis."""
```

### 2. **`developer_load_balancer.py`** (Adicionar método)

**Localização:** `backlog_manager/domain/services/developer_load_balancer.py`

**Adicionar método:**
```python
@staticmethod
def sort_by_load_and_name(
    developers: List[Developer],
    all_stories: List[Story]
) -> List[Developer]:
    """
    Ordena desenvolvedores por:
    1. Menor número de histórias
    2. Ordem alfabética (nome)

    Args:
        developers: Lista de desenvolvedores
        all_stories: Todas as histórias

    Returns:
        Lista ordenada de desenvolvedores
    """
    load_count = DeveloperLoadBalancer._count_stories_per_developer(
        developers, all_stories
    )

    # Ordenar por carga + nome alfabético
    sorted_devs = sorted(
        developers,
        key=lambda d: (load_count.get(d.id, 0), d.name.lower())
    )

    return sorted_devs
```

### 3. **`schedule_calculator.py`** (Possivelmente usar método existente)

**Verificar se existe método para adicionar dias úteis:**
- Se sim: reutilizar
- Se não: adicionar método `add_workdays(start_date: date, days: int) -> date`

---

## 🧪 Cenários de Teste

### Cenário 1: Histórias em Ordem, Devs Disponíveis

**Setup:**
- 3 histórias: H1 (início: 01/01), H2 (início: 05/01), H3 (início: 10/01)
- 2 desenvolvedores: Dev1, Dev2
- Todos disponíveis

**Resultado Esperado:**
- H1 → Dev1 (menor carga)
- H2 → Dev2 (menor carga)
- H3 → Dev1 (menor carga)

**Critérios:**
- ✅ Processadas em ordem: H1, H2, H3
- ✅ Balanceamento: 2 para Dev1, 1 para Dev2
- ✅ Sem ajuste de datas

---

### Cenário 2: Dev Indisponível → Ajuste de Data

**Setup:**
- 2 histórias: H1 (início: 01/01, duração: 10 dias), H2 (início: 03/01, duração: 5 dias)
- 1 desenvolvedor: Dev1

**Fluxo Esperado:**
1. H1 alocada para Dev1 (01/01 - 10/01)
2. H2 tenta alocar Dev1, mas está ocupado (01/01 - 10/01)
3. H2.início ajustado: 03/01 → 04/01 (+1 dia)
4. H2 ainda não pode ser alocada (Dev1 ocupado até 10/01)
5. H2.início ajustado: 04/01 → 06/01 (+2 dias)
6. Continua até H2.início = 11/01
7. H2 alocada para Dev1 (11/01 - 18/01)

**Critérios:**
- ✅ H1 não afetada
- ✅ H2 data ajustada dinamicamente
- ✅ Incremento linear: +1, +2, +4, +8...
- ✅ H2 eventualmente alocada

---

### Cenário 3: Fila de Pendentes com Prioridade

**Setup:**
- 4 histórias: H1 (01/01), H2 (02/01), H3 (03/01), H4 (04/01)
- 1 desenvolvedor: Dev1 (ocup até 05/01)

**Fluxo Esperado:**
1. H1 não alocada (Dev1 ocupado) → ajusta +1, vai para fila pendentes
2. **PRIORIDADE:** H1 tentada novamente (antes de H2)
3. H1 ainda não pode → ajusta +2, vai para fila
4. **PRIORIDADE:** H1 tentada novamente
5. Eventualmente H1 é alocada
6. Então processa H2, H3, H4

**Critérios:**
- ✅ H1 tem múltiplas tentativas antes de processar H2
- ✅ Fila de pendentes respeitada
- ✅ Todas eventualmente alocadas

---

### Cenário 4: Ordenação Alfabética em Empate de Carga

**Setup:**
- 1 história: H1
- 3 desenvolvedores: "Carlos", "Ana", "Bruno" (nenhum com histórias)

**Resultado Esperado:**
- H1 → Ana (primeiro alfabeticamente)

**Critérios:**
- ✅ Desempate por ordem alfabética
- ✅ Ana selecionada

---

## 🔧 Detalhes de Implementação

### Incremento Linear de Dias

```python
def _calculate_exponential_increment(self, attempts: int) -> int:
    """
    Calcula incremento linear de dias.

    Args:
        attempts: Número de tentativas anteriores

    Returns:
        Número de dias a incrementar

    Examples:
        >>> _calculate_exponential_increment(0)
        1
        >>> _calculate_exponential_increment(1)
        2
        >>> _calculate_exponential_increment(2)
        4
        >>> _calculate_exponential_increment(3)
        8
    """
    if attempts == 0:
        return 1
    return attempts + 1
```

### Ajuste de Datas (Dias Úteis)

```python
def _adjust_story_dates(
    self,
    story: Story,
    days_to_add: int,
    config: Configuration
) -> None:
    """
    Ajusta datas da história adicionando dias ÚTEIS.

    Args:
        story: História a ajustar
        days_to_add: Número de dias úteis a adicionar
        config: Configuração (para calcular duração)
    """
    # Usar método do ScheduleCalculator para adicionar dias úteis
    new_start = self._schedule_calculator.add_workdays(
        story.start_date,
        days_to_add
    )

    # Recalcular data de fim mantendo duração
    new_end = self._schedule_calculator.calculate_end_date(
        new_start,
        story.duration,
        config
    )

    story.start_date = new_start
    story.end_date = new_end
```

**⚠️ IMPORTANTE:** Verificar se `ScheduleCalculator` tem método `add_workdays()`. Se não, criar.

### Ordenação de Histórias por Data de Início

```python
# No início do execute()
eligible_stories = [
    s for s in all_stories
    if s.developer_id is None
    and s.start_date is not None
    and s.end_date is not None
    and s.story_point is not None
]

# ORDENAR por data de início (ascendente)
eligible_stories.sort(key=lambda s: s.start_date)
```

### Verificação de Disponibilidade de Desenvolvedor

```python
def _get_available_developers(
    self,
    start_date: date,
    end_date: date,
    all_stories: List[Story],
    developers: List[Developer]
) -> List[Developer]:
    """
    Retorna desenvolvedores disponíveis no período.

    Um desenvolvedor está disponível se NÃO tem histórias
    alocadas com período sobreposto.
    """
    available = []

    for dev in developers:
        # Buscar histórias deste desenvolvedor
        dev_stories = [
            s for s in all_stories
            if s.developer_id == dev.id
            and s.start_date is not None
            and s.end_date is not None
        ]

        # Verificar se há sobreposição
        has_overlap = False
        for story in dev_stories:
            if self._periods_overlap(
                start_date, end_date,
                story.start_date, story.end_date
            ):
                has_overlap = True
                break

        if not has_overlap:
            available.append(dev)

    return available

def _periods_overlap(
    self,
    start1: date,
    end1: date,
    start2: date,
    end2: date
) -> bool:
    """Verifica se dois períodos se sobrepõem."""
    return start1 <= end2 and start2 <= end1
```

---

## 📋 Checklist de Implementação

### Fase 1: Preparação (1h)
- [ ] Ler e entender código atual de `allocate_developers.py`
- [ ] Ler `developer_load_balancer.py` e `schedule_calculator.py`
- [ ] Identificar métodos reutilizáveis
- [ ] Verificar se `add_workdays()` existe em ScheduleCalculator

### Fase 2: Estruturas Auxiliares (1h)
- [ ] Criar classe `PendingStory` (dataclass)
- [ ] Criar classe `AllocationQueue`
- [ ] Adicionar testes unitários para AllocationQueue

### Fase 3: Modificar DeveloperLoadBalancer (30min)
- [ ] Adicionar método `sort_by_load_and_name()`
- [ ] Testar ordenação (carga + alfabética)

### Fase 4: Modificar ScheduleCalculator (30min - se necessário)
- [ ] Verificar se `add_workdays()` existe
- [ ] Se não: implementar método
- [ ] Testar adição de dias úteis

### Fase 5: Reescrever AllocateDevelopersUseCase (4h)
- [ ] Backup do código atual
- [ ] Implementar novo método `execute()`
- [ ] Implementar `_get_next_unallocated_story()`
- [ ] Implementar `_get_available_developers()`
- [ ] Implementar `_sort_developers_by_load()`
- [ ] Implementar `_calculate_exponential_increment()`
- [ ] Implementar `_adjust_story_dates()`
- [ ] Implementar `_periods_overlap()`
- [ ] Remover métodos antigos (pull, reallocate, etc.)

### Fase 6: Testes (2h)
- [ ] Testar Cenário 1: Histórias em ordem, devs disponíveis
- [ ] Testar Cenário 2: Dev indisponível → ajuste de data
- [ ] Testar Cenário 3: Fila de pendentes
- [ ] Testar Cenário 4: Ordenação alfabética
- [ ] Testar edge cases (1 dev, muitas histórias)
- [ ] Testar com dados reais do sistema

### Fase 7: Documentação e Refinamento (1h)
- [ ] Atualizar docstrings
- [ ] Adicionar comentários no código
- [ ] Atualizar documentação do projeto
- [ ] Verificar performance (< 5s para 100 histórias)

---

## ⚠️ Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Loop infinito (história nunca alocada) | Média | Alto | Limite de iterações (1000) + log de debug |
| Performance ruim com muitas histórias | Baixa | Médio | Otimizar busca de devs disponíveis (cache) |
| Incremento linear muito agressivo | Baixa | Médio | Adicionar limite máximo de dias (+30 dias) |
| Histórias fora de ordem visual | Baixa | Baixo | Garantido: apenas ordenação interna |
| Deadlock (nenhuma história alocada) | Baixa | Alto | Detectar deadlock e abortar com erro claro |

---

## 🎯 Critérios de Sucesso

### Funcionais
- ✅ Histórias processadas em ordem de `Início`
- ✅ Backlog visual NÃO reordenado
- ✅ Desenvolvedores ordenados por carga + alfabético
- ✅ Data de início ajustada quando não há dev disponível
- ✅ Incremento linear funcionando (1, 2, 3, 4...)
- ✅ Fila de pendentes respeitada (prioridade)
- ✅ TODAS as histórias eventualmente alocadas

### Não-Funcionais
- ✅ Performance: < 5 segundos para 100 histórias
- ✅ Código limpo e bem documentado
- ✅ Sem loops infinitos
- ✅ Logs claros de debug

---

## 📊 Comparação: Antes vs Depois

| Aspecto | Algoritmo Atual | Novo Algoritmo | Benefício |
|---------|----------------|----------------|-----------|
| **Ordem** | Aleatória | Por data de início | Cronograma mais realista |
| **Dev indisponível** | Ajusta datas do dev | Adia história | Respeita agenda existente |
| **Complexidade** | Alta (pull + realocate) | Média (incremento + fila) | Mais simples de entender |
| **Previsibilidade** | Baixa (realocações) | Alta (ordem fixa) | Mais determinístico |
| **Ociosidade** | Minimiza ativamente | Aceita ociosidade | Trade-off consciente |

---

## 📝 Notas Adicionais

### Por que Remover Pull e Realocate?

O algoritmo atual tenta **minimizar ociosidade** através de pull e realocação dinâmica.
O novo algoritmo **aceita ociosidade** em favor de:
- ✅ Simplicidade
- ✅ Previsibilidade
- ✅ Respeito à ordem temporal
- ✅ Menos mudanças nas datas já calculadas

### Limitação do Incremento Linear

Para evitar que histórias sejam adiadas indefinidamente, considerar:
- Limite máximo de dias a adicionar por tentativa (ex: +30 dias)
- Ou limite total de tentativas (ex: máx 10 tentativas)

```python
def _calculate_exponential_increment(self, attempts: int) -> int:
    increment = 1 if attempts == 0 else attempts + 1
    return min(increment, 30)  # Máx +30 dias por vez
```

---

## 🚀 Estimativa

- **Complexidade:** Alta (reescrita completa)
- **Story Points:** 13
- **Tempo Estimado:** 10-12 horas
  - Preparação: 1h
  - Estruturas auxiliares: 1h
  - Load balancer: 30min
  - Schedule calculator: 30min
  - Use case principal: 4h
  - Testes: 2h
  - Documentação: 1h
  - Buffer: 1h

---

## 📚 Referências

- Arquivo atual: `allocate_developers.py`
- Serviços de domínio: `developer_load_balancer.py`, `schedule_calculator.py`
- Plano anterior: `PLANO_REVISAO_CRONOGRAMA_ALOCACAO.md`
- Especificação do usuário (mensagem atual)
