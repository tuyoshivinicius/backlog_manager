# Plano: Corrigir Regras de Alocacao na Resolucao Final

> **Objetivo:** Garantir que `_final_dependency_check` e `_resolve_allocation_conflicts` respeitem as regras de alocacao (max_idle_days, criterio de alocacao, fallback).
>
> **Data:** 2025-12-26

---

## 1. Analise do Problema

### 1.1 Situacao Atual

Apos a alocacao principal, dois metodos sao executados para corrigir problemas:

1. **`_final_dependency_check`**: Ajusta datas de historias que violam dependencias
2. **`_resolve_allocation_conflicts`**: Ajusta datas de historias com periodos sobrepostos

**Problema:** Ambos os metodos apenas ajustam datas, sem considerar:

| Regra | Status Atual | Impacto |
|-------|--------------|---------|
| max_idle_days | NAO VERIFICADO | Pode criar gaps maiores que o permitido |
| allocation_criteria | NAO VERIFICADO | Ignora DEPENDENCY_OWNER |
| Fallback para outro dev | NAO IMPLEMENTADO | Sempre empurra datas, nunca realoca |
| Disponibilidade de outros devs | NAO VERIFICADO | Pode haver dev livre no periodo original |

### 1.2 Exemplo do Problema

```
Cenario:
- max_idle_days = 3
- Dev AA: Story1 termina 10/01
- Dev AA: Story2 alocada para 12/01-14/01 (gap de 1 dia - OK)
- Dev BB: Livre a partir de 12/01

Conflito detectado:
- Story2 precisa ser movida para 20/01 (por causa de dependencia ou conflito)

Comportamento ATUAL:
- Story2 movida para 20/01 (gap de 8 dias - VIOLA max_idle_days!)
- Dev AA fica ocioso por 8 dias

Comportamento ESPERADO:
- Verificar se BB esta disponivel em 12/01-14/01
- Se sim, realocar Story2 para BB
- Se nao, mover para 20/01 mas emitir warning
```

### 1.3 Fluxo Atual vs Esperado

**Atual:**
```
_final_dependency_check:
  Para cada historia com violacao:
    -> Ajustar datas (empurrar para frente)

_resolve_allocation_conflicts:
  Para cada conflito:
    -> Ajustar datas da historia posterior
```

**Esperado:**
```
_final_dependency_check:
  Para cada historia com violacao:
    -> Calcular nova data necessaria
    -> Se historia alocada:
       -> Verificar se dev original esta disponivel na nova data
       -> Se NAO: tentar realocar para outro dev disponivel
       -> Se nenhum disponivel: ajustar datas + warning
    -> Ajustar datas

_resolve_allocation_conflicts:
  Para cada conflito:
    -> Antes de ajustar: verificar se ha outro dev disponivel no periodo ORIGINAL
    -> Se sim: realocar para esse dev (evita o ajuste)
    -> Se nao: ajustar datas
    -> Apos ajuste: verificar se viola max_idle_days
    -> Se viola: tentar realocar para dev com menor ociosidade
```

---

## 2. Opcoes de Correcao

### Opcao A: Adicionar Verificacoes Simples

**Descricao:** Apenas emitir warnings quando regras sao violadas.

**Pros:**
- Implementacao simples
- Baixo risco de side effects
- Mantem comportamento atual

**Contras:**
- Nao resolve o problema de fato
- Apenas informa, nao corrige

### Opcao B: Tentar Realocar Antes de Ajustar

**Descricao:** Antes de ajustar datas, verificar se ha outro dev disponivel.

**Pros:**
- Resolve o problema na raiz
- Mantem alocacao no periodo original quando possivel

**Contras:**
- Implementacao mais complexa
- Pode criar cascata de realocacoes

### Opcao C: Realocar Apos Detectar Violacao de max_idle_days

**Descricao:** Ajustar datas primeiro, depois verificar se viola max_idle_days e realocar se necessario.

**Pros:**
- Mais simples que Opcao B
- Corrige apenas quando necessario

**Contras:**
- Pode resultar em datas diferentes do periodo original

### Opcao D: Combinar B + C (RECOMENDADA)

**Descricao:**
1. Antes de ajustar datas, verificar se ha dev disponivel no periodo original
2. Se nao ha, ajustar datas
3. Apos ajuste, verificar se viola max_idle_days
4. Se viola, tentar encontrar dev com menor ociosidade

**Pros:**
- Abordagem completa
- Prioriza manter periodo original
- Fallback para menor ociosidade

**Contras:**
- Implementacao mais complexa

---

## 3. Plano de Implementacao (Opcao D)

### Fase 1: Criar Metodo Auxiliar `_try_reallocate_story`

```python
def _try_reallocate_story(
    self,
    story: Story,
    all_stories: List[Story],
    developers: List[Developer],
    config: Configuration,
    reason: str,
) -> bool:
    """
    Tenta realocar historia para outro desenvolvedor.

    Args:
        story: Historia a realocar
        all_stories: Todas as historias
        developers: Todos os desenvolvedores
        config: Configuracao
        reason: Motivo da realocacao (para logging)

    Returns:
        True se realocou com sucesso, False se manteve alocacao original
    """
    if story.developer_id is None or story.start_date is None or story.end_date is None:
        return False

    # Buscar desenvolvedores disponiveis no periodo da historia
    available_devs = self._get_available_developers(
        story.start_date,
        story.end_date,
        all_stories,
        developers,
    )

    # Remover o desenvolvedor atual da lista (ele tem conflito ou viola regra)
    available_devs = [d for d in available_devs if d.id != story.developer_id]

    if not available_devs:
        return False

    # Usar load balancer para selecionar melhor desenvolvedor
    selected_dev = self._load_balancer.get_developer_for_story(
        story,
        self._story_map,
        available_devs,
        all_stories,
        allocation_criteria=self._allocation_criteria,
        new_story_start_date=story.start_date,
        max_idle_days=self._max_idle_days,
    )

    if selected_dev is None:
        selected_dev = available_devs[0]  # Fallback

    # Realocar
    old_dev = story.developer_id
    story.developer_id = selected_dev.id
    self._modified_stories.add(story.id)

    logger.info(
        f"Historia {story.id} realocada de {old_dev} para {selected_dev.id} ({reason})"
    )

    return True
```

### Fase 2: Criar Metodo `_check_idle_violation`

```python
def _check_idle_violation(
    self,
    story: Story,
    all_stories: List[Story],
) -> Optional[int]:
    """
    Verifica se a alocacao da historia viola max_idle_days.

    Returns:
        Numero de dias ociosos se viola, None se OK
    """
    if self._max_idle_days is None or story.developer_id is None or story.start_date is None:
        return None

    # Buscar ultima historia do desenvolvedor antes desta
    dev_stories = [
        s for s in all_stories
        if s.developer_id == story.developer_id
        and s.end_date is not None
        and s.end_date < story.start_date
    ]

    if not dev_stories:
        return None

    last_story = max(dev_stories, key=lambda s: s.end_date)
    idle_days = self._schedule_calculator.count_workdays_between(
        last_story.end_date, story.start_date
    )

    if idle_days > self._max_idle_days:
        return idle_days

    return None
```

### Fase 3: Modificar `_resolve_allocation_conflicts`

```python
def _resolve_allocation_conflicts(
    self,
    all_stories: List[Story],
    developers: List[Developer],
    config: Configuration,  # NOVO parametro
) -> int:
    """..."""
    conflicts_resolved = 0
    max_passes = 100

    for pass_num in range(max_passes):
        conflict_found_in_pass = False

        for dev in developers:
            dev_stories = [...]  # mesmo codigo

            for i in range(len(dev_stories) - 1):
                current = dev_stories[i]
                next_story = dev_stories[i + 1]

                if self._periods_overlap(...):
                    # NOVO: Tentar realocar next_story antes de ajustar datas
                    if self._try_reallocate_story(
                        next_story, all_stories, developers, config,
                        reason=f"conflito com {current.id}"
                    ):
                        conflicts_resolved += 1
                        conflict_found_in_pass = True
                        continue

                    # Nao foi possivel realocar - ajustar datas
                    old_start = next_story.start_date
                    new_start = self._schedule_calculator.add_workdays(
                        current.end_date, 1
                    )

                    if self._update_story_dates(next_story, new_start):
                        self._modified_stories.add(next_story.id)
                        conflicts_resolved += 1
                        conflict_found_in_pass = True

                        # NOVO: Verificar se ajuste viola max_idle_days
                        idle_days = self._check_idle_violation(next_story, all_stories)
                        if idle_days is not None:
                            # Tentar realocar para dev com menor ociosidade
                            if self._try_reallocate_story(
                                next_story, all_stories, developers, config,
                                reason=f"ociosidade excessiva ({idle_days} dias)"
                            ):
                                # Recalcular datas para o novo dev
                                # (ele pode ter slot mais cedo disponivel)
                                pass
                            else:
                                logger.warning(
                                    f"Historia {next_story.id}: violacao de max_idle_days "
                                    f"({idle_days} dias > {self._max_idle_days})"
                                )

        if not conflict_found_in_pass:
            break

    return conflicts_resolved
```

### Fase 4: Modificar `_final_dependency_check`

Similar ao `_resolve_allocation_conflicts`:
1. Apos calcular nova data, verificar se dev original esta disponivel
2. Se nao, tentar realocar
3. Se nao possivel, ajustar datas + verificar max_idle_days

### Fase 5: Adicionar Testes

```python
def test_resolve_conflicts_tries_reallocation_first():
    """Deve tentar realocar antes de ajustar datas."""
    pass

def test_resolve_conflicts_respects_max_idle_days():
    """Deve realocar se ajuste viola max_idle_days."""
    pass

def test_resolve_conflicts_uses_allocation_criteria():
    """Deve usar criterio de alocacao ao realocar."""
    pass

def test_final_check_tries_reallocation():
    """_final_dependency_check deve tentar realocar."""
    pass
```

---

## 4. Consideracoes

### 4.1 Ordem de Prioridade

1. **Dependencias** - Mais importante (regra de negocio)
2. **Sem conflitos de periodo** - Segundo mais importante
3. **Respeitar max_idle_days** - Terceiro
4. **Criterio de alocacao** - Quarto

### 4.2 Quando NAO Realocar

- Historia ja foi realocada neste ciclo (evitar ping-pong)
- Nenhum dev disponivel no periodo
- Realocacao criaria outro conflito

### 4.3 Limite de Realocacoes

Adicionar limite para evitar loop infinito:
- max_reallocations_per_story = 3
- Se exceder, manter alocacao atual + warning

---

## 5. Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Loop infinito de realocacoes | Media | Alto | Limite de realocacoes por historia |
| Cascata de ajustes | Media | Medio | Processar em ordem topologica |
| Performance degradada | Baixa | Medio | Limitar numero de passadas |
| Conflitos reaparecem | Baixa | Alto | Loop de estabilizacao ja implementado |

---

## 6. Checklist de Implementacao

- [ ] Criar metodo `_try_reallocate_story`
- [ ] Criar metodo `_check_idle_violation`
- [ ] Modificar `_resolve_allocation_conflicts` para tentar realocar
- [ ] Modificar `_resolve_allocation_conflicts` para verificar max_idle_days
- [ ] Modificar `_final_dependency_check` para tentar realocar
- [ ] Adicionar parametro config aos metodos
- [ ] Adicionar testes unitarios
- [ ] Testar com dados reais
- [ ] Verificar metricas de performance

---

**Status:** PENDENTE
**Complexidade:** Media-Alta
**Arquivos a Modificar:**
- `backlog_manager/application/use_cases/schedule/allocate_developers.py`
- `tests/unit/application/use_cases/test_allocate_developers.py`
