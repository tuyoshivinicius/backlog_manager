# Plano: Remover Barreira Temporal Entre Ondas

> **Objetivo:** Permitir que desenvolvedores livres adiantem histórias da próxima onda, sem esperar que todas as histórias da onda anterior terminem.
>
> **Data:** 2025-12-26

---

## 1. Situação Atual

### 1.1 Comportamento Atual

```
Onda 1:
  - Story1-A (Dev Ana): [01/01 - 05/01]
  - Story1-B (Dev Bruno): [01/01 - 10/01]  ← última da onda 1

Onda 2 (BARREIRA ATUAL):
  - Story2-A: [13/01 - ...]  ← Só inicia após 10/01 (fim de Story1-B)

PROBLEMA: Ana ficou ociosa de 06/01 a 12/01 (5 dias úteis)
          Ela poderia ter adiantado Story2-A!
```

### 1.2 Código da Barreira

**Arquivo:** `backlog_manager/domain/services/schedule_calculator.py`

**Linhas 91-101:**
```python
# Verificar barreira de onda (wave barrier)
current_wave = story.wave
if current_wave > 0:
    prev_waves = [w for w in wave_last_end_date.keys() if 0 < w < current_wave]
    if prev_waves:
        prev_wave = max(prev_waves)
        wave_barrier = self._next_workday(wave_last_end_date[prev_wave])
        earliest_start = max(earliest_start, wave_barrier)  # ← BARREIRA!
```

---

## 2. Comportamento Desejado

### 2.1 Novo Fluxo

```
Onda 1:
  - Story1-A (Dev Ana): [01/01 - 05/01]
  - Story1-B (Dev Bruno): [01/01 - 10/01]

Onda 2 (SEM BARREIRA):
  - Story2-A (Dev Ana): [06/01 - ...]  ← Ana adiantou! Inicia logo após terminar Story1-A
  - Story2-B (Dev Bruno): [13/01 - ...]  ← Bruno continua após Story1-B

RESULTADO: Ana não fica ociosa, onda 2 termina mais cedo!
```

### 2.2 Regras a Manter

1. **Dependências:** Histórias ainda devem respeitar suas dependências
2. **Disponibilidade:** Um desenvolvedor só pode trabalhar em uma história por vez
3. **Critério de alocação:** `max_idle_days`, `DEPENDENCY_OWNER`, `LOAD_BALANCING` continuam funcionando
4. **Prioridade:** Histórias de menor prioridade (dentro da onda) devem ser processadas primeiro

### 2.3 Decisão de Design

**Pergunta:** As ondas devem ter alguma restrição entre si?

| Opção | Descrição |
|-------|-----------|
| **A) Sem restrição** | Ondas são apenas agrupamentos lógicos, sem impacto no schedule |
| **B) Dependência de início** | Onda N só pode INICIAR após onda N-1 iniciar (mas não precisa terminar) |
| **C) Prioridade de onda** | Histórias de onda menor têm prioridade, mas não bloqueiam |

**Recomendação:** Opção A (sem restrição) - mais simples e atende ao requisito.

---

## 3. Arquivos a Modificar

### 3.1 Mudanças Obrigatórias

| Arquivo | Mudança |
|---------|---------|
| `schedule_calculator.py` | Remover/comentar linhas 91-101 (barreira de onda) |
| `schedule_calculator.py` | Remover/comentar linhas 134-136 (atualização de `wave_last_end_date`) |

### 3.2 Verificações Necessárias

| Arquivo | Verificar |
|---------|-----------|
| `allocate_developers.py` | Processamento por onda ainda faz sentido? |
| `backlog_sorter.py` | Ordenação considera onda - manter ou remover? |
| `idleness_detector.py` | Detecção de ociosidade "entre ondas" ainda é relevante? |

### 3.3 Testes a Atualizar

| Arquivo | Testes |
|---------|--------|
| `test_schedule_calculator.py` | `test_wave_barrier_prevents_overlap` |
| `test_schedule_calculator.py` | `test_non_contiguous_waves` |
| `test_schedule_calculator.py` | `test_dependency_and_wave_barrier` |
| `test_schedule_calculator.py` | `test_wave_end_date_uses_latest_story` |

---

## 4. Plano de Implementação

### Fase 1: Remover Barreira no ScheduleCalculator

**Arquivo:** `backlog_manager/domain/services/schedule_calculator.py`

#### 1.1 Remover variável de rastreamento

```python
# ANTES (linha 75):
wave_last_end_date: dict[int, date] = {}

# DEPOIS:
# (remover ou comentar - não é mais necessário)
```

#### 1.2 Remover lógica da barreira

```python
# ANTES (linhas 91-101):
current_wave = story.wave
if current_wave > 0:
    prev_waves = [w for w in wave_last_end_date.keys() if 0 < w < current_wave]
    if prev_waves:
        prev_wave = max(prev_waves)
        wave_barrier = self._next_workday(wave_last_end_date[prev_wave])
        earliest_start = max(earliest_start, wave_barrier)

# DEPOIS:
# (remover completamente - ondas não bloqueiam mais)
```

#### 1.3 Remover atualização do rastreamento

```python
# ANTES (linhas 134-136):
if current_wave not in wave_last_end_date or story.end_date > wave_last_end_date[current_wave]:
    wave_last_end_date[current_wave] = story.end_date

# DEPOIS:
# (remover - não é mais necessário)
```

### Fase 2: Revisar AllocateDevelopersUseCase

**Arquivo:** `backlog_manager/application/use_cases/schedule/allocate_developers.py`

#### 2.1 Decisão: Manter processamento por onda?

**Opção A: Manter processamento por onda**
- Vantagem: Mantém isolamento de deadlock por onda
- Vantagem: Código mais organizado
- Desvantagem: Pode não otimizar alocação entre ondas

**Opção B: Processar todas as histórias juntas**
- Vantagem: Otimização global da alocação
- Desvantagem: Deadlock em uma história pode travar tudo
- Desvantagem: Mudança mais complexa

**Recomendação:** Manter processamento por onda (Opção A) - mudança mínima.

#### 2.2 Ajuste necessário (se manter por onda)

O processamento por onda atual já funciona, mas as datas são calculadas pelo `CalculateScheduleUseCase` ANTES da alocação. Precisamos garantir que:

1. O `CalculateScheduleUseCase` (que usa `ScheduleCalculator`) não aplique barreira
2. O `AllocateDevelopersUseCase` continue processando onda por onda
3. As datas sejam recalculadas durante a alocação quando necessário

### Fase 3: Revisar BacklogSorter

**Arquivo:** `backlog_manager/domain/services/backlog_sorter.py`

#### 3.1 Ordenação atual

O `BacklogSorter` ordena por:
1. Onda (menor primeiro)
2. Prioridade (menor primeiro)
3. Dependências (topológica)

**Decisão:** Manter ordenação por onda?

| Opção | Comportamento |
|-------|---------------|
| **Manter** | Histórias de onda 1 são processadas antes de onda 2, mas sem barreira de data |
| **Remover** | Histórias são ordenadas apenas por prioridade e dependências |

**Recomendação:** Manter ordenação por onda - garante que histórias de ondas anteriores tenham prioridade natural.

### Fase 4: Revisar IdlenessDetector

**Arquivo:** `backlog_manager/domain/services/idleness_detector.py`

#### 4.1 Método `detect_between_waves_idleness()`

Este método detecta ociosidade entre ondas. Com a remoção da barreira, essa detecção ainda faz sentido?

**Decisão:**
- Se ociosidade entre ondas era "permitida" (não era warning), agora não deveria mais ocorrer
- Podemos manter o método para detectar casos residuais
- Ou remover se não for mais relevante

**Recomendação:** Manter por enquanto, avaliar depois.

### Fase 5: Atualizar Testes

#### 5.1 Testes a REMOVER ou MODIFICAR

```python
# test_schedule_calculator.py

def test_wave_barrier_prevents_overlap():
    """REMOVER - barreira não existe mais"""

def test_non_contiguous_waves():
    """MODIFICAR - verificar que ondas não-contíguas funcionam sem barreira"""

def test_dependency_and_wave_barrier():
    """MODIFICAR - manter apenas teste de dependência, remover teste de barreira"""

def test_wave_end_date_uses_latest_story():
    """REMOVER - não rastreamos mais data final de onda"""
```

#### 5.2 Testes a ADICIONAR

```python
def test_developer_can_start_next_wave_early():
    """
    Verifica que desenvolvedor livre pode adiantar história da próxima onda.

    Cenário:
    - Story1 (wave 1, Dev A): [01/01 - 05/01]
    - Story2 (wave 1, Dev B): [01/01 - 10/01]
    - Story3 (wave 2, Dev A): deve iniciar [06/01], não [13/01]
    """

def test_waves_can_overlap():
    """
    Verifica que histórias de ondas diferentes podem executar em paralelo.
    """

def test_dependencies_still_respected_across_waves():
    """
    Verifica que dependências entre ondas ainda são respeitadas.
    """
```

---

## 5. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Dependências entre ondas quebram | Baixa | Alto | Manter verificação de dependências intacta |
| Ordenação topológica falha | Baixa | Alto | Manter BacklogSorter inalterado |
| Ociosidade não detectada | Média | Baixo | Revisar IdlenessDetector |
| Testes existentes falham | Alta | Baixo | Atualizar testes conforme Fase 5 |

---

## 6. Ordem de Execução

1. **Criar branch** para a mudança
2. **Fase 1:** Remover barreira no ScheduleCalculator
3. **Fase 5:** Atualizar testes (ANTES de rodar para ver falhas esperadas)
4. **Rodar testes** - verificar que apenas testes esperados falham
5. **Fase 2:** Revisar AllocateDevelopersUseCase (se necessário)
6. **Fase 3:** Revisar BacklogSorter (se necessário)
7. **Fase 4:** Revisar IdlenessDetector (se necessário)
8. **Rodar testes** - todos devem passar
9. **Teste manual** na aplicação
10. **Commit e merge**

---

## 7. Estimativa

| Fase | Complexidade |
|------|--------------|
| Fase 1 (ScheduleCalculator) | Baixa - remover ~15 linhas |
| Fase 2 (AllocateDevelopersUseCase) | Baixa - provavelmente sem mudanças |
| Fase 3 (BacklogSorter) | Nenhuma - manter como está |
| Fase 4 (IdlenessDetector) | Baixa - avaliar relevância |
| Fase 5 (Testes) | Média - ~4 testes a modificar, ~3 a adicionar |

---

## 8. Checklist de Implementação

- [ ] Remover barreira de onda no `ScheduleCalculator.calculate()`
- [ ] Remover variável `wave_last_end_date`
- [ ] Remover atualização de `wave_last_end_date`
- [ ] Atualizar/remover testes de barreira
- [ ] Adicionar testes de sobreposição de ondas
- [ ] Verificar que dependências ainda funcionam
- [ ] Verificar que alocação por critério ainda funciona
- [ ] Testar manualmente na aplicação
- [ ] Atualizar documentação (CLAUDE.md se necessário)

---

## 9. Implementação Realizada

### 9.1 Mudanças no ScheduleCalculator

**Arquivo:** `backlog_manager/domain/services/schedule_calculator.py`

1. **Removido:** Variável `wave_last_end_date` (linha 75)
2. **Removido:** Bloco de verificação de barreira de onda (linhas 91-101)
3. **Removido:** Atualização de `wave_last_end_date` (linhas 134-136)
4. **Adicionado:** Comentário explicativo sobre remoção da barreira

### 9.2 Testes Atualizados

**Arquivo:** `tests/unit/domain/test_schedule_calculator.py`

| Teste Original | Novo Nome | Mudança |
|----------------|-----------|---------|
| `test_wave_barrier_prevents_overlap` | `test_waves_can_overlap_without_barrier` | Verifica que ondas PODEM sobrepor |
| `test_non_contiguous_waves` | `test_non_contiguous_waves_can_overlap` | Verifica que ondas não-contíguas PODEM sobrepor |
| `test_dependency_and_wave_barrier` | `test_dependency_across_waves` | Verifica apenas dependências, não barreira |
| `test_wave_end_date_uses_latest_story` | `test_developer_can_start_next_wave_early` | Verifica que dev pode adiantar |

### 9.3 Testes Inalterados (continuam passando)

- `test_wave_zero_does_not_block` - Wave 0 não bloqueia (ainda válido)
- `test_multiple_stories_same_wave` - Histórias da mesma onda podem iniciar juntas

### 9.4 Resultado dos Testes

```
213 passando / 3 falhando (bug pré-existente de rollback, não relacionado)
```

---

## 10. Checklist Final

- [x] Remover barreira de onda no `ScheduleCalculator.calculate()`
- [x] Remover variável `wave_last_end_date`
- [x] Remover atualização de `wave_last_end_date`
- [x] Atualizar/remover testes de barreira
- [x] Adicionar testes de sobreposição de ondas
- [x] Verificar que dependências ainda funcionam
- [x] Verificar que alocação por critério ainda funciona
- [ ] Testar manualmente na aplicação
- [ ] Atualizar documentação (CLAUDE.md se necessário)

---

**Status:** ✅ IMPLEMENTADO
**Data:** 2025-12-26
**Decisão de design:** Opção A - Ondas são apenas agrupamentos lógicos, sem barreira temporal
