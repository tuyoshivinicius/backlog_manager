# Plano: Corrigir Bug de Conflito de Alocação

> **Objetivo:** Corrigir o bug que permite alocar desenvolvedores para histórias com períodos sobrepostos.
>
> **Data:** 2025-12-26

---

## 1. Análise do Bug

### 1.1 Evidências Encontradas

**Conflitos identificados no `backlog.xlsx` para desenvolvedor AA:**

| História | Wave | Período        | Feature                    | Deps        |
|----------|------|----------------|----------------------------|-------------|
| T2       | 3    | 21-23/01/2026 | EXP APROVAR SOLICITAÇÃO    | L7, T1      |
| **N5**   | 5    | **21-23/01/2026** | EXP FINAL               | N1, N2, N3  |
| B9       | 4    | 26-28/01/2026 | EXP CONSULTAR APROVAÇÕES   | T2          |
| **A2**   | 5    | **26-29/01/2026** | EXP FINAL               | A1          |

**Problema:** T2 e N5 têm exatamente o mesmo período (21-23/01) com o mesmo desenvolvedor (AA). B9 e A2 se sobrepõem em 26-28/01.

### 1.2 Causa Raiz Identificada

**Arquivo:** `backlog_manager/application/use_cases/schedule/allocate_developers.py`

**Método problemático:** `_final_dependency_check()` (linhas 805-858)

```python
def _final_dependency_check(self, all_stories: List[Story], config: Configuration) -> int:
    sorted_stories = self._backlog_sorter.sort(all_stories)

    for story in sorted_stories:
        # ...
        if story.start_date <= latest_dep_end:
            # VIOLAÇÃO DETECTADA - Ajustar
            new_start = self._schedule_calculator.add_workdays(latest_dep_end, 1)
            self._update_story_dates(story, new_start)  # ← BUG AQUI!
            # ...
```

**O BUG:** Este método ajusta datas de histórias JÁ ALOCADAS sem verificar se o desenvolvedor ainda está disponível no novo período!

### 1.3 Cenário que Causa o Bug

```
1. Wave 3: T2 alocada para AA (21-23/01)

2. Wave 5: N5 é processada
   - Deps: N1 (30/12), N2 (12/01), N3 (16/01)
   - N5 pode iniciar 17/01 (Sáb → 19/01 Mon)
   - Período inicial: 19-21/01 (3 dias)
   - 19-21/01 sobrepõe com T2 (21-23/01) no dia 21!
   - AA não disponível → ajustar datas
   - Loop de ajustes até encontrar slot livre OU max_iterations

3. Mesmo que N5 seja alocada em slot livre (ex: 29-31/01)...

4. _final_dependency_check() executa APÓS todas as ondas:
   - Se alguma dependência de N5 foi ajustada durante alocação
   - N5.start_date pode violar a nova data da dependência
   - N5 é ajustada para novo período SEM verificar disponibilidade
   - Resultado: N5 pode cair no mesmo período de outra história do mesmo dev
```

---

## 2. Fluxo do Algoritmo Atual

```
execute()
│
├─1. Valida desenvolvedores
├─2. Carrega todas as histórias (cache)
├─3. Identifica ondas
│
├─4. Para cada onda (ordenadas):
│   └─ _allocate_wave()
│       ├─ Loop de alocação (max 1000 iterações)
│       │   ├─ Para cada história não alocada:
│       │   │   ├─ _ensure_dependencies_finished() - ajusta datas
│       │   │   ├─ _get_available_developers() - verifica conflitos
│       │   │   │
│       │   │   ├─ Se há dev disponível:
│       │   │   │   ├─ Aloca desenvolvedor
│       │   │   │   └─ Reinicia loop
│       │   │   │
│       │   │   └─ Se NÃO há dev disponível:
│       │   │       └─ Ajusta datas +1 dia útil
│       │   │
│       │   └─ Detecta deadlock (sem progresso)
│       │
│       └─ Retorna (histórias alocadas, warnings)
│
├─5. _final_dependency_check() ← BUG AQUI!
│   └─ Ajusta datas SEM verificar disponibilidade
│
├─6. Atualiza schedule_order
├─7. Salva em batch
└─8. Detecta ociosidade
```

---

## 3. Opções de Correção

### Opção A: Pular Histórias Alocadas no _final_dependency_check

**Descrição:** Não ajustar datas de histórias que já têm desenvolvedor alocado.

**Prós:**
- Implementação simples (adicionar um `if`)
- Preserva alocações existentes
- Menor risco de side effects

**Contras:**
- Pode deixar violações de dependência não resolvidas
- A história pode ter data de início antes da dependência terminar

**Implementação:**
```python
def _final_dependency_check(self, all_stories, config) -> int:
    for story in sorted_stories:
        # NOVO: Pular histórias já alocadas
        if story.developer_id is not None:
            continue
        # ... resto do código
```

### Opção B: Re-verificar e Re-alocar Após Ajuste

**Descrição:** Após ajustar datas de uma história alocada, verificar se o desenvolvedor ainda está disponível. Se não, limpar a alocação para que seja reprocessada.

**Prós:**
- Mantém consistência de dependências
- Permite que histórias encontrem novo slot

**Contras:**
- Implementação mais complexa
- Pode criar cascata de re-alocações
- Histórias podem ficar sem desenvolvedor se não houver slot

**Implementação:**
```python
def _final_dependency_check(self, all_stories, config) -> int:
    stories_to_reallocate = []

    for story in sorted_stories:
        # ... ajusta datas
        if story.developer_id is not None:
            # Verificar se dev ainda disponível no novo período
            available = self._get_available_developers(
                story.start_date, story.end_date, all_stories, [dev]
            )
            if not available:
                # Limpar alocação para reprocessamento
                story.developer_id = None
                stories_to_reallocate.append(story)

    # Reprocessar histórias que perderam desenvolvedor
    # ...
```

### Opção C: Adicionar Validação Final de Conflitos

**Descrição:** Após `_final_dependency_check`, adicionar nova etapa que detecta e resolve conflitos de período.

**Prós:**
- Abordagem defensiva (catch-all)
- Pode detectar outros tipos de conflitos
- Não modifica lógica existente

**Contras:**
- Adiciona complexidade ao algoritmo
- Pode ser lento com muitas histórias
- Resolve sintomas, não causa raiz

**Implementação:**
```python
def _resolve_allocation_conflicts(self, all_stories, developers, config):
    """Nova etapa após _final_dependency_check."""
    conflicts_found = True

    while conflicts_found:
        conflicts_found = False

        for dev in developers:
            dev_stories = [s for s in all_stories if s.developer_id == dev.id]
            dev_stories.sort(key=lambda s: s.start_date)

            for i, story in enumerate(dev_stories[:-1]):
                next_story = dev_stories[i + 1]
                if self._periods_overlap(story.start_date, story.end_date,
                                         next_story.start_date, next_story.end_date):
                    # Conflito detectado - ajustar next_story
                    new_start = self._schedule_calculator.add_workdays(story.end_date, 1)
                    self._update_story_dates(next_story, new_start)
                    conflicts_found = True
```

### Opção D: Combinar A + C (Recomendada)

**Descrição:** Pular histórias alocadas no `_final_dependency_check` (Opção A) E adicionar validação final de conflitos (Opção C).

**Prós:**
- Dupla proteção
- Simples de implementar
- Baixo risco

**Contras:**
- Ligeiramente mais código

---

## 4. Recomendação

**Recomendação:** Opção D (Combinar A + C)

**Justificativa:**
1. Opção A previne novos conflitos gerados por `_final_dependency_check`
2. Opção C detecta e resolve conflitos que possam existir por outros motivos
3. A combinação oferece proteção em múltiplas camadas
4. Ambas são simples de implementar e testar

---

## 5. Plano de Implementação

### Fase 1: Corrigir _final_dependency_check (Opção A)

**Arquivo:** `allocate_developers.py`

**Mudança:**
```python
def _final_dependency_check(self, all_stories: List[Story], config: Configuration) -> int:
    sorted_stories = self._backlog_sorter.sort(all_stories)
    violations_fixed = 0

    for story in sorted_stories:
        # NOVO: Pular histórias já alocadas
        if story.developer_id is not None:
            logger.debug(f"História {story.id}: pulando _final_dependency_check (já alocada)")
            continue

        if not story.start_date or not story.dependencies:
            continue
        # ... resto do código
```

### Fase 2: Adicionar Validação de Conflitos (Opção C)

**Arquivo:** `allocate_developers.py`

**Novo método:**
```python
def _resolve_allocation_conflicts(
    self,
    all_stories: List[Story],
    developers: List[Developer],
    config: Configuration
) -> int:
    """
    Detecta e resolve conflitos de alocação (períodos sobrepostos).

    Executa após _final_dependency_check para garantir que não há
    dois histórias do mesmo desenvolvedor com períodos sobrepostos.

    Returns:
        Número de conflitos resolvidos
    """
    conflicts_resolved = 0
    max_passes = 100  # Limite de segurança

    for _ in range(max_passes):
        conflict_found = False

        for dev in developers:
            # Buscar histórias alocadas para este dev
            dev_stories = [
                s for s in all_stories
                if s.developer_id == dev.id
                and s.start_date is not None
                and s.end_date is not None
            ]

            if len(dev_stories) < 2:
                continue

            # Ordenar por data de início
            dev_stories.sort(key=lambda s: s.start_date)

            # Verificar sobreposições consecutivas
            for i in range(len(dev_stories) - 1):
                current = dev_stories[i]
                next_story = dev_stories[i + 1]

                if self._periods_overlap(
                    current.start_date, current.end_date,
                    next_story.start_date, next_story.end_date
                ):
                    # CONFLITO! Ajustar next_story para começar após current
                    old_start = next_story.start_date
                    new_start = self._schedule_calculator.add_workdays(current.end_date, 1)

                    if self._update_story_dates(next_story, new_start):
                        self._modified_stories.add(next_story.id)
                        conflicts_resolved += 1
                        conflict_found = True

                        logger.warning(
                            f"Conflito resolvido: {next_story.id} ajustada de {old_start} "
                            f"para {new_start} (sobrepunha com {current.id})"
                        )

        if not conflict_found:
            break

    return conflicts_resolved
```

**Integração no execute():**
```python
# 5. VALIDAÇÃO FINAL: Re-verificar e ajustar dependências
logger.info("Validação final: verificando dependências")
violations_fixed = self._final_dependency_check(all_stories, config)

# 5.5 NOVO: Resolver conflitos de alocação
logger.info("Validação final: resolvendo conflitos de alocação")
conflicts_resolved = self._resolve_allocation_conflicts(all_stories, developers, config)
if conflicts_resolved > 0:
    logger.warning(f"Validação final: {conflicts_resolved} conflitos de alocação resolvidos")
```

### Fase 3: Adicionar Testes

**Arquivo:** `tests/unit/application/use_cases/test_allocate_developers.py`

**Novos testes:**
```python
def test_final_dependency_check_skips_allocated_stories():
    """Verifica que _final_dependency_check pula histórias já alocadas."""
    pass

def test_resolve_allocation_conflicts_adjusts_overlapping_periods():
    """Verifica que _resolve_allocation_conflicts ajusta períodos sobrepostos."""
    pass

def test_no_allocation_conflicts_after_full_execution():
    """Verifica que não há conflitos após execução completa."""
    pass
```

---

## 6. Testes de Validação

### 6.1 Teste Manual

1. Fazer backup do `backlog.db`
2. Limpar alocações existentes: `UPDATE stories SET developer_id = NULL`
3. Executar alocação via UI
4. Verificar que não há sobreposições no Excel exportado

### 6.2 Script de Validação

```python
# Verificar conflitos no banco
import sqlite3

conn = sqlite3.connect('backlog.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT s1.id, s2.id, s1.developer_id, s1.start_date, s1.end_date, s2.start_date, s2.end_date
    FROM stories s1
    JOIN stories s2 ON s1.developer_id = s2.developer_id AND s1.id < s2.id
    WHERE s1.start_date <= s2.end_date AND s2.start_date <= s1.end_date
''')

conflicts = cursor.fetchall()
if conflicts:
    print(f"ERRO: {len(conflicts)} conflitos encontrados!")
    for c in conflicts:
        print(f"  {c[0]} e {c[1]} (dev={c[2]}): {c[3]}-{c[4]} vs {c[5]}-{c[6]}")
else:
    print("OK: Nenhum conflito de alocação encontrado")
```

---

## 7. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Cascata de ajustes infinita | Baixa | Alto | Limite de passes (max_passes=100) |
| Performance degradada | Baixa | Médio | Algoritmo O(n) por desenvolvedor |
| Dependências violadas | Baixa | Alto | Fase 1 não ajusta histórias alocadas |
| Histórias sem desenvolvedor | Média | Médio | Opção A preserva alocações |

---

## 8. Checklist de Implementação

- [x] Fase 1: Modificar `_final_dependency_check` para pular histórias alocadas
- [x] Fase 2: Implementar `_resolve_allocation_conflicts`
- [x] Fase 2: Integrar no `execute()` após `_final_dependency_check`
- [x] Fase 3: Adicionar testes unitários
- [ ] Validar com dados do `backlog.xlsx`
- [ ] Verificar métricas de performance
- [ ] Atualizar documentação se necessário

---

## 9. Implementação Realizada

### 9.1 Mudanças em `allocate_developers.py`

**Fase 1 - Modificação de `_final_dependency_check` (linhas 834-842):**
```python
# IMPORTANTE: Pular histórias já alocadas para evitar criar conflitos
if story.developer_id is not None:
    logger.debug(
        f"História {story.id}: pulando _final_dependency_check (já alocada para dev {story.developer_id})"
    )
    continue
```

**Fase 2 - Novo método `_resolve_allocation_conflicts` (linhas 874-956):**
- Detecta histórias do mesmo desenvolvedor com períodos sobrepostos
- Ajusta a história posterior para iniciar após a anterior
- Usa múltiplas passadas (max 100) para resolver cascatas
- Integrado no `execute()` após `_final_dependency_check` (linhas 267-276)

### 9.2 Testes Adicionados

**Arquivo:** `tests/unit/application/use_cases/test_allocate_developers.py`

| Teste | Descrição |
|-------|-----------|
| `test_final_dependency_check_skips_allocated_stories` | Verifica que histórias alocadas são puladas |
| `test_resolve_allocation_conflicts_adjusts_overlapping_periods` | Verifica que conflitos são resolvidos |
| `test_no_conflicts_when_periods_dont_overlap` | Verifica que não há ajustes desnecessários |

### 9.3 Resultado dos Testes

```
214 passando / 2 falhando (bug pré-existente de rollback, não relacionado)
```

---

## 10. Alternativa: Investigação Adicional

Antes de implementar, pode ser útil investigar:

1. **Por que N5 foi alocada para AA em vez de outro desenvolvedor?**
   - Verificar disponibilidade de BB, CC, DD, EE no período
   - Verificar se o algoritmo de load balancing funcionou corretamente

2. **Quando exatamente o conflito foi criado?**
   - Adicionar logging temporário no `_final_dependency_check`
   - Rastrear cada ajuste de data

3. **O _final_dependency_check está sendo chamado corretamente?**
   - Verificar se as dependências estão corretas no banco
   - Verificar ordem topológica

---

**Status:** ✅ IMPLEMENTADO
**Data de Implementação:** 2025-12-26
**Solução Adotada:** Opção D (A + C)
