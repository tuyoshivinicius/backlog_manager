# Plano de Investigação: Ociosidade Máxima não Respeitada no Balanceamento de Carga

> **Problema Reportado:** Quando a alocação é configurada por balanceamento de carga, a regra de ociosidade máxima (`max_idle_days`) não está sendo respeitada.
>
> **Data:** 2025-12-26

---

## 1. Hipóteses Iniciais

| # | Hipótese | Probabilidade | Como Verificar |
|---|----------|---------------|----------------|
| H1 | O filtro de ociosidade não está sendo aplicado no critério LOAD_BALANCING | Alta | Revisar código de `get_developer_for_story()` |
| H2 | O parâmetro `current_wave` não está sendo passado corretamente | Média | Verificar chamada em `_allocate_wave()` |
| H3 | A lógica de `_filter_developers_by_idle_threshold()` tem bug | Média | Testar com dados específicos |
| H4 | O fallback para "menor ociosidade" está sempre sendo usado | Média | Adicionar logs e verificar |
| H5 | A configuração `max_idle_days` não está chegando ao load balancer | Baixa | Verificar fluxo de dados |

---

## 2. Passos de Investigação

### Fase 1: Análise de Código

#### 1.1 Verificar fluxo em `get_developer_for_story()`

**Arquivo:** `backlog_manager/domain/services/developer_load_balancer.py`

**Perguntas:**
- O filtro de ociosidade é aplicado ANTES do critério de alocação?
- O critério LOAD_BALANCING respeita a lista `candidates` filtrada?
- O fallback está funcionando corretamente?

**Código atual (linhas 386-430):**
```python
if new_story_start_date is not None and max_idle_days is not None:
    within_threshold, idle_days_map = DeveloperLoadBalancer._filter_developers_by_idle_threshold(
        available_developers, story_map, new_story_start_date, max_idle_days, current_wave
    )

    if within_threshold:
        candidates = within_threshold  # <-- Deveria usar só estes
    else:
        # Fallback: usar o desenvolvedor com menor ociosidade
        least_idle_dev = min(...)
        return least_idle_dev  # <-- Retorna direto, não passa pelo balanceamento
```

**Possível problema:** Se `within_threshold` está vazio, o fallback retorna direto sem considerar o balanceamento.

#### 1.2 Verificar chamada em `_allocate_wave()`

**Arquivo:** `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Verificar:**
- `max_idle_days` está sendo passado?
- `current_wave` está sendo passado?
- Os valores estão corretos?

---

### Fase 2: Adicionar Logs de Debug

#### 2.1 Logs em `_filter_developers_by_idle_threshold()`

```python
logger.debug(f"Filtrando devs por ociosidade: max_idle_days={max_idle_days}, wave={current_wave}")
logger.debug(f"Desenvolvedores disponíveis: {[d.id for d in developers]}")
logger.debug(f"Idle days por dev: {idle_days_map}")
logger.debug(f"Devs dentro do limite: {[d.id for d in within_threshold]}")
```

#### 2.2 Logs em `get_developer_for_story()`

```python
logger.debug(f"Selecionando dev para {story.id}: criteria={allocation_criteria}, wave={current_wave}")
logger.debug(f"max_idle_days={max_idle_days}, start_date={new_story_start_date}")
logger.debug(f"Candidatos após filtro: {len(candidates)}")
logger.debug(f"Dev selecionado: {selected_dev.id if selected_dev else None}")
```

---

### Fase 3: Testes Específicos

#### 3.1 Cenário de Teste

```
Configuração:
- max_idle_days = 3
- allocation_criteria = LOAD_BALANCING
- 5 desenvolvedores (AA, BB, CC, DD, EE)

Onda 1:
- Story S1 (5 SP) → Dev AA (dias 1-4)
- Story S2 (5 SP) → Dev BB (dias 1-4)
- Story S3 (5 SP) → Dev CC (dias 1-4)
- Story S4 (5 SP) → Dev AA (dias 5-8) ← AA tem 0 dias ocioso
- Story S5 (5 SP) → Quem deve receber?

Expectativa:
- S5 deve ir para BB ou CC (0 dias ociosos)
- NÃO deve ir para DD ou EE (que têm histórico vazio na onda = 0 dias)
```

#### 3.2 Teste Unitário a Criar

```python
def test_load_balancing_respects_max_idle_days():
    """Verifica que balanceamento de carga respeita limite de ociosidade."""
    # Arrange: 3 devs, 1 já com história terminada há 5 dias
    # Act: Alocar nova história com max_idle_days=3
    # Assert: Dev com ociosidade > 3 não deve ser escolhido
```

---

### Fase 4: Análise do Fluxo Completo

```
AllocateDevelopersUseCase.execute()
    │
    ├── Lê config.max_idle_days ─────────────────────┐
    │                                                 │
    └── Para cada onda:                               │
        └── _allocate_wave(wave, ...)                 │
            │                                         │
            └── Para cada história não alocada:       │
                │                                     │
                └── _load_balancer.get_developer_for_story(
                        story,
                        story_map,
                        available_devs,
                        all_stories,
                        allocation_criteria=LOAD_BALANCING,
                        new_story_start_date=story.start_date,
                        max_idle_days=self._max_idle_days,  ◄── Valor correto?
                        current_wave=wave,                   ◄── Valor correto?
                    )
                    │
                    └── _filter_developers_by_idle_threshold()
                        │
                        └── _get_developer_last_allocation_before(
                                dev.id, story_map, before_date, current_wave
                            )
                            │
                            └── Filtra histórias da mesma onda ◄── Problema aqui?
```

---

## 3. Possíveis Causas Identificadas

### Causa 1: Filtro por onda está excluindo todas as histórias

Se `current_wave` é passado, o método `_get_developer_last_allocation_before()` só considera histórias **da mesma onda**.

**Problema:** Se o desenvolvedor só tem histórias de **ondas anteriores**, ele aparece como "sem alocações anteriores" (idle_days = 0), mesmo tendo trabalhado recentemente.

**Verificação:**
```python
# Em _get_developer_last_allocation_before(), linha 262-267:
dev_stories = [
    story for story in story_map.values()
    if story.developer_id == developer_id
    and story.end_date is not None
    and story.end_date < before_date
    and (current_wave is None or story.wave == current_wave)  # ← ESTE FILTRO!
]
```

**Se o dev só tem histórias de ondas anteriores, `dev_stories` fica vazio, e idle_days = 0.**

### Causa 2: O conceito de "ociosidade dentro da onda" pode estar errado

Se estamos na onda 3 e o desenvolvedor só trabalhou nas ondas 1 e 2:
- Com o filtro por onda: idle_days = 0 (nenhuma história na onda 3)
- Sem o filtro: idle_days = X dias desde a última história

**Questão conceitual:** O que significa "ociosidade máxima dentro da onda"?

1. **Interpretação A:** Ociosidade desde a última história DO DESENVOLVEDOR na onda atual
2. **Interpretação B:** Ociosidade desde a última história DO DESENVOLVEDOR (qualquer onda)

---

## 4. Proposta de Correção (se confirmado)

### Opção A: Remover filtro por onda no cálculo de ociosidade para seleção

O filtro por onda faz sentido para **detecção de warnings**, mas talvez não para **seleção de desenvolvedor**.

```python
# Em get_developer_for_story(), NÃO passar current_wave para o filtro:
within_threshold, idle_days_map = DeveloperLoadBalancer._filter_developers_by_idle_threshold(
    available_developers, story_map, new_story_start_date, max_idle_days,
    current_wave=None  # ← Considerar todas as histórias do dev
)
```

### Opção B: Mudar a lógica para considerar "desde última atividade"

O max_idle_days deveria considerar a última história do desenvolvedor, independente da onda.

---

## 5. Checklist de Investigação

- [ ] Verificar valor de `max_idle_days` chegando em `get_developer_for_story()`
- [ ] Verificar valor de `current_wave` passado
- [ ] Verificar resultado de `_filter_developers_by_idle_threshold()`
- [ ] Verificar se `within_threshold` está ficando vazio
- [ ] Verificar se o fallback está sendo acionado sempre
- [ ] Verificar se o filtro por onda está excluindo histórias válidas
- [ ] Criar teste unitário reproduzindo o problema
- [ ] Confirmar comportamento esperado com o usuário

---

## 6. Próximos Passos

1. **Imediato:** Adicionar logs de debug nos pontos críticos
2. **Executar:** Rodar alocação e analisar logs
3. **Confirmar:** Identificar causa raiz
4. **Corrigir:** Implementar correção baseada na causa identificada
5. **Testar:** Validar correção com testes automatizados

---

**Status:** ✅ CAUSA RAIZ IDENTIFICADA

---

## 7. Análise do Código Real

### 7.1 Fluxo Confirmado

Em `allocate_developers.py` linha 385-394:
```python
selected_dev = self._load_balancer.get_developer_for_story(
    story,
    self._story_map,
    available_devs,
    all_stories,
    allocation_criteria=self._allocation_criteria,
    new_story_start_date=story.start_date,
    max_idle_days=self._max_idle_days,  # ← Valor passado corretamente
    current_wave=wave,                   # ← Onda passada corretamente
)
```

✅ **H2 e H5 descartadas:** Os parâmetros estão sendo passados corretamente.

### 7.2 Problema Identificado em `_filter_developers_by_idle_threshold()`

**Arquivo:** `developer_load_balancer.py`, linhas 300-351

```python
@staticmethod
def _filter_developers_by_idle_threshold(..., current_wave: Optional[int] = None):
    for dev in developers:
        # Buscar última alocação que termina ANTES da nova história (na mesma onda)
        last_allocation = DeveloperLoadBalancer._get_developer_last_allocation_before(
            dev.id, story_map, new_story_start_date, current_wave  # ← Filtra por onda
        )

        if last_allocation is None:
            # Desenvolvedor sem alocações anteriores à nova história nesta onda
            idle_days_map[dev.id] = 0      # ← PROBLEMA: considera 0 dias ocioso!
            within_threshold.append(dev)    # ← Sempre passa no filtro!
        else:
            # Calcula ociosidade normalmente
            idle_days = DeveloperLoadBalancer._calculate_idle_days(...)
            if idle_days <= max_idle_days:
                within_threshold.append(dev)
```

### 7.3 Causa Raiz Confirmada

**PROBLEMA:** Quando um desenvolvedor **não tem histórias na onda atual**, ele é considerado com **0 dias ociosos**.

**Consequência:**
1. Na primeira história de cada onda, TODOS os desenvolvedores têm `last_allocation = None`
2. Todos recebem `idle_days = 0`
3. Todos passam no filtro `within_threshold`
4. O critério `max_idle_days` é completamente ignorado
5. O balanceamento de carga escolhe entre TODOS, não apenas os "menos ociosos"

### 7.4 Cenário de Reprodução

```
Configuração:
- max_idle_days = 3
- allocation_criteria = LOAD_BALANCING
- 3 desenvolvedores: Ana, Bruno, Carlos

Estado antes da onda 3:
- Ana: última história na onda 2, terminou há 10 dias úteis
- Bruno: última história na onda 2, terminou há 5 dias úteis
- Carlos: nunca teve histórias

Processando primeira história da onda 3 (S1):
1. _filter_developers_by_idle_threshold() é chamado com current_wave=3
2. Para cada dev, chama _get_developer_last_allocation_before(..., current_wave=3)
3. NENHUM dev tem histórias na onda 3 → last_allocation = None para todos
4. idle_days_map = {Ana: 0, Bruno: 0, Carlos: 0}
5. within_threshold = [Ana, Bruno, Carlos]  ← TODOS passam!
6. max_idle_days=3 é ignorado, pois todos têm idle_days=0

Resultado esperado: Bruno deveria ter prioridade (5 dias < 10 dias de Ana)
Resultado real: Balanceamento ignora ociosidade e usa contagem de histórias
```

---

## 8. Conclusão da Investigação

### 8.1 Confirmação

| Hipótese | Status | Evidência |
|----------|--------|-----------|
| H1 | ❌ Falso | Filtro É aplicado, mas lógica interna está errada |
| H2 | ❌ Falso | Parâmetros são passados corretamente |
| H3 | ✅ **CONFIRMADO** | `_filter_developers_by_idle_threshold()` tem bug semântico |
| H4 | ❌ Parcial | Fallback funciona, mas nunca é acionado (all pass) |
| H5 | ❌ Falso | Config chega corretamente |

### 8.2 Bug Semântico

O filtro por onda no cálculo de ociosidade faz com que:
- **Intenção:** "Não penalizar gaps entre ondas diferentes"
- **Efeito colateral:** "Ignorar completamente max_idle_days quando dev não tem histórias na onda atual"

---

## 9. Proposta de Correção Refinada

### Opção A: Considerar ociosidade GLOBAL para seleção (RECOMENDADA)

**Mudança:** Não passar `current_wave` para o filtro de ociosidade na **seleção de desenvolvedor**.

O `current_wave` deve ser usado apenas para **detecção de warnings**, não para **seleção**.

**Arquivo:** `developer_load_balancer.py`, método `get_developer_for_story()`, linhas 401-404

```python
# ANTES (linha 403):
within_threshold, idle_days_map = DeveloperLoadBalancer._filter_developers_by_idle_threshold(
    available_developers, story_map, new_story_start_date, max_idle_days, current_wave
)

# DEPOIS:
within_threshold, idle_days_map = DeveloperLoadBalancer._filter_developers_by_idle_threshold(
    available_developers, story_map, new_story_start_date, max_idle_days,
    current_wave=None  # ← Considera histórias de TODAS as ondas para seleção
)
```

**Impacto:**
- ✅ max_idle_days será respeitado considerando a última história do dev (qualquer onda)
- ✅ Devs com histórias recentes (qualquer onda) terão prioridade
- ✅ Devs ociosos há muito tempo serão preteridos
- ⚠️ Gaps entre ondas serão considerados na seleção (pode ser desejado)

### Opção B: Calcular ociosidade como "tempo desde última atividade"

**Mudança:** Quando `last_allocation is None` na onda atual, buscar a última história em qualquer onda.

```python
# Em _filter_developers_by_idle_threshold():
if last_allocation is None and current_wave is not None:
    # Fallback: buscar última história de QUALQUER onda
    last_allocation = DeveloperLoadBalancer._get_developer_last_allocation_before(
        dev.id, story_map, new_story_start_date, current_wave=None
    )
```

**Impacto:**
- ✅ Mantém filtro por onda para devs com histórias na onda
- ✅ Usa ociosidade global como fallback
- ⚠️ Mais complexo de implementar e testar

### Opção C: Adicionar parâmetro separado para controlar comportamento

**Mudança:** Criar `use_wave_filter_for_selection: bool` na configuração.

```python
# Configuração permite escolher:
# - True: ociosidade só conta dentro da onda (comportamento atual)
# - False: ociosidade conta desde última história (qualquer onda)
```

**Impacto:**
- ✅ Máxima flexibilidade
- ⚠️ Mais complexo de implementar
- ⚠️ Adiciona mais opções de configuração

---

## 10. Plano de Implementação

### Fase 1: Implementar Correção (Opção A)

1. **Modificar `get_developer_for_story()`:**
   - Remover `current_wave` da chamada a `_filter_developers_by_idle_threshold()`
   - Manter `current_wave` disponível para outros usos futuros se necessário

2. **Atualizar docstrings:**
   - Documentar que ociosidade para seleção considera TODAS as ondas
   - Documentar que warnings ainda usam filtro por onda

### Fase 2: Testes

1. **Criar teste unitário específico:**
   ```python
   def test_load_balancing_respects_max_idle_days_across_waves():
       """
       Cenário:
       - max_idle_days = 3
       - DevA: última história há 10 dias (onda anterior)
       - DevB: última história há 2 dias (onda anterior)
       - Nova história na onda atual

       Esperado: DevB deve ser selecionado (2 dias < 10 dias)
       """
   ```

2. **Testar cenário de reprodução:**
   - 3 devs com histórias em ondas anteriores
   - Verificar que dev com menor ociosidade é selecionado

### Fase 3: Validação

1. Rodar aplicação com logs de debug
2. Verificar que max_idle_days está sendo respeitado
3. Validar que não há regressões em outros cenários

---

## 11. Decisão Pendente

**Pergunta para o usuário:**

> Qual comportamento é desejado para max_idle_days?
>
> **A)** Considerar ociosidade desde a ÚLTIMA história do desenvolvedor (qualquer onda)
>    - Exemplo: Dev que não trabalha há 10 dias será preterido, mesmo se for primeira história da onda
>
> **B)** Considerar ociosidade apenas DENTRO da mesma onda
>    - Exemplo: Dev sem histórias na onda atual tem ociosidade 0, independente de há quanto tempo não trabalha
>
> **C)** Híbrido: Usar global se dev não tem histórias na onda, senão usar onda
>    - Exemplo: Dev sem histórias na onda usa ociosidade global; dev com histórias na onda usa ociosidade da onda

---

## 12. Correção Implementada

### 12.1 Mudança Realizada

**Arquivo:** `backlog_manager/domain/services/developer_load_balancer.py`

**Linha 401-410 (método `get_developer_for_story()`):**

```python
if new_story_start_date is not None and max_idle_days is not None:
    # NOTA: Usamos current_wave=None para considerar histórias de TODAS as ondas
    # na seleção do desenvolvedor. O parâmetro current_wave é usado apenas para
    # detecção de warnings de ociosidade, não para seleção.
    # Isso garante que max_idle_days seja respeitado mesmo na primeira história
    # de cada onda.
    within_threshold, idle_days_map = DeveloperLoadBalancer._filter_developers_by_idle_threshold(
        available_developers, story_map, new_story_start_date, max_idle_days,
        current_wave=None  # Considera ociosidade global, não por onda
    )
```

### 12.2 Docstring Atualizada

A docstring do método foi atualizada para documentar o novo comportamento:

```python
"""
...
NOTA: O parâmetro current_wave NÃO é usado para filtrar ociosidade na
seleção. A ociosidade é calculada desde a última história do desenvolvedor,
independente da onda. Isso garante que max_idle_days seja respeitado mesmo
na primeira história de cada onda.
...
"""
```

### 12.3 Testes

- ✅ Testes unitários do `DeveloperLoadBalancer`: 6/6 passando
- ✅ Testes unitários do `AllocateDevelopersUseCase`: 6/6 passando

---

## 13. Análise do Critério DEPENDENCY_OWNER

### 13.1 Pergunta

O mesmo bug de ignorar `max_idle_days` também afetava o critério DEPENDENCY_OWNER?

### 13.2 Análise do Fluxo

```
┌─────────────────────────────────────────────────────────┐
│  1. FILTRO DE OCIOSIDADE (aplicado PRIMEIRO)           │
│     ├─ Se há candidatos dentro do limite:              │
│     │   candidates = within_threshold                   │
│     │   → continua para passo 2                        │
│     └─ Se NENHUM dentro do limite (fallback):          │
│         return least_idle_dev  ← retorna direto        │
├─────────────────────────────────────────────────────────┤
│  2. PROPRIETÁRIO DE DEPENDÊNCIA                        │
│     ├─ Busca em candidates (já filtrados)              │
│     ├─ Se encontrar: return dependency_owner           │
│     └─ Se não encontrar: continua para passo 3        │
├─────────────────────────────────────────────────────────┤
│  3. BALANCEAMENTO DE CARGA (fallback final)            │
│     return sorted_devs[0]                              │
└─────────────────────────────────────────────────────────┘
```

### 13.3 Comportamento Verificado

| Cenário | Comportamento | Correto? |
|---------|---------------|----------|
| Proprietário dentro do limite | Ele é selecionado | ✅ |
| Proprietário fora do limite, outros dentro | Outro dev é selecionado | ✅ |
| Todos fora do limite (fallback) | Menos ocioso é selecionado, ignora proprietário | ✅ |

### 13.4 Decisão

**Opção escolhida: A - Limite de ociosidade tem prioridade**

Ordem de prioridade:
1. **Limite de ociosidade** (filtro primário)
2. **Proprietário de dependência** (dentro dos filtrados)
3. **Balanceamento de carga** (fallback)

Se o proprietário da dependência excede `max_idle_days`, ele perde a prioridade.
A continuidade de contexto é sacrificada em favor do limite de ociosidade.

### 13.5 Correção Adicional

O código original tinha um problema: quando NENHUM dev passava no filtro de ociosidade,
retornava direto o menos ocioso SEM aplicar o critério de alocação.

**Antes:**
```python
if within_threshold:
    candidates = within_threshold
else:
    # Retornava direto, ignorando DEPENDENCY_OWNER
    return min(available_developers, key=lambda d: idle_days_map.get(d.id, 0))
```

**Depois:**
```python
if within_threshold:
    candidates = within_threshold
else:
    # Mantém todos como candidatos e aplica critério normalmente
    candidates = available_developers
```

### 13.6 Novo Fluxo

```
1. Filtro de ociosidade → within_threshold
2. Se há candidatos dentro do limite → candidates = within_threshold
3. Se nenhum dentro do limite → candidates = available_developers (TODOS)
4. Se DEPENDENCY_OWNER → busca proprietário em candidates
5. Se encontrar → retorna proprietário
6. Se não encontrar → balanceamento de carga
```

### 13.7 Testes

- ✅ 12/12 testes passando

---

**Última atualização:** 2025-12-26 (correção fallback DEPENDENCY_OWNER)
**Status:** ✅ CORRIGIDO - Fallback agora aplica critério de alocação normalmente
