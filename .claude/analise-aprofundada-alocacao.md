# Analise Aprofundada: Sistema de Alocacao de Desenvolvedores

> **Objetivo:** Documentar o funcionamento completo do algoritmo de alocacao,
> identificar gaps e propor solucao robusta e definitiva.
>
> **Data:** 2025-12-26

---

## 1. Arquitetura Atual

### 1.1 Componentes Principais

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AllocateDevelopersUseCase                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ execute()                                                         │   │
│  │   1. Carregar dados (devs, config, stories)                       │   │
│  │   2. Para cada onda: _allocate_wave()                             │   │
│  │   3. Loop de estabilizacao:                                       │   │
│  │      - _final_dependency_check()                                  │   │
│  │      - _resolve_allocation_conflicts()                            │   │
│  │   4. Salvar e detectar ociosidade                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────┐  ┌──────────────────────────────────┐    │
│  │ _allocate_wave()         │  │ DeveloperLoadBalancer            │    │
│  │ - Loop de alocacao       │──│ - get_developer_for_story()     │    │
│  │ - Ajuste de datas        │  │ - get_dependency_owner()        │    │
│  │ - Deteccao de deadlock   │  │ - filter_by_idle_threshold()    │    │
│  └──────────────────────────┘  └──────────────────────────────────┘    │
│                                                                         │
│  ┌──────────────────────────┐  ┌──────────────────────────────────┐    │
│  │ _final_dependency_check()│  │ _resolve_allocation_conflicts()  │    │
│  │ - Ajusta datas apenas    │  │ - Ajusta datas apenas            │    │
│  │ - NAO usa LoadBalancer   │  │ - NAO usa LoadBalancer           │    │
│  │ - NAO verifica regras    │  │ - NAO verifica regras            │    │
│  └──────────────────────────┘  └──────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Fluxo Detalhado

```
INICIO
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. PREPARACAO                                                        │
│    - Carregar desenvolvedores                                        │
│    - Carregar configuracao (allocation_criteria, max_idle_days)     │
│    - Carregar historias e features                                   │
│    - Identificar ondas                                               │
└─────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. ALOCACAO POR ONDA (para cada onda em ordem)                       │
│    ┌───────────────────────────────────────────────────────────────┐ │
│    │ Loop ate todas alocadas ou deadlock:                          │ │
│    │   Para cada historia nao alocada:                             │ │
│    │     1. _ensure_dependencies_finished() - ajusta datas         │ │
│    │     2. _get_available_developers() - devs sem conflito        │ │
│    │     3. Se ha devs disponiveis:                                │ │
│    │        - LoadBalancer.get_developer_for_story() ✓             │ │
│    │          (considera max_idle_days, allocation_criteria)       │ │
│    │        - Alocar e reiniciar loop                              │ │
│    │     4. Se NAO ha devs:                                        │ │
│    │        - Ajustar datas +1 dia                                 │ │
│    │     5. Detectar deadlock                                      │ │
│    └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. LOOP DE ESTABILIZACAO (max 10 passadas)                          │
│    ┌───────────────────────────────────────────────────────────────┐ │
│    │ _final_dependency_check():                                    │ │
│    │   - Para cada historia em ordem topologica                    │ │
│    │   - Se inicia antes da dependencia terminar: AJUSTAR ✗        │ │
│    │   - NAO verifica disponibilidade do dev                       │ │
│    │   - NAO tenta realocar                                        │ │
│    │   - NAO verifica max_idle_days                                │ │
│    └───────────────────────────────────────────────────────────────┘ │
│    ┌───────────────────────────────────────────────────────────────┐ │
│    │ _resolve_allocation_conflicts():                              │ │
│    │   - Para cada dev, verificar sobreposicoes                    │ │
│    │   - Se conflito: empurrar historia posterior ✗                │ │
│    │   - NAO tenta realocar para outro dev                         │ │
│    │   - NAO verifica max_idle_days                                │ │
│    │   - NAO usa allocation_criteria                               │ │
│    └───────────────────────────────────────────────────────────────┘ │
│    Repetir ate estabilizar                                           │
└─────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. FINALIZACAO                                                       │
│    - Atualizar schedule_order                                        │
│    - Salvar historias modificadas                                    │
│    - Detectar ociosidade (IdlenessDetector)                          │
└─────────────────────────────────────────────────────────────────────┘
  │
  ▼
FIM
```

---

## 2. Regras de Alocacao

### 2.1 Regras Configuradas (Configuration)

| Regra | Descricao | Onde e Usada |
|-------|-----------|--------------|
| `allocation_criteria` | DEPENDENCY_OWNER ou LOAD_BALANCING | Apenas em _allocate_wave |
| `max_idle_days` | Maximo de dias ociosos permitidos | Apenas em _allocate_wave |

### 2.2 Comportamento de `allocation_criteria`

**DEPENDENCY_OWNER:**
1. Buscar desenvolvedor que trabalhou em dependencia da historia
2. Se disponivel: alocar para ele
3. Se nao disponivel: fallback para LOAD_BALANCING

**LOAD_BALANCING:**
1. Ordenar desenvolvedores por carga (menos historias primeiro)
2. Desempate aleatorio
3. Selecionar o primeiro

### 2.3 Comportamento de `max_idle_days`

1. Filtrar desenvolvedores com ociosidade <= max_idle_days
2. Se nenhum: usar o menos ocioso como fallback
3. Aplicado apenas na selecao inicial, NAO na realocacao

---

## 3. Gaps e Problemas Identificados

### 3.1 Inconsistencia entre Fases

| Aspecto | _allocate_wave | _final_dependency_check | _resolve_allocation_conflicts |
|---------|----------------|-------------------------|-------------------------------|
| Usa LoadBalancer | ✓ Sim | ✗ Nao | ✗ Nao |
| Verifica max_idle_days | ✓ Sim | ✗ Nao | ✗ Nao |
| Considera allocation_criteria | ✓ Sim | ✗ Nao | ✗ Nao |
| Tenta realocar | ✓ N/A | ✗ Nao | ✗ Nao |
| Verifica disponibilidade | ✓ Sim | ✗ Nao | ✗ Nao |

### 3.2 Problemas Especificos

#### Problema 1: Ajuste de Datas Sem Verificacao

```
Cenario:
- Dev AA: Story1 termina 10/01
- Dev AA: Story2 alocada 12/01-14/01 (gap = 1 dia, OK com max_idle_days=3)

Conflito detectado: Story2 precisa mover para 25/01

ATUAL:
  Story2 movida para 25/01 (gap = 11 dias uteis)
  VIOLA max_idle_days mas nao e verificado!

ESPERADO:
  Verificar se outro dev esta disponivel em 12/01-14/01
  Se sim: realocar Story2 para ele
  Se nao: mover + WARNING de violacao
```

#### Problema 2: Nao Tenta Realocar

```
Cenario:
- Dev AA: tem conflito em 12/01
- Dev BB: disponivel em 12/01

ATUAL:
  Empurra historia de AA para 15/01

ESPERADO:
  Verificar que BB esta disponivel
  Realocar historia para BB
  Manter data original 12/01
```

#### Problema 3: Criterio de Alocacao Ignorado

```
Cenario:
- allocation_criteria = DEPENDENCY_OWNER
- Story2 depende de Story1 (feita por Dev AA)
- Story2 precisa ser realocada

ATUAL:
  Mantem Story2 com Dev AA mesmo se nao for ideal

ESPERADO:
  Ao realocar, verificar se AA ainda e o DEPENDENCY_OWNER
  Se BB fez Story1, priorizar BB
```

#### Problema 4: Cascata de Ajustes

```
Cenario:
- Dev AA: S1 (10-12/01), S2 (13-15/01), S3 (16-18/01)
- S2 precisa mover para 20/01 (por dependencia)

ATUAL:
  S2 move para 20/01
  S3 agora conflita com S2
  S3 move para 21/01
  Loop continua ate estabilizar

ESPERADO:
  Antes de mover S2, verificar impacto em S3
  Tentar realocar S2 ou S3 para evitar cascata
```

### 3.3 Gaps de Metricas

| Metrica | Status |
|---------|--------|
| Total de realocacoes na fase final | NAO RASTREADO |
| Violacoes de max_idle_days apos ajustes | NAO RASTREADO |
| Historias que mudaram de desenvolvedor | NAO RASTREADO |
| Tentativas de realocacao falhas | NAO RASTREADO |

---

## 4. Analise de Impacto

### 4.1 Cenarios Afetados

1. **Historias com muitas dependencias em ondas diferentes**
   - Dependencia em onda anterior pode terminar tarde
   - Ajuste de data pode violar max_idle_days

2. **Desenvolvedores com poucas historias**
   - Mais propensos a gaps grandes
   - Ajustes podem criar ociosidade excessiva

3. **Ondas com muitas historias interdependentes**
   - Mais ajustes de dependencias
   - Mais conflitos potenciais
   - Cascata de realocacoes

### 4.2 Consequencias Atuais

1. **Violacao silenciosa de max_idle_days**
   - Usuario configura max_idle_days=3
   - Sistema cria gaps de 10+ dias
   - Nao ha warning ou correcao

2. **Distribuicao desigual apos ajustes**
   - Alocacao inicial e balanceada
   - Ajustes podem sobrecarregar alguns devs

3. **Perda de contexto (DEPENDENCY_OWNER)**
   - Historia fica com dev que nao conhece o contexto
   - Mesmo quando dev original esta disponivel

---

## 5. Solucao Proposta: Arquitetura Revisada

### 5.1 Principio Central

**Unificar a logica de alocacao em um unico ponto**

Ao inves de ter logica duplicada em varios metodos, criar um servico
central que aplica TODAS as regras de alocacao de forma consistente.

### 5.2 Nova Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AllocateDevelopersUseCase                        │
│  ┌──────────────────────────────────────────────────────────────────┐
│  │ execute()                                                         │
│  │   1. Carregar dados                                               │
│  │   2. Para cada onda: _allocate_wave()                             │
│  │   3. Loop de estabilizacao:                                       │
│  │      - _validate_and_fix_allocations() [NOVO]                     │
│  │   4. Salvar e detectar ociosidade                                 │
│  └──────────────────────────────────────────────────────────────────┘
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐
│  │ _validate_and_fix_allocations() [NOVO - substitui os dois]       │
│  │                                                                   │
│  │ Para cada historia (ordem topologica):                            │
│  │   1. Verificar violacao de dependencia                            │
│  │   2. Verificar conflito de periodo                                │
│  │   3. Se problema detectado:                                       │
│  │      a) Calcular nova data necessaria                             │
│  │      b) Verificar se dev atual disponivel na nova data            │
│  │      c) Se NAO: _try_reallocate_with_rules()                      │
│  │      d) Se realocacao falha: ajustar data + verificar regras      │
│  │   4. Apos ajuste: verificar max_idle_days                         │
│  │      a) Se viola: _try_reallocate_with_rules()                    │
│  │      b) Se realocacao falha: WARNING                              │
│  └──────────────────────────────────────────────────────────────────┘
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐
│  │ _try_reallocate_with_rules() [NOVO]                               │
│  │                                                                   │
│  │ Tenta realocar historia para outro dev respeitando TODAS regras:  │
│  │   1. Buscar devs disponiveis no periodo da historia               │
│  │   2. Remover dev atual da lista                                   │
│  │   3. Aplicar filtro de max_idle_days                              │
│  │   4. Aplicar allocation_criteria (DEPENDENCY_OWNER ou LOAD_BAL)   │
│  │   5. Se encontrou dev: realocar e retornar True                   │
│  │   6. Se nao: retornar False                                       │
│  └──────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Fluxo Revisado

```
LOOP DE ESTABILIZACAO:
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Para cada historia (ordem topologica):                               │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────────┐
│   │ 1. VERIFICAR VIOLACAO DE DEPENDENCIA                            │
│   │    - Buscar ultima dependencia que termina                       │
│   │    - Se historia inicia antes: PROBLEMA DETECTADO               │
│   └─────────────────────────────────────────────────────────────────┘
│                          │
│                          ▼ (se problema)
│   ┌─────────────────────────────────────────────────────────────────┐
│   │ 2. VERIFICAR CONFLITO DE PERIODO (com dev atual)                │
│   │    - Buscar outras historias do dev                             │
│   │    - Verificar sobreposicao                                      │
│   └─────────────────────────────────────────────────────────────────┘
│                          │
│                          ▼ (se problema)
│   ┌─────────────────────────────────────────────────────────────────┐
│   │ 3. TENTAR REALOCAR (antes de ajustar datas)                     │
│   │                                                                  │
│   │    available = _get_available_developers(periodo_original)      │
│   │    if available:                                                 │
│   │       selected = LoadBalancer.get_developer_for_story(          │
│   │         candidates=available,                                    │
│   │         max_idle_days=config.max_idle_days,                      │
│   │         allocation_criteria=config.allocation_criteria           │
│   │       )                                                          │
│   │       if selected: REALOCAR e CONTINUAR                         │
│   └─────────────────────────────────────────────────────────────────┘
│                          │
│                          ▼ (se realocacao falhou)
│   ┌─────────────────────────────────────────────────────────────────┐
│   │ 4. AJUSTAR DATAS (ultimo recurso)                               │
│   │    - Calcular nova data (apos dependencia ou apos conflito)     │
│   │    - Atualizar historia                                          │
│   └─────────────────────────────────────────────────────────────────┘
│                          │
│                          ▼
│   ┌─────────────────────────────────────────────────────────────────┐
│   │ 5. VERIFICAR MAX_IDLE_DAYS                                      │
│   │    - Calcular gap entre ultima historia do dev e esta           │
│   │    - Se gap > max_idle_days:                                     │
│   │      a) Tentar realocar para dev com menor gap                  │
│   │      b) Se falhar: emitir WARNING                               │
│   └─────────────────────────────────────────────────────────────────┘
│                                                                      │
│ Repetir ate nao haver mais problemas                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Plano de Implementacao Detalhado

### Fase 1: Criar Metodos Auxiliares

#### 1.1 `_calculate_idle_days_for_story`

```python
def _calculate_idle_days_for_story(
    self,
    story: Story,
    all_stories: List[Story],
) -> Optional[int]:
    """
    Calcula dias ociosos entre ultima historia do dev e esta.

    Returns:
        Numero de dias ociosos, ou None se e a primeira do dev
    """
```

#### 1.2 `_check_max_idle_violation`

```python
def _check_max_idle_violation(
    self,
    story: Story,
    all_stories: List[Story],
) -> Optional[int]:
    """
    Verifica se alocacao viola max_idle_days.

    Returns:
        Numero de dias se viola, None se OK
    """
```

#### 1.3 `_try_reallocate_with_rules`

```python
def _try_reallocate_with_rules(
    self,
    story: Story,
    all_stories: List[Story],
    developers: List[Developer],
    config: Configuration,
    exclude_dev_id: Optional[str] = None,
    reason: str = "",
) -> bool:
    """
    Tenta realocar historia respeitando TODAS as regras.

    Processo:
    1. Buscar devs disponiveis no periodo
    2. Excluir dev atual se especificado
    3. Aplicar filtro de max_idle_days
    4. Aplicar allocation_criteria
    5. Realocar se encontrou dev

    Returns:
        True se realocou, False se nao foi possivel
    """
```

### Fase 2: Criar Metodo Unificado

#### 2.1 `_validate_and_fix_allocations`

```python
def _validate_and_fix_allocations(
    self,
    all_stories: List[Story],
    developers: List[Developer],
    config: Configuration,
) -> Tuple[int, int, int]:
    """
    Valida e corrige alocacoes respeitando TODAS as regras.

    Substitui _final_dependency_check e _resolve_allocation_conflicts.

    Processo:
    1. Ordenar historias topologicamente
    2. Para cada historia:
       a) Verificar violacao de dependencia
       b) Verificar conflito de periodo
       c) Se problema: tentar realocar primeiro
       d) Se realocacao falhou: ajustar datas
       e) Verificar max_idle_days
       f) Se viola: tentar realocar ou warning

    Returns:
        Tupla (dependencias_corrigidas, conflitos_resolvidos, realocacoes)
    """
```

### Fase 3: Modificar execute()

```python
# ANTES:
for pass_num in range(max_stabilization_passes):
    violations_fixed = self._final_dependency_check(all_stories, config)
    conflicts_resolved = self._resolve_allocation_conflicts(all_stories, developers)
    if violations_fixed == 0 and conflicts_resolved == 0:
        break

# DEPOIS:
for pass_num in range(max_stabilization_passes):
    deps_fixed, conflicts_fixed, reallocations = self._validate_and_fix_allocations(
        all_stories, developers, config
    )
    total_fixes = deps_fixed + conflicts_fixed + reallocations
    if total_fixes == 0:
        break
```

### Fase 4: Adicionar Metricas

```python
@dataclass
class AllocationMetrics:
    # ... campos existentes ...

    # NOVOS campos:
    reallocations_in_validation: int = 0
    max_idle_violations_detected: int = 0
    max_idle_violations_fixed: int = 0
    failed_reallocations: int = 0
```

### Fase 5: Adicionar Testes

```python
class TestValidateAndFixAllocations:
    def test_tries_reallocation_before_date_adjustment(self):
        """Deve tentar realocar antes de ajustar datas."""

    def test_respects_max_idle_days_after_adjustment(self):
        """Deve verificar max_idle_days apos ajuste."""

    def test_uses_allocation_criteria_when_reallocating(self):
        """Deve usar criterio de alocacao ao realocar."""

    def test_emits_warning_when_max_idle_violated(self):
        """Deve emitir warning quando max_idle e violado."""

    def test_handles_cascading_adjustments(self):
        """Deve lidar com ajustes em cascata."""
```

---

## 7. Consideracoes de Implementacao

### 7.1 Ordem de Prioridade das Regras

1. **Dependencias** - OBRIGATORIO (regra de negocio)
2. **Sem conflitos de periodo** - OBRIGATORIO (impossibilidade fisica)
3. **max_idle_days** - DESEJAVEL (configuracao do usuario)
4. **allocation_criteria** - DESEJAVEL (preferencia do usuario)

### 7.2 Quando NAO Realocar

- Historia ja foi realocada neste ciclo (evitar ping-pong)
- Realocacao criaria outro conflito de dependencia
- Nenhum dev disponivel no periodo
- Limite de realocacoes atingido (safety)

### 7.3 Limite de Realocacoes

```python
MAX_REALLOCATIONS_PER_STORY = 3
MAX_TOTAL_REALLOCATIONS = 100

# Rastrear realocacoes por historia
_reallocations_count: Dict[str, int] = {}
```

### 7.4 Logging e Debugging

```python
# Niveis de log:
# INFO: Realocacoes bem-sucedidas, warnings
# DEBUG: Tentativas de realocacao, calculos de idle_days
# WARNING: Violacoes de max_idle_days nao corrigidas
```

---

## 8. Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Loop infinito de realocacoes | Media | Alto | Limite por historia e total |
| Performance degradada | Media | Medio | Limitar passadas, cache |
| Cascata de ajustes | Media | Medio | Processar em ordem topologica |
| Conflitos reaparecendo | Baixa | Alto | Verificacao apos cada ajuste |
| Realocacao viola outra regra | Media | Medio | Verificar TODAS regras antes |

---

## 9. Checklist de Implementacao

### Fase 1: Metodos Auxiliares
- [ ] Implementar `_calculate_idle_days_for_story`
- [ ] Implementar `_check_max_idle_violation`
- [ ] Implementar `_try_reallocate_with_rules`
- [ ] Adicionar testes unitarios

### Fase 2: Metodo Unificado
- [ ] Implementar `_validate_and_fix_allocations`
- [ ] Integrar verificacao de dependencias
- [ ] Integrar verificacao de conflitos
- [ ] Integrar verificacao de max_idle_days
- [ ] Adicionar testes unitarios

### Fase 3: Integracao
- [ ] Modificar execute() para usar novo metodo
- [ ] Remover ou deprecar metodos antigos
- [ ] Atualizar metricas
- [ ] Adicionar testes de integracao

### Fase 4: Validacao
- [ ] Testar com dados reais
- [ ] Verificar metricas de performance
- [ ] Validar que todas as regras sao respeitadas
- [ ] Revisar logs e warnings

---

## 10. Estimativa de Esforco

| Fase | Complexidade | Arquivos |
|------|--------------|----------|
| Fase 1: Metodos auxiliares | Baixa | allocate_developers.py |
| Fase 2: Metodo unificado | Alta | allocate_developers.py |
| Fase 3: Integracao | Media | allocate_developers.py |
| Fase 4: Testes | Media | test_allocate_developers.py |
| Fase 5: Validacao | Baixa | - |

---

**Status:** PENDENTE APROVACAO
**Proximos Passos:** Implementar apos aprovacao do usuario
