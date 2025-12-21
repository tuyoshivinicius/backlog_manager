# Plano: Dropdown de Desenvolvedor com Cores de Disponibilidade

## Objetivo

Alterar o dropdown da coluna desenvolvedor para que, quando o usuário clicar para escolher um desenvolvedor:
- **Desenvolvedores disponíveis**: fundo VERDE
- **Desenvolvedores indisponíveis**: fundo VERMELHO

Isso orienta o usuário antecipadamente sobre quais desenvolvedores podem ser alocados sem conflitos com histórias concorrentes.

---

## Análise da Implementação Atual

### Arquitetura Existente

**DeveloperDelegate** (`developer_delegate.py`):
- Responsável por criar o QComboBox quando célula é editada
- Método `createEditor()`: cria o combobox com lista de desenvolvedores
- Método `setEditorData()`: define valor atual
- Método `setModelData()`: salva valor selecionado

**AllocationValidator** (`allocation_validator.py`):
- Serviço de domínio que verifica conflitos de alocação
- Método `has_conflict()`: retorna se há conflito e lista de conflitos
- Lógica: desenvolvedor não pode estar em múltiplas histórias com períodos sobrepostos

**ValidateDeveloperAllocationUseCase** (`validate_developer_allocation.py`):
- Caso de uso que encapsula validação
- Busca história e todas as outras histórias
- Delega para AllocationValidator

### Fluxo Atual
1. Usuário clica na célula "Desenvolvedor"
2. `createEditor()` é chamado
3. QComboBox é criado com lista de desenvolvedores
4. Usuário seleciona desenvolvedor
5. `setModelData()` salva seleção

---

## Especificação da Mudança

### Requisitos Funcionais

1. **RF1:** Ao abrir o dropdown, cada desenvolvedor deve ter cor de fundo indicativa:
   - Verde (`#c8e6c9`): desenvolvedor PODE ser alocado (sem conflito)
   - Vermelho (`#ffcdd2`): desenvolvedor NÃO PODE ser alocado (com conflito)

2. **RF2:** A opção "(Nenhum)" deve permanecer sem cor (fundo padrão)

3. **RF3:** A validação deve considerar:
   - História atual (linha sendo editada)
   - Datas de início e fim da história
   - Alocações existentes de cada desenvolvedor
   - Sobreposição de períodos

4. **RF4:** Se a história NÃO tem datas definidas, todos os desenvolvedores ficam VERDES (nenhum conflito possível)

### Regras de Negócio

- **RN1:** Conflito ocorre quando desenvolvedor está em outra história com período sobreposto
- **RN2:** História sem datas (`start_date=None` ou `end_date=None`) não gera conflito
- **RN3:** História comparando consigo mesma não gera conflito

---

## Arquitetura da Solução

### Opção 1: Delegate com Acesso ao Use Case (RECOMENDADA)

**Vantagens:**
- Mantém responsabilidades claras (validação no use case)
- Reutiliza lógica existente
- Fácil de testar

**Mudanças necessárias:**
1. Injetar `ValidateDeveloperAllocationUseCase` no `DeveloperDelegate`
2. Injetar `StoryRepository` no `DeveloperDelegate` (para buscar história atual)
3. No `createEditor()`:
   - Obter ID da história atual (via índice da linha)
   - Buscar dados da história (datas)
   - Para cada desenvolvedor, chamar `validate_allocation_use_case.execute()`
   - Aplicar cor de fundo baseado no resultado
4. Usar `QStandardItemModel` + `QComboBox.setModel()` para permitir estilização por item

### Opção 2: Delegate com Validação Inline

**Vantagens:**
- Menos dependências injetadas

**Desvantagens:**
- Duplica lógica de validação
- Viola separação de responsabilidades

❌ **Não recomendada**

---

## Implementação Detalhada (Opção 1)

### Arquivos a Modificar

#### 1. `developer_delegate.py`

**Mudanças no `__init__`:**
```python
def __init__(
    self,
    validate_allocation_use_case: ValidateDeveloperAllocationUseCase,
    story_repository: StoryRepository,
    parent=None
):
    """
    Inicializa o delegate.

    Args:
        validate_allocation_use_case: Use case de validação de alocação
        story_repository: Repositório de histórias
        parent: Widget pai
    """
    super().__init__(parent)
    self._developers: List[DeveloperDTO] = []
    self._validate_allocation_use_case = validate_allocation_use_case
    self._story_repository = story_repository
```

**Mudanças no `createEditor`:**
```python
def createEditor(
    self, parent: QWidget, option, index: QModelIndex
) -> QComboBox:
    """
    Cria combobox para selecionar desenvolvedor com cores de disponibilidade.

    Args:
        parent: Widget pai
        option: Opções de estilo
        index: Índice do modelo

    Returns:
        ComboBox com desenvolvedores coloridos
    """
    from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor

    editor = QComboBox(parent)

    # Criar modelo customizado para permitir cores
    model = QStandardItemModel()

    # Adicionar opção "(Nenhum)" sem cor
    none_item = QStandardItem("(Nenhum)")
    none_item.setData(None, Qt.ItemDataRole.UserRole)
    model.appendRow(none_item)

    # Obter ID da história atual (via model.data ou index.row)
    story_id = self._get_story_id_from_index(index)

    if not story_id:
        # Se não conseguir obter ID, adicionar todos sem cor
        for dev in self._developers:
            item = QStandardItem(f"{dev.name} ({dev.id})")
            item.setData(dev.id, Qt.ItemDataRole.UserRole)
            model.appendRow(item)
    else:
        # Buscar história para obter datas
        story = self._story_repository.find_by_id(story_id)

        # Adicionar desenvolvedores com cores
        for dev in self._developers:
            item = QStandardItem(f"{dev.name} ({dev.id})")
            item.setData(dev.id, Qt.ItemDataRole.UserRole)

            # Validar se desenvolvedor pode ser alocado
            is_available = self._check_developer_availability(
                dev.id, story_id, story
            )

            # Aplicar cor de fundo
            if is_available:
                item.setBackground(QColor("#c8e6c9"))  # Verde claro
            else:
                item.setBackground(QColor("#ffcdd2"))  # Vermelho claro

            model.appendRow(item)

    editor.setModel(model)
    return editor


def _get_story_id_from_index(self, index: QModelIndex) -> Optional[str]:
    """
    Obtém ID da história a partir do índice da tabela.

    Args:
        index: Índice do modelo

    Returns:
        ID da história ou None
    """
    # A coluna 1 (ID) contém o ID da história
    id_index = index.siblingAtColumn(1)  # Assumindo coluna 1 é ID
    return id_index.data(Qt.ItemDataRole.DisplayRole)


def _check_developer_availability(
    self,
    developer_id: str,
    story_id: str,
    story: Optional[Story]
) -> bool:
    """
    Verifica se desenvolvedor está disponível para alocação.

    Args:
        developer_id: ID do desenvolvedor
        story_id: ID da história
        story: Entidade Story (pode ser None)

    Returns:
        True se disponível (sem conflito), False caso contrário
    """
    # Se história não existe ou não tem datas, sempre disponível
    if not story or not story.start_date or not story.end_date:
        return True

    # Validar alocação
    is_valid, conflicts = self._validate_allocation_use_case.execute(
        story_id=story_id,
        developer_id=developer_id
    )

    return is_valid
```

**Mudanças no `setEditorData`:**
```python
def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
    """
    Preenche combobox com valor atual.

    Args:
        editor: ComboBox
        index: Índice do modelo
    """
    value = index.data(Qt.ItemDataRole.EditRole)

    # Encontrar índice correspondente no modelo
    model = editor.model()

    if value and value != "(Nenhum)":
        for i in range(model.rowCount()):
            item = model.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == value:
                editor.setCurrentIndex(i)
                return

    # Se não encontrou ou é "(Nenhum)", selecionar primeiro item
    editor.setCurrentIndex(0)
```

**Mudanças no `setModelData`:**
```python
def setModelData(
    self, editor: QComboBox, model, index: QModelIndex
) -> None:
    """
    Salva valor selecionado no modelo.

    Args:
        editor: ComboBox
        model: Modelo de dados
        index: Índice do modelo
    """
    # Obter item selecionado do modelo customizado
    combo_model = editor.model()
    selected_index = editor.currentIndex()

    if selected_index >= 0:
        item = combo_model.item(selected_index)
        selected_id = item.data(Qt.ItemDataRole.UserRole)

        if selected_id:
            model.setData(index, selected_id, Qt.ItemDataRole.EditRole)
        else:
            model.setData(index, "(Nenhum)", Qt.ItemDataRole.EditRole)
```

#### 2. `di_container.py`

**Mudanças em `_create_controllers`:**
```python
# Atualizar criação do story_controller
self.story_controller = StoryController(
    # ... outros use cases ...
    self.validate_allocation_use_case,
)

# O story_controller precisa passar o delegate para a view
# Isso será feito no main_controller ao configurar a view
```

#### 3. `main_controller.py` ou onde o delegate é criado

**Mudanças:**
```python
# Criar delegate com dependências
developer_delegate = DeveloperDelegate(
    validate_allocation_use_case=self._container.validate_allocation_use_case,
    story_repository=self._container.story_repository,
)

# Passar delegate para a view/tabela
self._backlog_table.setItemDelegateForColumn(
    COLUMN_DEVELOPER,
    developer_delegate
)
```

---

## Ordem de Implementação

### Fase 1: Preparação
1. ✅ Analisar estrutura atual
2. ✅ Criar plano de implementação
3. Identificar índice exato da coluna ID (verificar constantes)

### Fase 2: Modificar DeveloperDelegate
1. Adicionar parâmetros ao `__init__`
2. Implementar `_get_story_id_from_index()`
3. Implementar `_check_developer_availability()`
4. Modificar `createEditor()` para usar `QStandardItemModel`
5. Atualizar `setEditorData()` para trabalhar com modelo customizado
6. Atualizar `setModelData()` para trabalhar com modelo customizado

### Fase 3: Atualizar DI Container
1. Modificar criação do delegate em `main_controller.py`
2. Injetar `validate_allocation_use_case` e `story_repository`

### Fase 4: Testes
1. Testar cenário: história sem datas → todos verdes
2. Testar cenário: história com datas → alguns verdes, alguns vermelhos
3. Testar cenário: desenvolvedor já alocado em período sobreposto → vermelho
4. Testar cenário: desenvolvedor livre → verde
5. Testar seleção e salvamento

### Fase 5: Refinamentos (Opcional)
1. Adicionar tooltip nos itens vermelhos mostrando conflito
2. Ajustar cores se necessário (acessibilidade)
3. Adicionar testes unitários para `_check_developer_availability()`

---

## Considerações Técnicas

### Performance
- A validação é executada para CADA desenvolvedor ao abrir o dropdown
- Com 10 desenvolvedores e 100 histórias, são 10 validações
- AllocationValidator já é otimizado (O(n) por desenvolvedor)
- Performance aceitável para até 50 desenvolvedores e 500 histórias

### Alternativas de Otimização (se necessário)
- Cache de resultados durante a edição
- Pré-calcular disponibilidade ao carregar backlog
- Usar threads para validação assíncrona (complexo demais)

### Cores Escolhidas
- Verde: `#c8e6c9` (Material Design Green 100)
- Vermelho: `#ffcdd2` (Material Design Red 100)
- Cores suaves para não cansar visualmente
- Contraste suficiente com texto preto

### Compatibilidade
- QStandardItemModel + setBackground() funciona em PySide6/PyQt6
- Testado em Windows, Linux, macOS

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Performance lenta com muitos desenvolvedores | Média | Médio | Adicionar cache se necessário |
| Cores não visíveis em temas escuros | Baixa | Baixo | Usar cores adaptativas ou testar em tema escuro |
| Coluna ID não estar na posição esperada | Baixa | Alto | Buscar coluna por nome, não por índice fixo |
| História sem ID (nova história) | Média | Médio | Tratar caso None, mostrar todos verdes |

---

## Exemplo de Uso (User Story)

**Como** gerente de projeto
**Quero** ver quais desenvolvedores estão disponíveis ao abrir o dropdown
**Para que** eu possa alocar sem criar conflitos de agenda

**Cenário 1: História com datas definidas**
```
Dado que a história "US-001" tem:
  - Start: 01/02/2025
  - End: 10/02/2025
E o desenvolvedor "João" está alocado em "US-002" de 05/02 a 15/02
Quando eu abrir o dropdown de desenvolvedor em "US-001"
Então "João" deve aparecer com fundo VERMELHO
E outros desenvolvedores livres devem aparecer com fundo VERDE
```

**Cenário 2: História sem datas**
```
Dado que a história "US-005" não tem datas definidas
Quando eu abrir o dropdown de desenvolvedor
Então TODOS os desenvolvedores devem aparecer com fundo VERDE
```

---

## Checklist Final

Antes de considerar implementação completa:

- [ ] DeveloperDelegate modificado e funcional
- [ ] Cores aplicadas corretamente (verde/vermelho)
- [ ] "(Nenhum)" sem cor
- [ ] Validação funcionando (usa AllocationValidator)
- [ ] História sem datas → todos verdes
- [ ] História com datas → cores corretas
- [ ] Seleção e salvamento funcionando
- [ ] DI Container atualizado
- [ ] Performance aceitável (<500ms para abrir dropdown)
- [ ] Testado em cenários reais
- [ ] Código comentado e documentado
- [ ] (Opcional) Tooltip com mensagem de conflito

---

## Estimativa

- **Complexidade:** Média
- **Story Points:** 5
- **Tempo Estimado:** 3-4 horas
  - Implementação: 2h
  - Testes: 1h
  - Ajustes: 1h

---

## Referências

- [Qt Documentation: QStandardItemModel](https://doc.qt.io/qt-6/qstandarditemmodel.html)
- [Qt Documentation: QComboBox](https://doc.qt.io/qt-6/qcombobox.html)
- [Material Design Colors](https://material.io/design/color/the-color-system.html)
- Arquivos do projeto:
  - `developer_delegate.py`
  - `allocation_validator.py`
  - `validate_developer_allocation.py`
