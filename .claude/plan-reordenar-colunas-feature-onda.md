# Plano: Reordenar Colunas Feature e Onda no Backlog

## Objetivo

Modificar a ordem das colunas da tabela de backlog para posicionar "Feature" e "Onda" logo após "Prioridade". Adicionar essas duas colunas à exportação Excel (atualmente ausentes) e garantir compatibilidade com importação.

## Análise do Estado Atual

### Estrutura da Tabela UI (editable_table.py)

**Ordem atual das colunas (13 colunas):**
```
0: Prioridade    5: Nome           10: Início
1: ID            6: Status         11: Fim
2: Component     7: Desenvolvedor  12: Duração
3: Feature       8: Dependências
4: Onda          9: SP
```

**Ordem desejada das colunas:**
```
0: Prioridade    5: Nome           10: Início
1: Feature       6: Status         11: Fim
2: Onda          7: Desenvolvedor  12: Duração
3: ID            8: Dependências
4: Component     9: SP
```

### Estrutura da Exportação Excel (openpyxl_excel_service.py)

**EXPORT_COLUMNS atual (11 colunas - SEM Feature e Onda):**
```python
EXPORT_COLUMNS = [
    "Prioridade",    # 1
    "ID",            # 2
    "Component",     # 3
    "Nome",          # 4
    "Status",        # 5
    "Desenvolvedor", # 6
    "Dependências",  # 7
    "SP",            # 8
    "Início",        # 9
    "Fim",           # 10
    "Duração",       # 11
]
```

**EXPORT_COLUMNS desejado (13 colunas):**
```python
EXPORT_COLUMNS = [
    "Prioridade",    # 1
    "Feature",       # 2  <- NOVO
    "Onda",          # 3  <- NOVO
    "ID",            # 4
    "Component",     # 5
    "Nome",          # 6
    "Status",        # 7
    "Desenvolvedor", # 8
    "Dependências",  # 9
    "SP",            # 10
    "Início",        # 11
    "Fim",           # 12
    "Duração",       # 13
]
```

---

## Steps

### Step 1: Atualizar constantes de índices em editable_table.py

**Arquivo:** `backlog_manager/presentation/views/widgets/editable_table.py`

**Linhas 77-90** - Atualizar índices das colunas:

```python
# De:
COL_PRIORITY = 0
COL_ID = 1
COL_COMPONENT = 2
COL_FEATURE = 3
COL_WAVE = 4
COL_NAME = 5
COL_STATUS = 6
COL_DEVELOPER = 7
COL_DEPENDENCIES = 8
COL_STORY_POINT = 9
COL_START_DATE = 10
COL_END_DATE = 11
COL_DURATION = 12

# Para:
COL_PRIORITY = 0
COL_FEATURE = 1      # Movido para logo após Prioridade
COL_WAVE = 2         # Movido para logo após Feature
COL_ID = 3           # Deslocado
COL_COMPONENT = 4    # Deslocado
COL_NAME = 5
COL_STATUS = 6
COL_DEVELOPER = 7
COL_DEPENDENCIES = 8
COL_STORY_POINT = 9
COL_START_DATE = 10
COL_END_DATE = 11
COL_DURATION = 12
```

**Linhas 128-142** - Atualizar lista de headers:

```python
# De:
headers = [
    "Prioridade",
    "ID",
    "Component",
    "Feature",
    "Onda",
    "Nome",
    ...
]

# Para:
headers = [
    "Prioridade",
    "Feature",       # Movido
    "Onda",          # Movido
    "ID",            # Deslocado
    "Component",     # Deslocado
    "Nome",
    ...
]
```

### Step 2: Atualizar configurações de largura em editable_table.py

**Arquivo:** `backlog_manager/presentation/views/widgets/editable_table.py`

**Linhas 145-158** - Reordenar setColumnWidth:

```python
# De:
self.setColumnWidth(self.COL_PRIORITY, 80)
self.setColumnWidth(self.COL_ID, 60)
self.setColumnWidth(self.COL_COMPONENT, 100)
self.setColumnWidth(self.COL_FEATURE, 150)
self.setColumnWidth(self.COL_WAVE, 60)
...

# Para:
self.setColumnWidth(self.COL_PRIORITY, 80)
self.setColumnWidth(self.COL_FEATURE, 150)
self.setColumnWidth(self.COL_WAVE, 60)
self.setColumnWidth(self.COL_ID, 60)
self.setColumnWidth(self.COL_COMPONENT, 100)
...
```

**Nota:** O dicionário `COLUMN_TO_FIELD` (linhas 93-101) não precisa de alteração pois usa as constantes COL_*, que serão atualizadas automaticamente.

### Step 3: Adicionar Feature e Onda na exportação Excel

**Arquivo:** `backlog_manager/infrastructure/excel/openpyxl_excel_service.py`

**Linhas 36-48** - Atualizar EXPORT_COLUMNS:

```python
# De:
EXPORT_COLUMNS = [
    "Prioridade",
    "ID",
    "Component",
    "Nome",
    ...
]

# Para:
EXPORT_COLUMNS = [
    "Prioridade",
    "Feature",       # NOVO
    "Onda",          # NOVO
    "ID",
    "Component",
    "Nome",
    ...
]
```

**Linhas 448-459** - Atualizar mapeamento de dados na exportação:

```python
# De:
for row_num, story in enumerate(stories, start=2):
    sheet.cell(row=row_num, column=1).value = story.priority
    sheet.cell(row=row_num, column=2).value = story.id
    sheet.cell(row=row_num, column=3).value = story.component
    sheet.cell(row=row_num, column=4).value = story.name
    sheet.cell(row=row_num, column=5).value = story.status
    sheet.cell(row=row_num, column=6).value = story.developer_id or ""
    sheet.cell(row=row_num, column=7).value = ", ".join(story.dependencies) if story.dependencies else ""
    sheet.cell(row=row_num, column=8).value = story.story_point
    sheet.cell(row=row_num, column=9).value = story.start_date.strftime("%d/%m/%Y") if story.start_date else ""
    sheet.cell(row=row_num, column=10).value = story.end_date.strftime("%d/%m/%Y") if story.end_date else ""
    sheet.cell(row=row_num, column=11).value = story.duration or ""

# Para:
for row_num, story in enumerate(stories, start=2):
    sheet.cell(row=row_num, column=1).value = story.priority
    sheet.cell(row=row_num, column=2).value = story.feature_name or ""   # NOVO
    sheet.cell(row=row_num, column=3).value = story.wave or ""           # NOVO
    sheet.cell(row=row_num, column=4).value = story.id
    sheet.cell(row=row_num, column=5).value = story.component
    sheet.cell(row=row_num, column=6).value = story.name
    sheet.cell(row=row_num, column=7).value = story.status
    sheet.cell(row=row_num, column=8).value = story.developer_id or ""
    sheet.cell(row=row_num, column=9).value = ", ".join(story.dependencies) if story.dependencies else ""
    sheet.cell(row=row_num, column=10).value = story.story_point
    sheet.cell(row=row_num, column=11).value = story.start_date.strftime("%d/%m/%Y") if story.start_date else ""
    sheet.cell(row=row_num, column=12).value = story.end_date.strftime("%d/%m/%Y") if story.end_date else ""
    sheet.cell(row=row_num, column=13).value = story.duration or ""
```

### Step 4: Adicionar aliases para importação

**Arquivo:** `backlog_manager/infrastructure/excel/openpyxl_excel_service.py`

**Linhas 52-61** - Adicionar aliases para Feature e Onda:

```python
# De:
COLUMN_ALIASES = {
    "id": ["id"],
    "component": ["component"],
    "nome": ["nome", "name"],
    "story_point": ["storypoint", "sp"],
    "deps": ["deps", "dependencias", "dependências"],
    "status": ["status"],
    "desenvolvedor": ["desenvolvedor", "developer", "developer_id"],
    "prioridade": ["prioridade", "priority"],
}

# Para:
COLUMN_ALIASES = {
    "id": ["id"],
    "component": ["component"],
    "nome": ["nome", "name"],
    "story_point": ["storypoint", "sp"],
    "deps": ["deps", "dependencias", "dependências"],
    "status": ["status"],
    "desenvolvedor": ["desenvolvedor", "developer", "developer_id"],
    "prioridade": ["prioridade", "priority"],
    "feature": ["feature"],           # NOVO
    "onda": ["onda", "wave"],         # NOVO
}
```

**Nota:** A importação de Feature requer lógica adicional para resolver `feature_name` → `feature_id`. Esta funcionalidade pode ser implementada futuramente quando necessário.

### Step 5: Testar ciclo completo

1. **Visualização da tabela:**
   - Executar aplicação e verificar nova ordem das colunas
   - Confirmar que Feature e Onda aparecem logo após Prioridade
   - Validar que células são exibidas corretamente

2. **Exportação Excel:**
   - Criar algumas histórias com Feature associada
   - Exportar para Excel
   - Verificar que Feature e Onda aparecem nas colunas 2 e 3
   - Confirmar valores corretos (nome da feature e número da onda)

3. **Importação Excel (formato antigo):**
   - Importar planilha antiga sem colunas Feature e Onda
   - Confirmar que importação funciona sem erros
   - Histórias devem usar feature padrão

4. **Importação Excel (formato novo):**
   - Criar planilha com colunas Feature e Onda
   - Importar e verificar que colunas são reconhecidas (sem erro)
   - Nota: Mapeamento Feature→feature_id requer implementação futura

---

## Considerações Importantes

### Coluna Onda é Somente Leitura
- A coluna "Onda" é derivada automaticamente do "Feature"
- Exibida em cinza na tabela (já implementado)
- Não deve ser editável na UI
- Na exportação, é apenas informativa
- Na importação, pode ser ignorada (derivada da Feature)

### Compatibilidade Retroativa
- A importação usa mapeamento flexível por nome de coluna (case-insensitive)
- Planilhas antigas sem "Feature" e "Onda" continuarão funcionando
- Campo `feature_id` usará valor padrão `"feature_default"` para histórias importadas sem Feature

### Campos do StoryDTO
O DTO já possui os campos necessários:
```python
@dataclass
class StoryDTO:
    ...
    feature_id: str
    feature_name: Optional[str] = None
    wave: Optional[int] = None
```

### Limitação Conhecida
A importação de Feature via nome requer resolver `feature_name` → `feature_id`, o que necessitaria acesso ao repositório de Features. Esta funcionalidade pode ser adicionada posteriormente se necessário.

---

## Arquivos a Modificar

1. `backlog_manager/presentation/views/widgets/editable_table.py`
   - Constantes COL_* (linhas 77-90)
   - Lista headers (linhas 128-142)
   - Configurações de largura (linhas 145-158)

2. `backlog_manager/infrastructure/excel/openpyxl_excel_service.py`
   - EXPORT_COLUMNS (linhas 36-48)
   - COLUMN_ALIASES (linhas 52-61)
   - Mapeamento de dados na exportação (linhas 448-459)

## Estimativa de Impacto

- **Baixo risco:** Alterações são localizadas em dois arquivos
- **Sem quebra de API:** Interfaces de Use Cases permanecem inalteradas
- **Compatibilidade:** Planilhas antigas continuam funcionando
