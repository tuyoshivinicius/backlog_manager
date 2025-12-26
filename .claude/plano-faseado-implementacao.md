# Plano Faseado de Implementação: Barreira de Onda

> **Referência:** `plano-corrigir-bug-alocacao.md` (Proposta A aprovada)
>
> **Objetivo:** Implementar barreira temporal entre ondas no `ScheduleCalculator`
>
> **Data:** 2024-12-26

---

## Visão Geral das Fases

| Fase | Nome | Descrição | Duração Estimada |
|------|------|-----------|------------------|
| 1 | Preparação | Revisar código e testes existentes | - |
| 2 | Implementação | Modificar `ScheduleCalculator` | - |
| 3 | Testes Unitários | Criar e executar testes | - |
| 4 | Validação | Testes de integração e regressão | - |
| 5 | Teste Manual | Validar na aplicação real | - |
| 6 | Finalização | Documentação e commit | - |

---

## Fase 1: Preparação

### 1.1 Objetivos
- Entender código atual do `ScheduleCalculator`
- Identificar testes existentes que podem ser afetados
- Preparar ambiente de testes

### 1.2 Tarefas

| # | Tarefa | Arquivo | Critério de Aceite |
|---|--------|---------|-------------------|
| 1.1 | Ler código atual do `calculate()` | `domain/services/schedule_calculator.py` | Entendimento completo do fluxo |
| 1.2 | Listar testes existentes | `tests/unit/domain/test_schedule_calculator.py` | Lista de testes que podem quebrar |
| 1.3 | Executar testes atuais | - | Todos passando (baseline) |
| 1.4 | Verificar se há testes com múltiplas ondas | - | Identificar gaps de cobertura |

### 1.3 Comandos
```bash
# Executar testes do ScheduleCalculator
./.venv/Scripts/python.exe -m pytest tests/unit/domain/test_schedule_calculator.py -v

# Ver cobertura atual
./.venv/Scripts/python.exe -m pytest tests/unit/domain/test_schedule_calculator.py -v --cov=backlog_manager.domain.services.schedule_calculator
```

### 1.4 Entregáveis
- [ ] Baseline de testes passando
- [ ] Lista de testes que podem ser afetados
- [ ] Entendimento do código atual documentado

---

## Fase 2: Implementação

### 2.1 Objetivos
- Implementar rastreamento de `wave_last_end_date`
- Adicionar lógica de barreira de onda
- Manter compatibilidade com código existente

### 2.2 Tarefas

| # | Tarefa | Descrição | Critério de Aceite |
|---|--------|-----------|-------------------|
| 2.1 | Adicionar dicionário `wave_last_end_date` | `wave_last_end_date: dict[int, date] = {}` | Variável declarada |
| 2.2 | Capturar wave da história | `current_wave = story.wave` | Wave acessível no loop |
| 2.3 | Implementar busca de onda anterior | `prev_waves = [w for w in ...]` | Suporta ondas não contíguas |
| 2.4 | Calcular barreira temporal | `wave_barrier = self._next_workday(...)` | Barreira calculada corretamente |
| 2.5 | Aplicar barreira ao `earliest_start` | `earliest_start = max(...)` | Barreira aplicada |
| 2.6 | Atualizar `wave_last_end_date` após cada história | `wave_last_end_date[current_wave] = ...` | End date atualizado |
| 2.7 | Garantir wave 0 não bloqueia | `if current_wave > 0` e `if 0 < w < current_wave` | Wave 0 ignorada |
| 2.8 | Atualizar docstring | Documentar novo comportamento | Docstring atualizada |

### 2.3 Código a Implementar

```python
# Linha ~65: Adicionar após dev_last_end_date
wave_last_end_date: dict[int, date] = {}

# Linha ~79: Adicionar ANTES da verificação de desenvolvedor
current_wave = story.wave
if current_wave > 0:
    prev_waves = [w for w in wave_last_end_date.keys() if 0 < w < current_wave]
    if prev_waves:
        prev_wave = max(prev_waves)
        wave_barrier = self._next_workday(wave_last_end_date[prev_wave])
        earliest_start = max(earliest_start, wave_barrier)

# Linha ~110: Adicionar APÓS atualização de dev_last_end_date
if current_wave not in wave_last_end_date or story.end_date > wave_last_end_date[current_wave]:
    wave_last_end_date[current_wave] = story.end_date
```

### 2.4 Ordem de Inserção

1. **Primeiro:** Adicionar `wave_last_end_date` (linha ~65)
2. **Segundo:** Adicionar lógica de barreira (antes de deps, linha ~79)
3. **Terceiro:** Atualizar `wave_last_end_date` (após dev update, linha ~110)
4. **Quarto:** Atualizar docstring

### 2.5 Entregáveis
- [ ] Código implementado
- [ ] Sem erros de sintaxe
- [ ] Código compila (`python -m py_compile`)

---

## Fase 3: Testes Unitários

### 3.1 Objetivos
- Criar testes para os 6 cenários definidos
- Garantir cobertura do novo código
- Validar comportamento esperado

### 3.2 Testes a Criar

| # | Nome do Teste | Cenário | Assertion Principal |
|---|---------------|---------|---------------------|
| 3.1 | `test_wave_barrier_prevents_overlap` | Ondas 1 e 2 não se sobrepõem | `story2.start > story1.end` |
| 3.2 | `test_non_contiguous_waves` | Onda 3 aguarda onda 1 (sem onda 2) | `story3.start > story1.end` |
| 3.3 | `test_wave_zero_does_not_block` | Wave 0 não bloqueia wave 1 | `story1.start == start_date` |
| 3.4 | `test_dependency_and_wave_barrier` | Maior restrição prevalece | `story3.start > story2.end` |
| 3.5 | `test_multiple_stories_same_wave` | Mesma onda, mesma data (sem deps) | `story1.start == story2.start` |
| 3.6 | `test_wave_end_date_updates` | Última história define fim da onda | `story3.start > story2.end` |

### 3.3 Arquivo de Teste

Adicionar ao arquivo: `tests/unit/domain/test_schedule_calculator.py`

### 3.4 Fixture Helper

```python
def create_story_with_wave(
    id: str,
    wave: int = 1,
    story_points: int = 5,
    dependencies: list[str] = None
) -> Story:
    """Cria história com feature mockada para testes de onda."""
    from backlog_manager.domain.entities.feature import Feature

    feature = Feature(id=f"F{wave}", name=f"Feature {wave}", wave=wave) if wave > 0 else None
    return Story(
        id=id,
        component="TEST",
        name=f"Story {id}",
        story_point=StoryPoint(story_points),
        feature_id=feature.id if feature else None,
        feature=feature,
        dependencies=dependencies or [],
    )
```

### 3.5 Comandos
```bash
# Executar apenas novos testes
./.venv/Scripts/python.exe -m pytest tests/unit/domain/test_schedule_calculator.py -v -k "wave"

# Executar todos os testes do módulo
./.venv/Scripts/python.exe -m pytest tests/unit/domain/test_schedule_calculator.py -v
```

### 3.6 Entregáveis
- [ ] 6 testes criados
- [ ] Todos os 6 testes passando
- [ ] Fixture helper funcionando

---

## Fase 4: Validação

### 4.1 Objetivos
- Garantir que testes existentes não quebraram
- Executar suite completa de testes
- Verificar integração com outros componentes

### 4.2 Tarefas

| # | Tarefa | Comando | Critério de Aceite |
|---|--------|---------|-------------------|
| 4.1 | Executar testes do ScheduleCalculator | `pytest tests/unit/domain/test_schedule_calculator.py -v` | Todos passando |
| 4.2 | Executar testes de domínio | `pytest tests/unit/domain/ -v` | Todos passando |
| 4.3 | Executar testes de use cases | `pytest tests/unit/application/ -v` | Todos passando |
| 4.4 | Executar testes de integração | `pytest tests/integration/ -v` | Todos passando |
| 4.5 | Executar suite completa | `pytest tests/ -v` | Todos passando |

### 4.3 Comandos
```bash
# Suite completa com resumo
./.venv/Scripts/python.exe -m pytest tests/ -v --tb=short

# Se falhar, ver detalhes
./.venv/Scripts/python.exe -m pytest tests/ -v --tb=long -x
```

### 4.4 Tratamento de Falhas

Se algum teste existente falhar:

1. **Analisar:** O teste está correto ou precisa ser atualizado?
2. **Se teste incorreto:** Teste assumia comportamento errado (ondas podiam sobrepor)
3. **Se código incorreto:** Revisar implementação da Fase 2
4. **Documentar:** Registrar qualquer ajuste feito

### 4.5 Entregáveis
- [ ] Todos os testes de domínio passando
- [ ] Todos os testes de application passando
- [ ] Todos os testes de integração passando
- [ ] Suite completa passando

---

## Fase 5: Teste Manual

### 5.1 Objetivos
- Validar correção na aplicação real
- Verificar que ondas não se sobrepõem
- Confirmar logs de debug

### 5.2 Preparação

```bash
# Iniciar aplicação em modo debug
./run_debug.bat
```

### 5.3 Roteiro de Teste

| # | Ação | Resultado Esperado |
|---|------|-------------------|
| 5.1 | Abrir aplicação | Aplicação inicia sem erros |
| 5.2 | Verificar histórias existentes | Histórias carregadas na tabela |
| 5.3 | Clicar em "Calcular Cronograma" | Cronograma calculado |
| 5.4 | Verificar histórias de ondas diferentes | Ondas não se sobrepõem temporalmente |
| 5.5 | Clicar em "Alocar Desenvolvedores" | Alocação executada |
| 5.6 | Verificar logs | Sem erros, comportamento correto |
| 5.7 | Verificar N1 e T1 | T1 (onda 3) inicia APÓS N1 (onda 1) |

### 5.4 Verificações Específicas

**Verificar no log:**
```
# Deve aparecer algo como:
DEBUG | Histórias ordenadas por onda
DEBUG | Onda 1: X histórias
DEBUG | Onda 2: Y histórias
DEBUG | Onda 3: Z histórias
```

**Verificar na UI:**
- Coluna "Início" de histórias de ondas diferentes
- Ondas posteriores devem ter datas posteriores

### 5.5 Entregáveis
- [ ] Aplicação funciona sem erros
- [ ] Ondas não se sobrepõem
- [ ] Bug original corrigido (N1 e T1 não iniciam na mesma data)

---

## Fase 6: Finalização

### 6.1 Objetivos
- Atualizar documentação
- Criar commit com mensagem descritiva
- Atualizar status do plano

### 6.2 Tarefas

| # | Tarefa | Descrição |
|---|--------|-----------|
| 6.1 | Atualizar docstring do ScheduleCalculator | Documentar barreira de onda |
| 6.2 | Atualizar CLAUDE.md se necessário | Adicionar informação sobre ondas |
| 6.3 | Marcar checklist como concluído | Atualizar `plano-corrigir-bug-alocacao.md` |
| 6.4 | Criar commit | Mensagem descritiva |

### 6.3 Template de Commit

```bash
git add backlog_manager/domain/services/schedule_calculator.py
git add tests/unit/domain/test_schedule_calculator.py

git commit -m "$(cat <<'EOF'
fix: Implementar barreira temporal entre ondas no ScheduleCalculator

- Adiciona rastreamento de wave_last_end_date para cada onda
- Histórias de onda N+1 só iniciam após onda N terminar
- Wave 0 (histórias sem feature) não bloqueia outras ondas
- Suporta ondas não contíguas (ex: 1, 3, 5 sem 2, 4)

Corrige bug onde histórias de ondas diferentes (ex: N1 e T1)
podiam iniciar na mesma data, violando RF-ALOC-001.

Closes #XXX

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 6.4 Entregáveis
- [ ] Docstring atualizada
- [ ] Commit criado
- [ ] Plano marcado como concluído

---

## Diagrama de Dependências entre Fases

```
Fase 1 (Preparação)
    │
    ▼
Fase 2 (Implementação)
    │
    ▼
Fase 3 (Testes Unitários)
    │
    ▼
Fase 4 (Validação)
    │
    ├──────────────────┐
    ▼                  ▼
Fase 5 (Manual)    (Paralelo se quiser)
    │
    ▼
Fase 6 (Finalização)
```

---

## Critérios de Conclusão

A implementação está **completa** quando:

1. ✅ Código implementado no `ScheduleCalculator`
2. ✅ 6 testes unitários passando
3. ✅ Suite completa de testes passando (sem regressões)
4. ✅ Teste manual confirma correção do bug
5. ✅ Commit criado com mensagem descritiva

---

## Rollback

Se houver problemas críticos:

```bash
# Reverter alterações não commitadas
git checkout -- backlog_manager/domain/services/schedule_calculator.py

# Se já commitou, reverter commit
git revert HEAD
```

---

**Status:** Pronto para execução
**Próximo passo:** Iniciar Fase 1
