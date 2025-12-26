# Plano de Correção: Bug de Ondas Iniciando Simultaneamente

> **STATUS: PROPOSTA A APROVADA**
>
> Data de aprovação: 2024-12-26
> Versão: 3.0

---

## 1. Descrição do Bug

### 1.1 Comportamento Observado

Histórias de ondas diferentes estão recebendo a mesma data de início. Exemplo:
- **N1** (onda 1) inicia em 2024-12-26
- **T1** (onda 3) inicia em 2024-12-26

### 1.2 Comportamento Esperado

Ondas devem ser janelas temporais **exclusivas e sequenciais**:
- Onda 1: inicia em 2024-12-26, termina em 2025-01-10
- Onda 2: inicia em 2025-01-13 (após onda 1), termina em 2025-01-24
- Onda 3: inicia em 2025-01-27 (após onda 2), termina em ...

### 1.3 Impacto

- Viola o requisito principal de alocação por onda (RF-ALOC-001)
- Desenvolvedores podem ser alocados em histórias de ondas diferentes simultaneamente
- Planejamento de entregas por onda fica comprometido

---

## 2. Análise da Causa Raiz

### 2.1 Fluxo Atual

```
CalculateScheduleUseCase.execute()
│
├─ 1. Desaloca todos os desenvolvedores    ← Limpa developer_id de todas as histórias
├─ 2. BacklogSorter.sort()                 ← Ordena por dependências → onda → prioridade
├─ 3. ScheduleCalculator.calculate()       ← Calcula datas
│      └─ Para cada história:
│           earliest_start = max(
│               start_date_global,           ← Sempre usado como base
│               dev_last_end + 1,            ← NUNCA usado (devs desalocados!)
│               max(deps.end_date) + 1       ← Só dependências EXPLÍCITAS
│           )
└─ 4. Salva histórias
```

### 2.2 O Problema Central

O `ScheduleCalculator.calculate()` determina `earliest_start` considerando:

| Fator | Considerado? | Observação |
|-------|--------------|------------|
| Data global de início | ✅ Sim | `start_date` passado como parâmetro |
| Última história do dev | ❌ **Não funciona** | Devs são desalocados ANTES do cálculo |
| Dependências explícitas | ✅ Sim | Histórias listadas em `story.dependencies` |
| **Onda (wave)** | ❌ **Não** | **Não há barreira temporal entre ondas** |

**Descoberta crítica:** A verificação `dev_last_end_date` (linhas 82-85 do ScheduleCalculator) é **inútil** neste fluxo porque `CalculateScheduleUseCase` desaloca todos os desenvolvedores antes de chamar `calculate()`.

### 2.3 Por que isso acontece?

1. O `BacklogSorter` ordena corretamente: onda 1 → onda 2 → onda 3
2. O `ScheduleCalculator` processa na ordem correta
3. **MAS** ao calcular `earliest_start`, não considera a onda
4. Se T1 (onda 3) não tem dependência explícita de histórias anteriores, usa `start_date_global`

---

## 3. Mapeamento do Conceito de Onda

### 3.1 Onde "wave" é definida

```
Feature.wave (int > 0)        → Definida na entidade Feature
       ↓
Story.wave (property)         → Retorna feature.wave ou 0 se não houver feature
       ↓
BacklogSorter._composite_priority() → Usa wave * 10000 + priority para ordenar
       ↓
AllocateDevelopersUseCase     → Agrupa e processa por wave
```

### 3.2 Regras de Wave

| Situação | Valor de wave | Comportamento |
|----------|---------------|---------------|
| História COM feature | `feature.wave` (>= 1) | Incluída na alocação por onda |
| História SEM feature | `0` | **Excluída da alocação por onda!** |

**Código relevante** (`allocate_developers.py:216`):
```python
waves = sorted(set(s.wave for s in all_stories if s.feature is not None))
```

### 3.3 Ondas Não Contíguas

O sistema permite ondas não contíguas (ex: 1, 3, 5 sem 2 e 4). Isso ocorre quando:
- Features são criadas com waves específicas
- Features são deletadas, deixando gaps

---

## 4. Requisitos da Correção

### 4.1 Regras de Negócio Confirmadas

1. **Ondas são janelas temporais exclusivas** - não podem se sobrepor
2. **Sequenciamento de ondas** - onda N+1 só inicia após onda N terminar
3. **Histórias dentro da onda** - podem ter qualquer data dentro da janela da onda
4. **Dependências entre ondas** - devem ser respeitadas (já funciona)
5. **Ondas não contíguas** - onda 3 aguarda onda 1 se não existir onda 2

### 4.2 Definição de "Onda Terminar"

**Pergunta conceitual:** Quando uma onda "termina"?

| Opção | Definição | Implicação |
|-------|-----------|------------|
| A | Quando a última história da onda termina (`max(end_date)`) | Próxima onda inicia no dia útil seguinte |
| B | Quando todas as histórias alocadas terminam | Igual a A, mas considera apenas histórias com dev |
| C | Quando um % das histórias termina (ex: 80%) | Permite overlap controlado |

**Recomendação:** Opção A (mais simples e determinística)

### 4.3 Tratamento de Histórias sem Feature

**Pergunta:** O que fazer com histórias sem feature (wave = 0)?

| Opção | Comportamento | Implicação |
|-------|---------------|------------|
| 1 | Processar antes de todas as ondas | Wave 0 é tratada como "pré-onda" |
| 2 | Processar após todas as ondas | Wave 0 é "backlog futuro" |
| 3 | Ignorar no cálculo de cronograma | Histórias ficam sem data |
| 4 | Exigir feature obrigatória | Forçar usuário a associar |

**Recomendação:** Opção 1 (wave 0 como pré-onda, mantém compatibilidade)

---

## 5. Propostas de Correção

### 5.1 Proposta A: Barreira de Onda no ScheduleCalculator

**Onde:** `domain/services/schedule_calculator.py`

**Conceito:** Adicionar rastreamento de `wave_last_end_date` e usar como barreira.

```python
def calculate(self, stories, config, start_date):
    # ...
    wave_last_end_date: dict[int, date] = {}  # NOVO

    for story in stories:
        earliest_start = start_date

        # NOVO: Barreira de onda
        current_wave = story.wave
        if current_wave > 0:
            # Buscar a onda anterior EXISTENTE (não necessariamente current_wave - 1)
            prev_waves = [w for w in wave_last_end_date.keys() if w < current_wave]
            if prev_waves:
                prev_wave = max(prev_waves)  # Maior onda anterior
                wave_barrier = self._next_workday(wave_last_end_date[prev_wave])
                earliest_start = max(earliest_start, wave_barrier)

        # ... resto da lógica existente (dependências, etc.) ...

        # NOVO: Atualizar última data da onda
        if current_wave not in wave_last_end_date or story.end_date > wave_last_end_date[current_wave]:
            wave_last_end_date[current_wave] = story.end_date
```

**Prós:**
- Correção na camada de domínio (arquiteturalmente correto)
- Automática para qualquer chamada de `calculate()`
- Não modifica dados das histórias
- Suporta ondas não contíguas (busca maior onda anterior)

**Contras:**
- Assume que histórias chegam ordenadas por onda (garantido pelo BacklogSorter)
- `ScheduleCalculator` passa a depender do conceito de "onda" (acoplamento)

**Pré-requisito:**
- Histórias DEVEM ter `feature` carregada antes de `calculate()`

---

### 5.2 Proposta B: Processamento por Onda no CalculateScheduleUseCase

**Onde:** `application/use_cases/schedule/calculate_schedule.py`

**Conceito:** Processar ondas separadamente, passando a data de início correta para cada.

```python
def execute(self, start_date=None):
    # ... ordenar histórias ...

    # Agrupar por onda
    waves = {}
    for story in sorted_stories:
        waves.setdefault(story.wave, []).append(story)

    # Processar onda por onda
    all_scheduled = []
    wave_start = effective_start_date
    for wave_num in sorted(waves.keys()):
        wave_stories = waves[wave_num]

        # Calcular cronograma desta onda
        # NOTA: Precisa passar story_map completo para dependências cross-wave
        self._schedule_calculator.calculate(
            wave_stories,
            config,
            wave_start,
            all_stories_map=story_map  # NOVO parâmetro
        )
        all_scheduled.extend(wave_stories)

        # Próxima onda inicia após esta
        wave_end = max(s.end_date for s in wave_stories)
        wave_start = self._schedule_calculator._next_workday(wave_end)
```

**Prós:**
- Não modifica `ScheduleCalculator` (exceto novo parâmetro)
- Explícito sobre o processamento por onda
- Mais fácil de debugar

**Contras:**
- Lógica de "barreira de onda" na camada de aplicação (menos ideal)
- Requer modificar `ScheduleCalculator.calculate()` para receber `all_stories_map`
- Dependências cross-wave precisam de tratamento especial
- Duplicação de lógica com `AllocateDevelopersUseCase`

**Problema Crítico:** Dependências cross-wave não funcionam se `story_map` só contém histórias da onda atual.

---

### 5.3 Proposta C: Dependências Implícitas entre Ondas

**Onde:** `domain/services/backlog_sorter.py` ou novo serviço

**Conceito:** Criar dependências automáticas para representar a barreira de onda.

```python
def add_wave_dependencies(stories):
    """
    Adiciona dependência implícita: primeira história de cada onda
    depende da última história da onda anterior.
    """
    waves = group_by_wave(stories)

    for wave_num in sorted(waves.keys())[1:]:  # pula onda 1
        prev_wave = wave_num - 1
        last_of_prev = get_last_story_of_wave(waves[prev_wave])
        first_of_current = get_first_story_of_wave(waves[wave_num])

        first_of_current.dependencies.append(last_of_prev.id)
```

**Prós:**
- Usa mecanismo existente de dependências
- Funciona com toda a lógica já implementada

**Contras:**
- Modifica dados das histórias (pode causar confusão)
- Difícil determinar qual é a "última" história de uma onda (antes do cálculo de datas!)
- Pode criar problemas com detecção de ciclos
- Dependências "falsas" aparecem na UI
- Ondas não contíguas precisam de tratamento especial

**Problema Crítico:** Não é possível saber qual é a "última" história de uma onda antes de calcular as datas.

---

### 5.4 Proposta D: Duas Passagens no ScheduleCalculator

**Onde:** `domain/services/schedule_calculator.py`

**Conceito:** Primeira passagem calcula datas ignorando ondas, segunda passagem ajusta.

```python
def calculate(self, stories, config, start_date):
    # Passagem 1: Cálculo normal (como hoje)
    self._calculate_basic(stories, config, start_date)

    # Passagem 2: Ajustar para respeitar barreiras de onda
    self._apply_wave_barriers(stories)

def _apply_wave_barriers(self, stories):
    """Ajusta datas para garantir que ondas não se sobreponham."""
    wave_end_dates = self._get_wave_end_dates(stories)

    # Processar ondas em ordem
    for story in stories:
        if story.wave > 0:
            prev_waves = [w for w in wave_end_dates.keys() if w < story.wave]
            if prev_waves:
                prev_wave = max(prev_waves)
                prev_wave_end = wave_end_dates[prev_wave]
                if story.start_date <= prev_wave_end:
                    # Ajustar para dia seguinte ao fim da onda anterior
                    story.start_date = self._next_workday(prev_wave_end)
                    story.end_date = self.add_workdays(story.start_date, story.duration - 1)
                    # Atualizar end_date da onda atual
                    if story.wave not in wave_end_dates or story.end_date > wave_end_dates[story.wave]:
                        wave_end_dates[story.wave] = story.end_date
```

**Prós:**
- Separa lógica de cálculo básico da lógica de onda
- Mais fácil de testar cada parte

**Contras:**
- Duas passagens = mais processamento
- Segunda passagem pode gerar "efeito cascata" se não processada corretamente
- Precisa recalcular `wave_end_dates` durante a segunda passagem
- Complexidade adicional

---

## 6. Comparação das Propostas

| Critério | A (Barreira) | B (UseCase) | C (Deps) | D (2 Passagens) |
|----------|--------------|-------------|----------|-----------------|
| Camada correta | ✅ Domain | ⚠️ Application | ✅ Domain | ✅ Domain |
| Simplicidade | ✅ Alta | ⚠️ Média | ❌ Baixa | ⚠️ Média |
| Não modifica dados | ✅ | ✅ | ❌ | ✅ |
| Deps cross-wave | ✅ | ❌ Problemático | ✅ | ✅ |
| Ondas não contíguas | ✅ | ✅ | ⚠️ | ✅ |
| Testabilidade | ✅ | ⚠️ | ⚠️ | ✅ |
| Performance | ✅ O(n) | ✅ O(n) | ⚠️ O(n) | ⚠️ O(2n) |
| Viabilidade | ✅ | ❌ | ❌ | ⚠️ |

---

## 7. Considerações Adicionais

### 7.1 Dependências entre Ondas

**Pergunta:** O que acontece se uma história da onda 3 depende de uma história da onda 1?

**Resposta:** Funciona corretamente com Proposta A:
```
earliest_start = max(
    start_date_global,      # ex: 2024-12-26
    wave_barrier,           # ex: 2025-01-15 (fim onda 2 + 1)
    dependency_end + 1      # ex: 2025-01-05 (fim da dep na onda 1)
)
# Resultado: 2025-01-15 (wave_barrier é maior)
```

### 7.2 Ondas Não Contíguas

**Pergunta:** O que acontece se não há histórias na onda 2?

**Cenário:** Ondas existentes são [1, 3]

**Com Proposta A:**
- Onda 1: processada normalmente
- Onda 3: `prev_waves = [1]`, usa barreira da onda 1

**Não há problema:** A busca por "maior onda anterior" funciona corretamente.

### 7.3 Histórias sem Feature (wave = 0)

**Com Proposta A:**
- Wave 0 é processada primeiro (se ordenado corretamente)
- Outras ondas usam wave 0 como barreira? Ou ignoram?

**Recomendação:** Wave 0 deve ser tratada como onda especial que:
- Inicia no `start_date_global`
- Não bloqueia outras ondas (ondas >= 1 usam apenas outras ondas >= 1 como barreira)

```python
# Ajuste na Proposta A:
if current_wave > 0:
    prev_waves = [w for w in wave_last_end_date.keys() if 0 < w < current_wave]
    # ...
```

### 7.4 Pré-requisito: Feature Carregada

O `ScheduleCalculator` precisa acessar `story.wave`, que depende de `story.feature`.

**Verificação:** O `CalculateScheduleUseCase` carrega features?

**Resposta: SIM.** O `SQLiteStoryRepository.find_all()` carrega features automaticamente:

```python
# sqlite_story_repository.py:119-137
def find_all(self) -> List[Story]:
    # ...
    stories = [self._row_to_entity(row) for row in rows]
    self._load_features_bulk(stories)  # ← Carrega features em bulk
    return stories
```

**Risco mitigado:** Features são carregadas pelo repository via `_load_features_bulk()`.

### 7.5 Impacto em Testes Existentes

**Testes que podem quebrar:**
- `test_schedule_calculator.py` - Se assumem que histórias de ondas diferentes podem ter mesma data
- Testes de integração que verificam datas específicas

**Novos testes necessários:**
- Histórias de ondas diferentes não se sobrepõem
- Ondas não contíguas funcionam corretamente
- Dependências cross-wave respeitam tanto a dependência quanto a barreira de onda
- Histórias sem feature (wave = 0) são tratadas corretamente

---

## 8. Análise de Risco

### 8.1 Riscos da Proposta A

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Features não carregadas | Média | Alto | Verificar em CalculateScheduleUseCase |
| Histórias fora de ordem | Baixa | Alto | BacklogSorter garante ordem |
| Regressão em testes | Alta | Médio | Atualizar testes afetados |
| Acoplamento wave/schedule | Baixa | Baixo | Documentar dependência |

### 8.2 Pontos de Atenção

1. **Performance:** O impacto é O(n) - aceitável
2. **Manutenibilidade:** Lógica fica encapsulada em ScheduleCalculator
3. **Testabilidade:** Fácil de testar unitariamente
4. **Compatibilidade:** Não quebra interface pública

---

## 9. Recomendação Final

**Proposta A (Barreira de Onda no ScheduleCalculator)** é a mais adequada:

1. ✅ Implementação na camada de domínio
2. ✅ Simples e direta
3. ✅ Não modifica dados das histórias
4. ✅ Funciona com dependências cross-wave
5. ✅ Suporta ondas não contíguas
6. ✅ Performance O(n)

### 9.1 Ajustes Necessários na Proposta A

1. **Wave 0:** Ignorar como barreira para outras ondas
2. **Features:** Garantir que estão carregadas antes do cálculo
3. **Ordenação:** Documentar que histórias devem vir ordenadas por onda

### 9.2 Pontos Resolvidos

1. ✅ **Acoplamento:** Aceitável - wave é conceito de domínio
2. ✅ **Ondas vazias:** Buscar maior onda anterior existente
3. ✅ **Primeira onda:** Wave 1+ inicia após wave 0 (se houver) ou no start_date
4. ✅ **Histórias sem feature:** Wave 0 é processada mas não bloqueia outras

---

## 10. Detalhamento da Implementação

### 10.1 Arquivo a Modificar

`backlog_manager/domain/services/schedule_calculator.py`

### 10.2 Código Completo Proposto

```python
def calculate(
    self, stories: list[Story], config: Configuration, start_date: date | None = None
) -> list[Story]:
    """
    Calcula cronograma completo para lista de histórias.

    Args:
        stories: Histórias ordenadas (deve estar em ordem topológica por onda)
        config: Configuração com velocidade do time
        start_date: Data de início do projeto (padrão: hoje)

    Returns:
        Lista de histórias com datas e durações calculadas

    Note:
        Histórias DEVEM ter feature carregada para que story.wave funcione.
        Ondas são usadas como barreira temporal: onda N+1 só inicia após onda N.
    """
    if not stories:
        return []

    if start_date is None:
        start_date = date.today()

    # Garantir que start_date seja um dia útil
    start_date = self._ensure_workday(start_date)

    # Rastrear última data de fim por desenvolvedor
    dev_last_end_date: dict[str, date] = {}

    # NOVO: Rastrear última data de fim por onda (barreira temporal)
    wave_last_end_date: dict[int, date] = {}

    # Mapear histórias por ID para consulta rápida
    story_map: dict[str, Story] = {s.id: s for s in stories}

    # Processar cada história
    for story in stories:
        # Calcular duração em dias úteis baseada em SP e velocidade
        story.duration = self._calculate_duration(story.story_point.value, config)

        # Determinar data de início considerando múltiplas restrições
        earliest_start = start_date

        # NOVO: Verificar barreira de onda (ondas >= 1 bloqueiam entre si)
        current_wave = story.wave
        if current_wave > 0:
            # Buscar a maior onda anterior EXISTENTE (suporta ondas não contíguas)
            # Wave 0 é ignorada como barreira
            prev_waves = [w for w in wave_last_end_date.keys() if 0 < w < current_wave]
            if prev_waves:
                prev_wave = max(prev_waves)
                wave_barrier = self._next_workday(wave_last_end_date[prev_wave])
                earliest_start = max(earliest_start, wave_barrier)

        # Verificar última história do desenvolvedor
        if story.developer_id and story.developer_id in dev_last_end_date:
            earliest_start = max(
                earliest_start, self._next_workday(dev_last_end_date[story.developer_id])
            )

        # Verificar dependências - história só pode começar
        # após TODAS as dependências terminarem
        if story.dependencies:
            for dep_id in story.dependencies:
                dep_story = story_map.get(dep_id)
                if dep_story and dep_story.end_date:
                    dep_next_day = self._next_workday(dep_story.end_date)
                    earliest_start = max(earliest_start, dep_next_day)

        # Garantir que earliest_start seja um dia útil
        earliest_start = self._ensure_workday(earliest_start)

        story.start_date = earliest_start

        # Calcular data de fim
        story.end_date = self.add_workdays(story.start_date, story.duration - 1)

        # Atualizar última data de fim do desenvolvedor
        if story.developer_id:
            dev_last_end_date[story.developer_id] = story.end_date

        # NOVO: Atualizar última data de fim da onda
        if current_wave not in wave_last_end_date or story.end_date > wave_last_end_date[current_wave]:
            wave_last_end_date[current_wave] = story.end_date

    return stories
```

### 10.3 Mudanças Específicas

| Linha | Mudança | Descrição |
|-------|---------|-----------|
| +1 | `wave_last_end_date: dict[int, date] = {}` | Novo dicionário para rastrear fim de cada onda |
| +2 | `current_wave = story.wave` | Captura wave da história atual |
| +3 | `if current_wave > 0:` | Só aplica barreira para waves >= 1 |
| +4 | `prev_waves = [...]` | Busca ondas anteriores (exclui wave 0) |
| +5 | `wave_barrier = self._next_workday(...)` | Calcula barreira temporal |
| +6 | `earliest_start = max(...)` | Aplica barreira se existir |
| +7 | `if current_wave not in wave_last_end_date...` | Atualiza end_date da onda |

---

## 11. Cenários de Teste

### 11.1 Testes Unitários

#### Teste 1: Barreira Básica entre Ondas
```python
def test_wave_barrier_prevents_overlap():
    """Histórias de ondas diferentes não podem ter datas sobrepostas."""
    # Given
    story1 = create_story(id="S1", wave=1, story_points=5)  # ~4 dias
    story2 = create_story(id="S2", wave=2, story_points=3)  # ~3 dias

    # When
    result = calculator.calculate([story1, story2], config, date(2024, 12, 26))

    # Then
    assert result[1].start_date > result[0].end_date
```

#### Teste 2: Ondas Não Contíguas
```python
def test_non_contiguous_waves():
    """Onda 3 deve aguardar onda 1 se não existir onda 2."""
    story1 = create_story(id="S1", wave=1)
    story3 = create_story(id="S3", wave=3)  # Pula wave 2

    result = calculator.calculate([story1, story3], config, start_date)

    assert result[1].start_date > result[0].end_date
```

#### Teste 3: Wave 0 Não Bloqueia
```python
def test_wave_zero_does_not_block():
    """Histórias sem feature (wave=0) não bloqueiam outras ondas."""
    story0 = create_story(id="S0", wave=0, story_points=13)  # 10 dias
    story1 = create_story(id="S1", wave=1, story_points=3)

    result = calculator.calculate([story0, story1], config, date(2024, 12, 26))

    # Story1 deve iniciar no start_date, não após story0
    assert result[1].start_date == date(2024, 12, 26)
```

#### Teste 4: Dependência Cross-Wave
```python
def test_dependency_and_wave_barrier():
    """A maior restrição prevalece: dependência ou barreira de onda."""
    story1 = create_story(id="S1", wave=1, story_points=5)
    story2 = create_story(id="S2", wave=1, story_points=8)
    story3 = create_story(id="S3", wave=2, dependencies=["S1"])

    result = calculator.calculate([story1, story2, story3], config, start_date)

    # Story3 deve aguardar wave 1 terminar (S2), não apenas S1
    assert result[2].start_date > result[1].end_date
```

#### Teste 5: Múltiplas Histórias na Mesma Onda
```python
def test_multiple_stories_same_wave():
    """Histórias da mesma onda podem iniciar na mesma data."""
    story1 = create_story(id="S1", wave=1)
    story2 = create_story(id="S2", wave=1)  # Mesma onda, sem deps

    result = calculator.calculate([story1, story2], config, start_date)

    # Ambas podem iniciar na mesma data (sem dependência entre elas)
    assert result[0].start_date == result[1].start_date
```

#### Teste 6: Onda Atualiza End Date Progressivamente
```python
def test_wave_end_date_updates():
    """A última história da onda define o end_date da onda."""
    story1 = create_story(id="S1", wave=1, story_points=3)  # Curta
    story2 = create_story(id="S2", wave=1, story_points=13)  # Longa
    story3 = create_story(id="S3", wave=2)

    result = calculator.calculate([story1, story2, story3], config, start_date)

    # Story3 deve aguardar story2 (a mais longa da wave 1)
    assert result[2].start_date > result[1].end_date
```

### 11.2 Fixture Helper

```python
def create_story(
    id: str,
    wave: int = 1,
    story_points: int = 5,
    dependencies: list[str] = None
) -> Story:
    """Cria história com feature mockada para testes."""
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

---

## 12. Checklist de Implementação

### 12.1 Pré-Implementação
- [x] Proposta aprovada
- [x] Verificar que `find_all()` carrega features
- [ ] Revisar testes existentes de `ScheduleCalculator`

### 12.2 Implementação
- [ ] Adicionar `wave_last_end_date` ao `calculate()`
- [ ] Implementar lógica de barreira de onda
- [ ] Garantir que wave 0 não bloqueia
- [ ] Suportar ondas não contíguas
- [ ] Atualizar docstring do método

### 12.3 Testes
- [ ] Criar testes unitários (6 cenários)
- [ ] Executar testes existentes
- [ ] Verificar regressões

### 12.4 Validação
- [ ] Teste manual na aplicação
- [ ] Verificar logs de debug
- [ ] Validar com dados reais

---

## 13. Análise de Risco (Atualizada)

| Risco | Probabilidade | Impacto | Mitigação | Status |
|-------|---------------|---------|-----------|--------|
| Features não carregadas | ~~Média~~ | ~~Alto~~ | ~~Verificar em UseCase~~ | ✅ **Mitigado** |
| Histórias fora de ordem | Baixa | Alto | BacklogSorter garante ordem | ⚠️ Monitorar |
| Regressão em testes | Alta | Médio | Executar suite completa | 🔄 Pendente |
| Acoplamento wave/schedule | Baixa | Baixo | Documentar dependência | ✅ Aceitável |

---

## 14. Próximos Passos

1. [x] Aprovar proposta A com ajustes
2. [x] Verificar se `find_all()` carrega features
3. [ ] Implementar barreira de onda no `ScheduleCalculator`
4. [ ] Escrever testes para cenários de onda
5. [ ] Executar testes existentes
6. [ ] Testar na aplicação
7. [ ] Commit e documentação

---

**Data:** 2024-12-26
**Versão:** 3.0 (Proposta A aprovada, detalhamento completo)
**Status:** Pronto para implementação
