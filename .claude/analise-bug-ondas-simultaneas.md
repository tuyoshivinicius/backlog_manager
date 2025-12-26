# Análise do Bug: Ondas Iniciando Simultaneamente

## 1. Resumo Executivo

**Bug Crítico Identificado:** Histórias de ondas diferentes (ex: T1 da onda 3 e N1 da onda 1) estão iniciando na mesma data, violando o requisito fundamental de que a alocação deve ser feita por onda, com ondas posteriores iniciando apenas após as anteriores.

**Impacto:** Alto - Viola o requisito principal de alocação de desenvolvedores por onda (RF-ALOC-001).

**Causa Raiz:** O `ScheduleCalculator` calcula datas baseado apenas em dependências explícitas entre histórias, não considerando ondas (waves) como barreira temporal implícita.

---

## 2. Evidência do Bug

### 2.1 Comportamento Observado

Ao executar a alocação de desenvolvedores:
- História **N1** (onda 1) inicia em uma determinada data
- História **T1** (onda 3) inicia **na mesma data** que N1
- Isso ocorre porque T1 não possui dependência explícita de N1 ou qualquer história de ondas anteriores

### 2.2 Comportamento Esperado

De acordo com o requisito RF-ALOC-001:
- Histórias da **onda 1** devem ser processadas primeiro
- Histórias da **onda 2** devem iniciar apenas **após** todas as histórias da onda 1 terminarem (ou suas dependências específicas)
- Histórias da **onda 3** devem seguir a mesma lógica

---

## 3. Análise Técnica Detalhada

### 3.1 Fluxo de Execução Atual

```
CalculateScheduleUseCase.execute()
    │
    ├── 1. Buscar histórias e configuração
    ├── 2. Desalocar todos os desenvolvedores (reset)
    ├── 3. Ordenar histórias com BacklogSorter.sort()
    │      └── Ordena por: dependências → onda → prioridade
    ├── 4. Calcular datas com ScheduleCalculator.calculate()
    │      └── Considera APENAS: desenvolvedor + dependências
    └── 5. Salvar histórias
```

### 3.2 Problema no ScheduleCalculator

**Arquivo:** `backlog_manager/domain/services/schedule_calculator.py`

**Método:** `calculate()` (linhas 41-112)

```python
def calculate(self, stories: list[Story], config: Configuration, start_date: date | None = None) -> list[Story]:
    # ...
    for story in stories:
        # Determinar data de início considerando:
        # 1. Última história do desenvolvedor (se houver)
        # 2. Dependências (histórias das quais esta depende)

        earliest_start = start_date  # <-- PROBLEMA: Usa start_date global

        # Verificar última história do desenvolvedor
        if story.developer_id and story.developer_id in dev_last_end_date:
            earliest_start = max(earliest_start, ...)  # <-- Desenvolvedores foram desalocados!

        # Verificar dependências
        if story.dependencies:
            for dep_id in story.dependencies:
                # ...  # <-- Só considera dependências EXPLÍCITAS
```

**O problema:**
1. `earliest_start` é inicializado com `start_date` global (linha 79)
2. A verificação de desenvolvedor (linhas 82-85) **não se aplica** porque desenvolvedores são desalocados no início do `CalculateScheduleUseCase`
3. A verificação de dependências (linhas 89-96) só considera dependências **explícitas** entre histórias
4. **Ondas (waves) NÃO são consideradas** como barreira temporal

### 3.3 Consequência

| Cenário | Resultado Atual | Resultado Esperado |
|---------|-----------------|---------------------|
| N1 (onda 1, sem deps) | start_date = 2024-12-26 | start_date = 2024-12-26 |
| T1 (onda 3, sem deps) | start_date = 2024-12-26 | start_date = após todas histórias da onda 2 |

### 3.4 BacklogSorter e a Ordenação

**Arquivo:** `backlog_manager/domain/services/backlog_sorter.py`

O `BacklogSorter` ordena corretamente por ondas usando prioridade composta:

```python
def _composite_priority(story: Story) -> int:
    """Calcula prioridade composta: (wave * 10000) + priority."""
    return (story.wave * 10000) + story.priority
```

**Porém:** Esta ordenação é usada apenas para determinar a **ordem de processamento**, não para definir datas. As histórias são processadas na ordem correta (onda 1 → onda 2 → onda 3), mas as datas são calculadas independentemente.

---

## 4. Diagrama do Problema

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUXO ATUAL (COM BUG)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CalculateScheduleUseCase                                           │
│  ├── Ordena: [N1, N2, N3, ... (onda 1)] → [T1, T2, ... (onda 3)]   │
│  │                                                                  │
│  └── ScheduleCalculator.calculate():                                │
│      ├── N1 (onda 1): earliest_start = 2024-12-26                  │
│      ├── N2 (onda 1): earliest_start = depende de N1               │
│      ├── ...                                                        │
│      ├── T1 (onda 3): earliest_start = 2024-12-26  ← BUG!          │
│      │   (não tem dependência explícita → usa start_date global)    │
│      └── ...                                                        │
│                                                                     │
│  RESULTADO: N1 e T1 iniciam na MESMA DATA!                         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    FLUXO ESPERADO (CORRIGIDO)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CalculateScheduleUseCase                                           │
│  ├── Ordena: [N1, N2, N3, ... (onda 1)] → [T1, T2, ... (onda 3)]   │
│  │                                                                  │
│  └── ScheduleCalculator.calculate():                                │
│      ├── N1 (onda 1): earliest_start = 2024-12-26                  │
│      ├── N2 (onda 1): depende de dependências                      │
│      ├── ...                                                        │
│      ├── [BARREIRA DE ONDA: onda 1 → onda 2]                       │
│      │   wave_2_earliest = max(end_dates de todas histórias onda 1)│
│      ├── ...                                                        │
│      ├── [BARREIRA DE ONDA: onda 2 → onda 3]                       │
│      │   wave_3_earliest = max(end_dates de todas histórias onda 2)│
│      ├── T1 (onda 3): earliest_start = wave_3_earliest + 1 dia     │
│      └── ...                                                        │
│                                                                     │
│  RESULTADO: T1 inicia APÓS onda 2 terminar                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Possíveis Soluções

### 5.1 Solução A: Modificar ScheduleCalculator (Recomendada)

Adicionar lógica de barreira de onda no `ScheduleCalculator`:

```python
def calculate(self, stories: list[Story], config: Configuration, start_date: date | None = None) -> list[Story]:
    # ...

    # Rastrear última data de fim por ONDA (além de por desenvolvedor)
    wave_last_end_date: dict[int, date] = {}

    for story in stories:
        # ... cálculo de duração ...

        earliest_start = start_date

        # NOVA REGRA: Verificar onda anterior
        if story.wave > 1:
            prev_wave = story.wave - 1
            if prev_wave in wave_last_end_date:
                wave_barrier = self._next_workday(wave_last_end_date[prev_wave])
                earliest_start = max(earliest_start, wave_barrier)

        # ... resto da lógica ...

        # Atualizar última data de fim da ONDA
        if story.wave not in wave_last_end_date or story.end_date > wave_last_end_date[story.wave]:
            wave_last_end_date[story.wave] = story.end_date
```

**Prós:**
- Solução na camada de domínio (mais limpa)
- Aplicável tanto para cálculo inicial quanto para recálculos

**Contras:**
- Modifica lógica central do ScheduleCalculator

### 5.2 Solução B: Modificar CalculateScheduleUseCase

Processar ondas separadamente no use case:

```python
def execute(self, start_date: date | None = None) -> BacklogDTO:
    # ...

    # Agrupar histórias por onda
    waves = {}
    for story in sorted_stories:
        waves.setdefault(story.wave, []).append(story)

    # Processar onda por onda
    wave_start_date = effective_start_date
    for wave_num in sorted(waves.keys()):
        wave_stories = waves[wave_num]

        # Calcular cronograma desta onda
        self._schedule_calculator.calculate(wave_stories, config, wave_start_date)

        # Próxima onda inicia após esta terminar
        wave_end = max(s.end_date for s in wave_stories if s.end_date)
        wave_start_date = self._schedule_calculator._next_workday(wave_end)
```

**Prós:**
- Não modifica ScheduleCalculator
- Mais explícito sobre processamento por onda

**Contras:**
- Lógica de domínio na camada de aplicação
- Pode não funcionar bem com recálculos parciais

### 5.3 Solução C: Dependências Implícitas por Onda

Criar dependências automáticas entre ondas:

```python
# Antes de calcular, criar dependência implícita:
# Primeira história de cada onda depende da última história da onda anterior
```

**Prós:**
- Usa mecanismo existente de dependências

**Contras:**
- Modifica dados de forma não transparente
- Pode causar confusão para o usuário
- Complica detecção de ciclos

---

## 6. Recomendação

**Recomendo a Solução A** (Modificar ScheduleCalculator) pelos seguintes motivos:

1. **Coerência arquitetural:** A lógica de cálculo de cronograma pertence ao serviço de domínio `ScheduleCalculator`
2. **Reutilização:** A barreira de onda será aplicada automaticamente em qualquer cálculo de cronograma
3. **Transparência:** Não modifica os dados das histórias (dependências)
4. **Testabilidade:** Pode ser testada unitariamente de forma isolada

### 6.1 Escopo da Correção

1. Modificar `ScheduleCalculator.calculate()` para rastrear `wave_last_end_date`
2. Adicionar verificação de barreira de onda antes do cálculo de `earliest_start`
3. Adicionar testes unitários para o novo comportamento
4. Atualizar documentação do algoritmo

---

## 7. Impacto da Correção

### 7.1 Arquivos a Modificar

| Arquivo | Modificação |
|---------|-------------|
| `domain/services/schedule_calculator.py` | Adicionar lógica de barreira de onda |
| `tests/unit/domain/test_schedule_calculator.py` | Adicionar testes para barreira de onda |
| `algoritmo-alocacao-desenvolvedores.md` | Documentar comportamento de barreira |

### 7.2 Comportamento Esperado Após Correção

```
Antes (bug):
  N1 (onda 1): 2024-12-26 → 2024-12-27
  T1 (onda 3): 2024-12-26 → 2024-12-30  ← MESMO DIA que N1!

Depois (corrigido):
  N1 (onda 1): 2024-12-26 → 2024-12-27
  [outras histórias onda 1...]
  [histórias onda 2...]
  T1 (onda 3): 2025-01-XX → 2025-01-YY  ← APÓS onda 2 terminar
```

---

## 8. Conclusão

O bug ocorre porque o `ScheduleCalculator` não considera ondas como barreira temporal. Histórias sem dependências explícitas de ondas anteriores recebem a data de início global, causando paralelismo indevido entre ondas.

A correção requer adicionar rastreamento de `wave_last_end_date` no `ScheduleCalculator` para garantir que histórias de ondas posteriores só iniciem após todas as histórias de ondas anteriores terminarem.

---

**Data:** 2024-12-26
**Autor:** Claude (análise automatizada)
**Status:** Aguardando aprovação para implementação
