# PLANO DE IMPLEMENTAÇÃO: Melhorias na Alocação de Desenvolvedores

**Projeto:** Backlog Manager
**Versão:** 1.0
**Data:** 20/12/2025
**Objetivo:** Implementar dropdown de desenvolvedores com validação de conflitos de alocação e feedback visual

---

## 📋 ÍNDICE
1. [Requisitos](#requisitos)
2. [Análise do Estado Atual](#análise-do-estado-atual)
3. [Arquitetura da Solução](#arquitetura-da-solução)
4. [Plano de Implementação](#plano-de-implementação)
5. [Critérios de Aceitação](#critérios-de-aceitação)
6. [Casos de Teste](#casos-de-teste)

---

## 📊 REQUISITOS

### RF-NEW-001: Dropdown de Desenvolvedores na Tabela
**Descrição:** Substituir campo de texto livre por dropdown com lista de desenvolvedores.

**Critérios de Aceitação:**
- [ ] Célula "Desenvolvedor" exibe dropdown ao editar
- [ ] Dropdown lista todos os desenvolvedores cadastrados
- [ ] Primeira opção é "(Nenhum)" para remover alocação
- [ ] Seleção atualiza imediatamente a célula
- [ ] Comportamento similar ao StatusDelegate

**Prioridade:** Alta
**Estimativa:** 3 SP

---

### RF-NEW-002: Validação de Conflito de Alocação
**Descrição:** Impedir que desenvolvedor seja alocado a múltiplas histórias com períodos sobrepostos.

**Regra de Negócio:**
```
Conflito existe SE:
  - Desenvolvedor X está alocado à História A
  - História A tem start_date e end_date definidos
  - Usuário tenta alocar Desenvolvedor X à História B
  - História B tem start_date e end_date definidos
  - Períodos se sobrepõem:
    (A.start <= B.end) AND (B.start <= A.end)
```

**Critérios de Aceitação:**
- [ ] Sistema detecta conflitos antes de salvar
- [ ] Alocação é cancelada se houver conflito
- [ ] Valor anterior é mantido na célula
- [ ] Mensagem clara informa o conflito

**Prioridade:** Alta
**Estimativa:** 5 SP

---

### RF-NEW-003: Feedback Visual de Conflito
**Descrição:** Destacar visualmente células conflitantes por 2 segundos.

**Comportamento:**
1. Usuário seleciona desenvolvedor com conflito
2. Sistema detecta conflito
3. Células ficam vermelhas por 2 segundos:
   - Célula da história sendo editada
   - Célula(s) da(s) história(s) conflitante(s)
4. Após 2s, cor volta ao normal
5. Alocação não é salva

**Critérios de Aceitação:**
- [ ] Background vermelho (#FF0000 com 50% transparência)
- [ ] Animação dura exatamente 2 segundos
- [ ] Múltiplas células podem piscar simultaneamente
- [ ] Não bloqueia interface (não modal)

**Prioridade:** Média
**Estimativa:** 3 SP

---

### RF-NEW-004: Remover Alocação de Desenvolvedor
**Descrição:** Permitir desalocar desenvolvedor de uma história.

**Critérios de Aceitação:**
- [ ] Opção "(Nenhum)" no topo do dropdown
- [ ] Selecionar "(Nenhum)" remove `developer_id`
- [ ] Célula exibe "(Nenhum)" após desalocação
- [ ] Cronograma é recalculado

**Prioridade:** Alta
**Estimativa:** 1 SP

---

## 🔍 ANÁLISE DO ESTADO ATUAL

### Implementação Atual

**Arquivo:** `developer_delegate.py`

```python
class DeveloperDelegate(QStyledItemDelegate):
    """
    VERSÃO SIMPLIFICADA: Usa QLineEdit em vez de QComboBox.
    Usuário digita o ID do desenvolvedor diretamente.
    """

    def createEditor(self, parent, option, index) -> QLineEdit:
        editor = QLineEdit(parent)
        editor.setPlaceholderText("Digite o ID do desenvolvedor")
        return editor
```

**Problemas Identificados:**
1. ❌ Campo de texto livre é propenso a erros
2. ❌ Usuário precisa saber IDs dos desenvolvedores
3. ❌ Não há validação de conflitos
4. ❌ UX ruim comparado a outros campos
5. ❌ Sem feedback visual de problemas

**Funcionalidades Existentes:**
- ✅ `DeveloperController` já existe
- ✅ `list_developers()` retorna lista de desenvolvedores
- ✅ `MainController` já atualiza delegate após mudanças
- ✅ `StoryController.on_story_field_changed()` gerencia alocação
- ✅ Story tem métodos `allocate_developer()` e `deallocate_developer()`

---

## 🏗️ ARQUITETURA DA SOLUÇÃO

### Componentes a Modificar/Criar

```
presentation/
├── views/widgets/
│   ├── developer_delegate.py           # ⚠️ MODIFICAR - Trocar LineEdit por ComboBox
│   └── editable_table.py                # ⚠️ MODIFICAR - Adicionar highlight de conflito
├── controllers/
│   └── story_controller.py              # ⚠️ MODIFICAR - Adicionar validação de conflito
└── utils/
    └── cell_highlighter.py              # ✨ CRIAR - Utilitário para highlight temporário

application/
└── use_cases/
    └── story/
        └── validate_developer_allocation.py  # ✨ CRIAR - Use case de validação

domain/
└── services/
    └── allocation_validator.py          # ✨ CRIAR - Serviço de validação de alocação
```

---

## 📋 PLANO DE IMPLEMENTAÇÃO

### FASE 1: Criar Serviço de Validação de Alocação (5 SP) 🔍

**Objetivo:** Implementar lógica de detecção de conflitos no domínio.

#### 1.1 Criar AllocationValidator (Serviço de Domínio)

**Arquivo:** `domain/services/allocation_validator.py`

```python
"""Serviço para validar alocação de desenvolvedores."""
from typing import List, Optional, Tuple
from datetime import date
from backlog_manager.domain.entities.story import Story


class AllocationConflict:
    """Representa um conflito de alocação."""

    def __init__(self, story_id: str, developer_id: str,
                 start_date: date, end_date: date):
        self.story_id = story_id
        self.developer_id = developer_id
        self.start_date = start_date
        self.end_date = end_date

    def __str__(self) -> str:
        return (f"{self.story_id}: {self.developer_id} "
                f"({self.start_date} - {self.end_date})")


class AllocationValidator:
    """
    Serviço de domínio para validar alocação de desenvolvedores.

    Regra: Um desenvolvedor não pode estar alocado a múltiplas histórias
    com períodos de execução sobrepostos.
    """

    @staticmethod
    def has_conflict(
        developer_id: str,
        story_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        all_stories: List[Story]
    ) -> Tuple[bool, List[AllocationConflict]]:
        """
        Verifica se há conflito ao alocar desenvolvedor.

        Args:
            developer_id: ID do desenvolvedor a alocar
            story_id: ID da história sendo alocada
            start_date: Data início da história
            end_date: Data fim da história
            all_stories: Lista de todas as histórias

        Returns:
            Tupla (has_conflict: bool, conflicts: List[AllocationConflict])
        """
        # Se história não tem datas, não há conflito
        if not start_date or not end_date:
            return False, []

        conflicts = []

        for story in all_stories:
            # Ignorar a própria história
            if story.id == story_id:
                continue

            # Verificar se tem mesmo desenvolvedor
            if story.developer_id != developer_id:
                continue

            # Verificar se tem datas definidas
            if not story.start_date or not story.end_date:
                continue

            # Verificar sobreposição de períodos
            # Períodos se sobrepõem se: (A.start <= B.end) AND (B.start <= A.end)
            overlaps = (
                start_date <= story.end_date and
                story.start_date <= end_date
            )

            if overlaps:
                conflict = AllocationConflict(
                    story_id=story.id,
                    developer_id=story.developer_id,
                    start_date=story.start_date,
                    end_date=story.end_date
                )
                conflicts.append(conflict)

        return len(conflicts) > 0, conflicts

    @staticmethod
    def periods_overlap(
        start1: date, end1: date,
        start2: date, end2: date
    ) -> bool:
        """
        Verifica se dois períodos se sobrepõem.

        Args:
            start1: Início do período 1
            end1: Fim do período 1
            start2: Início do período 2
            end2: Fim do período 2

        Returns:
            True se períodos se sobrepõem
        """
        return start1 <= end2 and start2 <= end1
```

**Estimativa:** 3 SP
**Testes:**
- [ ] Sem conflito (datas não definidas)
- [ ] Sem conflito (períodos não se sobrepõem)
- [ ] Conflito detectado (períodos parcialmente sobrepostos)
- [ ] Conflito detectado (um período contém o outro)
- [ ] Múltiplos conflitos detectados
- [ ] Ignora própria história

---

#### 1.2 Criar Use Case de Validação

**Arquivo:** `application/use_cases/story/validate_developer_allocation.py`

```python
"""Caso de uso para validar alocação de desenvolvedor."""
from typing import List, Tuple
from datetime import date
from backlog_manager.application.interfaces.repositories.story_repository import (
    StoryRepository
)
from backlog_manager.domain.services.allocation_validator import (
    AllocationValidator,
    AllocationConflict
)


class ValidateDeveloperAllocationUseCase:
    """
    Valida se desenvolvedor pode ser alocado sem conflitos.
    """

    def __init__(
        self,
        story_repository: StoryRepository,
        validator: AllocationValidator
    ):
        self._story_repo = story_repository
        self._validator = validator

    def execute(
        self,
        story_id: str,
        developer_id: str
    ) -> Tuple[bool, List[AllocationConflict]]:
        """
        Valida alocação de desenvolvedor.

        Args:
            story_id: ID da história
            developer_id: ID do desenvolvedor

        Returns:
            Tupla (is_valid: bool, conflicts: List[AllocationConflict])
        """
        # Buscar história
        story = self._story_repo.find_by_id(story_id)
        if not story:
            return True, []  # História não existe, sem conflito

        # Buscar todas as histórias
        all_stories = self._story_repo.find_all()

        # Validar
        has_conflict, conflicts = self._validator.has_conflict(
            developer_id=developer_id,
            story_id=story_id,
            start_date=story.start_date,
            end_date=story.end_date,
            all_stories=all_stories
        )

        return not has_conflict, conflicts
```

**Estimativa:** 2 SP

---

### FASE 2: Criar Utilitário de Highlight (3 SP) ✨

**Objetivo:** Implementar animação de highlight vermelho nas células.

#### 2.1 Criar CellHighlighter

**Arquivo:** `presentation/utils/cell_highlighter.py`

```python
"""Utilitário para destacar células temporariamente."""
from typing import List
from PySide6.QtWidgets import QTableWidget
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor


class CellHighlighter:
    """
    Utilitário para destacar células da tabela temporariamente.

    Permite criar efeitos visuais como flash vermelho para indicar
    conflitos ou erros.
    """

    @staticmethod
    def highlight_cells(
        table: QTableWidget,
        rows: List[int],
        column: int,
        color: QColor = QColor(255, 0, 0, 128),  # Vermelho 50% transparente
        duration_ms: int = 2000
    ) -> None:
        """
        Destaca células temporariamente.

        Args:
            table: Tabela contendo as células
            rows: Lista de índices de linhas a destacar
            column: Índice da coluna
            color: Cor do highlight
            duration_ms: Duração em milissegundos
        """
        # Armazenar cores originais
        original_colors = {}
        for row in rows:
            item = table.item(row, column)
            if item:
                original_colors[row] = item.background()
                item.setBackground(color)

        # Restaurar cores após duração
        QTimer.singleShot(
            duration_ms,
            lambda: CellHighlighter._restore_colors(
                table, original_colors, column
            )
        )

    @staticmethod
    def _restore_colors(
        table: QTableWidget,
        original_colors: dict,
        column: int
    ) -> None:
        """
        Restaura cores originais das células.

        Args:
            table: Tabela
            original_colors: Dict {row: QBrush}
            column: Coluna
        """
        for row, color in original_colors.items():
            item = table.item(row, column)
            if item:
                item.setBackground(color)

    @staticmethod
    def flash_cell(
        table: QTableWidget,
        row: int,
        column: int,
        error: bool = True,
        duration_ms: int = 2000
    ) -> None:
        """
        Flash rápido em uma célula.

        Args:
            table: Tabela
            row: Linha
            column: Coluna
            error: Se True usa vermelho, se False usa amarelo
            duration_ms: Duração
        """
        color = QColor(255, 0, 0, 128) if error else QColor(255, 255, 0, 128)
        CellHighlighter.highlight_cells(table, [row], column, color, duration_ms)
```

**Estimativa:** 2 SP
**Testes Manuais:**
- [ ] Flash em célula única
- [ ] Flash em múltiplas células simultaneamente
- [ ] Cores restauradas corretamente após timeout
- [ ] Não trava interface

---

### FASE 3: Atualizar DeveloperDelegate (3 SP) 📝

**Objetivo:** Substituir LineEdit por ComboBox com lista de desenvolvedores.

#### 3.1 Modificar DeveloperDelegate

**Arquivo:** `presentation/views/widgets/developer_delegate.py`

```python
"""
Delegate para edição de Desenvolvedor com dropdown.

Fornece um combobox com lista de desenvolvedores disponíveis.
"""
from typing import List
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QWidget
from PySide6.QtCore import QModelIndex, Qt

from backlog_manager.application.dto.developer_dto import DeveloperDTO


class DeveloperDelegate(QStyledItemDelegate):
    """
    Delegate para edição de Desenvolvedor.

    Usa QComboBox com lista de desenvolvedores cadastrados.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._developers: List[DeveloperDTO] = []

    def set_developers(self, developers: List[DeveloperDTO]) -> None:
        """
        Define lista de desenvolvedores disponíveis.

        Args:
            developers: Lista de desenvolvedores
        """
        self._developers = developers

    def createEditor(
        self, parent: QWidget, option, index: QModelIndex
    ) -> QComboBox:
        """
        Cria combobox para selecionar desenvolvedor.

        Args:
            parent: Widget pai
            option: Opções de estilo
            index: Índice do modelo

        Returns:
            ComboBox com desenvolvedores
        """
        editor = QComboBox(parent)

        # Adicionar opção "(Nenhum)" no topo
        editor.addItem("(Nenhum)", None)

        # Adicionar desenvolvedores
        for dev in self._developers:
            editor.addItem(f"{dev.name} ({dev.id})", dev.id)

        return editor

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        """
        Preenche combobox com valor atual.

        Args:
            editor: ComboBox
            index: Índice do modelo
        """
        value = index.data(Qt.ItemDataRole.EditRole)

        # Encontrar índice correspondente
        if value and value != "(Nenhum)":
            for i in range(editor.count()):
                if editor.itemData(i) == value:
                    editor.setCurrentIndex(i)
                    return
        else:
            editor.setCurrentIndex(0)  # "(Nenhum)"

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
        selected_id = editor.currentData()

        if selected_id:
            model.setData(index, selected_id, Qt.ItemDataRole.EditRole)
        else:
            model.setData(index, "(Nenhum)", Qt.ItemDataRole.EditRole)
```

**Estimativa:** 2 SP

---

#### 3.2 Atualizar MainController

**Arquivo:** `main_controller.py`

```python
def _setup_delegates(self) -> None:
    """Configura delegates da tabela APÓS popular com dados."""
    if not self._table:
        return

    # ... outros delegates ...

    # Developer Delegate - Agora com ComboBox
    self._developer_delegate = DeveloperDelegate()
    developers = self._developer_controller.list_developers()
    self._developer_delegate.set_developers(developers)
    self._table.setItemDelegateForColumn(
        EditableTableWidget.COL_DEVELOPER, self._developer_delegate
    )

def refresh_backlog(self) -> None:
    """Atualiza a tabela de backlog."""
    # ... código existente ...

    # Atualizar lista de desenvolvedores no delegate
    if self._developer_delegate:
        developers = self._developer_controller.list_developers()
        self._developer_delegate.set_developers(developers)
```

**Estimativa:** 1 SP

---

### FASE 4: Adicionar Validação no StoryController (5 SP) 🔒

**Objetivo:** Validar conflitos antes de salvar e disparar feedback visual.

#### 4.1 Modificar StoryController

**Arquivo:** `story_controller.py`

```python
class StoryController:
    """Controlador de histórias."""

    def __init__(
        self,
        # ... use cases existentes ...
        validate_allocation_use_case: ValidateDeveloperAllocationUseCase,
    ):
        # ... inicializações existentes ...
        self._validate_allocation_use_case = validate_allocation_use_case

    def on_story_field_changed(
        self, story_id: str, field: str, value: object
    ) -> None:
        """Gerencia edição inline de campo."""
        try:
            # ... conversões existentes ...

            # VALIDAÇÃO ESPECIAL: developer_id
            if field == "developer_id" and value and value != "(Nenhum)":
                # Validar conflito de alocação
                is_valid, conflicts = self._validate_allocation_use_case.execute(
                    story_id, value
                )

                if not is_valid:
                    # Conflito detectado! Cancelar operação e mostrar feedback
                    self._handle_allocation_conflict(story_id, conflicts)
                    return  # NÃO salva

            # Se passou validação, atualizar normalmente
            self._update_use_case.execute(story_id, {field: value})

            # ... resto do código ...

        except Exception as e:
            # ... tratamento de erro ...

    def _handle_allocation_conflict(
        self,
        story_id: str,
        conflicts: List[AllocationConflict]
    ) -> None:
        """
        Trata conflito de alocação com feedback visual.

        Args:
            story_id: ID da história sendo editada
            conflicts: Lista de conflitos detectados
        """
        # Obter referência à tabela
        table = self._get_table_reference()
        if not table:
            return

        # Encontrar linhas conflitantes
        conflicting_rows = []
        current_row = None

        for row in range(table.rowCount()):
            id_item = table.item(row, table.COL_ID)
            if not id_item:
                continue

            row_story_id = id_item.text()

            # Linha atual sendo editada
            if row_story_id == story_id:
                current_row = row

            # Linhas conflitantes
            for conflict in conflicts:
                if row_story_id == conflict.story_id:
                    conflicting_rows.append(row)

        # Destacar células em vermelho
        from backlog_manager.presentation.utils.cell_highlighter import CellHighlighter

        all_rows = [current_row] + conflicting_rows if current_row is not None else []

        if all_rows:
            CellHighlighter.highlight_cells(
                table=table,
                rows=all_rows,
                column=table.COL_DEVELOPER,
                duration_ms=2000
            )

        # Mostrar mensagem de erro
        conflict_ids = [c.story_id for c in conflicts]
        MessageBox.warning(
            self._parent_widget,
            "Conflito de Alocação",
            f"Desenvolvedor já está alocado em: {', '.join(conflict_ids)}\n"
            f"Períodos de execução se sobrepõem."
        )

        # Reverter mudança na view
        self._refresh_view()

    def _get_table_reference(self):
        """Obtém referência à tabela via callback."""
        # Implementar mecanismo para obter tabela
        # Opção 1: Passar referência no construtor
        # Opção 2: Via callback
        # Opção 3: Via event bus
        pass
```

**Estimativa:** 3 SP

---

#### 4.2 Atualizar DI Container

**Arquivo:** `di_container.py`

```python
def create_story_controller() -> StoryController:
    """Cria StoryController com dependências."""
    # ... código existente ...

    # Criar validador de alocação
    allocation_validator = AllocationValidator()
    validate_allocation_use_case = ValidateDeveloperAllocationUseCase(
        story_repository=story_repo,
        validator=allocation_validator
    )

    return StoryController(
        # ... use cases existentes ...
        validate_allocation_use_case=validate_allocation_use_case,
    )
```

**Estimativa:** 1 SP

---

#### 4.3 Passar Referência da Tabela ao Controller

**Arquivo:** `main_controller.py`

```python
def _setup_controllers(self) -> None:
    """Configura controllers com callbacks."""
    # ... código existente ...

    # Story Controller - adicionar referência à tabela
    self._story_controller.set_parent_widget(self._main_window)
    self._story_controller.set_table_widget(self._table)  # NOVO
    self._story_controller.set_refresh_callback(self.refresh_backlog)
    # ...
```

**Arquivo:** `story_controller.py`

```python
class StoryController:
    def __init__(self, ...):
        # ... inicializações existentes ...
        self._table_widget = None

    def set_table_widget(self, table) -> None:
        """Define referência à tabela."""
        self._table_widget = table

    def _get_table_reference(self):
        """Obtém referência à tabela."""
        return self._table_widget
```

**Estimativa:** 1 SP

---

### FASE 5: Testes e Refinamentos (2 SP) 🧪

#### 5.1 Testes Unitários

**Arquivo:** `tests/unit/domain/test_allocation_validator.py`

```python
"""Testes para AllocationValidator."""
import pytest
from datetime import date, timedelta
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.services.allocation_validator import AllocationValidator
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


def test_no_conflict_when_no_dates():
    """Sem conflito se história não tem datas."""
    validator = AllocationValidator()

    stories = [
        Story(id="S1", feature="F1", name="Story 1",
              story_point=StoryPoint(5), developer_id="DEV1",
              start_date=date(2025, 1, 1), end_date=date(2025, 1, 5))
    ]

    has_conflict, conflicts = validator.has_conflict(
        developer_id="DEV1",
        story_id="S2",
        start_date=None,  # Sem data
        end_date=None,
        all_stories=stories
    )

    assert not has_conflict
    assert len(conflicts) == 0


def test_conflict_detected_overlapping_periods():
    """Conflito detectado quando períodos se sobrepõem."""
    validator = AllocationValidator()

    stories = [
        Story(id="S1", feature="F1", name="Story 1",
              story_point=StoryPoint(5), developer_id="DEV1",
              start_date=date(2025, 1, 1), end_date=date(2025, 1, 10))
    ]

    has_conflict, conflicts = validator.has_conflict(
        developer_id="DEV1",
        story_id="S2",
        start_date=date(2025, 1, 5),  # Sobrepõe S1
        end_date=date(2025, 1, 15),
        all_stories=stories
    )

    assert has_conflict
    assert len(conflicts) == 1
    assert conflicts[0].story_id == "S1"


def test_no_conflict_non_overlapping_periods():
    """Sem conflito quando períodos não se sobrepõem."""
    validator = AllocationValidator()

    stories = [
        Story(id="S1", feature="F1", name="Story 1",
              story_point=StoryPoint(5), developer_id="DEV1",
              start_date=date(2025, 1, 1), end_date=date(2025, 1, 10))
    ]

    has_conflict, conflicts = validator.has_conflict(
        developer_id="DEV1",
        story_id="S2",
        start_date=date(2025, 1, 15),  # Depois de S1
        end_date=date(2025, 1, 20),
        all_stories=stories
    )

    assert not has_conflict
    assert len(conflicts) == 0


def test_ignores_different_developer():
    """Ignora histórias de outros desenvolvedores."""
    validator = AllocationValidator()

    stories = [
        Story(id="S1", feature="F1", name="Story 1",
              story_point=StoryPoint(5), developer_id="DEV2",  # Outro dev
              start_date=date(2025, 1, 1), end_date=date(2025, 1, 10))
    ]

    has_conflict, conflicts = validator.has_conflict(
        developer_id="DEV1",
        story_id="S2",
        start_date=date(2025, 1, 5),
        end_date=date(2025, 1, 15),
        all_stories=stories
    )

    assert not has_conflict
```

**Estimativa:** 2 SP

---

## ✅ CRITÉRIOS DE ACEITAÇÃO GLOBAIS

### Funcionais
- [ ] Dropdown de desenvolvedores funciona na tabela
- [ ] Opção "(Nenhum)" remove alocação
- [ ] Sistema detecta conflitos de alocação
- [ ] Conflitos bloqueiam salvamento
- [ ] Células piscam em vermelho por 2 segundos
- [ ] Mensagem clara explica conflito
- [ ] Múltiplas células podem piscar simultaneamente
- [ ] Cronograma recalcula após alocação

### Técnicos
- [ ] AllocationValidator testado (cobertura ≥ 90%)
- [ ] Validação não impacta performance
- [ ] Código segue Clean Architecture
- [ ] Sem acoplamento entre camadas
- [ ] Animação não trava UI

### UX
- [ ] Dropdown similar ao StatusDelegate
- [ ] Feedback visual claro e imediato
- [ ] Mensagem de erro explicativa
- [ ] Não há travamentos ou lags

---

## 🧪 CASOS DE TESTE

### CT-001: Selecionar Desenvolvedor Sem Conflito
**Passos:**
1. Criar história H1 com Dev1 (01/01 - 10/01)
2. Criar história H2 sem desenvolvedor (15/01 - 20/01)
3. Editar célula desenvolvedor de H2
4. Selecionar Dev1 no dropdown

**Resultado Esperado:**
- ✅ Dev1 alocado a H2
- ✅ Célula atualiza para "Dev1"
- ✅ Cronograma recalculado
- ✅ Sem feedback de erro

---

### CT-002: Detectar Conflito de Alocação
**Passos:**
1. Criar história H1 com Dev1 (01/01 - 10/01)
2. Criar história H2 sem desenvolvedor (05/01 - 15/01)
3. Editar célula desenvolvedor de H2
4. Selecionar Dev1 no dropdown

**Resultado Esperado:**
- ❌ Alocação cancelada
- ✅ Células de H1 e H2 ficam vermelhas por 2s
- ✅ Mensagem: "Desenvolvedor já está alocado em: H1. Períodos se sobrepõem."
- ✅ H2 permanece sem desenvolvedor

---

### CT-003: Remover Alocação
**Passos:**
1. Criar história H1 com Dev1
2. Editar célula desenvolvedor de H1
3. Selecionar "(Nenhum)" no dropdown

**Resultado Esperado:**
- ✅ Dev1 desalocado de H1
- ✅ Célula exibe "(Nenhum)"
- ✅ Cronograma recalculado

---

### CT-004: Múltiplos Conflitos
**Passos:**
1. Criar H1 com Dev1 (01/01 - 10/01)
2. Criar H2 com Dev1 (08/01 - 15/01)
3. Criar H3 sem dev (05/01 - 12/01)
4. Tentar alocar Dev1 a H3

**Resultado Esperado:**
- ❌ Alocação cancelada
- ✅ Células de H1, H2 e H3 ficam vermelhas
- ✅ Mensagem lista ambos conflitos

---

## 📊 RESUMO DE ESTIMATIVAS

| Fase | Descrição | Story Points |
|------|-----------|--------------|
| 1 | Serviço de Validação | 5 SP |
| 2 | Utilitário de Highlight | 3 SP |
| 3 | DeveloperDelegate | 3 SP |
| 4 | Validação no Controller | 5 SP |
| 5 | Testes | 2 SP |
| **TOTAL** | | **18 SP** |

**Duração Estimada:** 2-3 semanas
**Complexidade:** Média-Alta

---

## 🎯 ORDEM DE IMPLEMENTAÇÃO RECOMENDADA

### Sprint 1 (8 SP)
1. ✅ FASE 1: AllocationValidator (domínio puro)
2. ✅ FASE 2: CellHighlighter (utilitário independente)

### Sprint 2 (10 SP)
3. ✅ FASE 3: DeveloperDelegate com ComboBox
4. ✅ FASE 4: Integração e validação no controller
5. ✅ FASE 5: Testes completos

---

## 📝 NOTAS DE IMPLEMENTAÇÃO

### Dependências Externas
- Nenhuma biblioteca externa necessária
- Usa apenas PySide6 (já presente)

### Considerações de Performance
- Validação O(n) onde n = número de histórias
- Aceitável para < 1000 histórias
- Se necessário, criar índice por desenvolvedor

### Tratamento de Edge Cases
1. **História sem datas:** Não valida conflito
2. **Desenvolvedor em história sem data:** Não conta como conflito
3. **Remover desenvolvedor:** Sempre permitido
4. **Múltiplos conflitos:** Mostra todos

### Melhorias Futuras
- [ ] Sugestão de período alternativo
- [ ] Visualização de timeline de alocação
- [ ] Drag-and-drop para realocar
- [ ] Balanceamento automático de carga

---

## ✅ CONCLUSÃO

Este plano implementa uma melhoria significativa na UX de alocação de desenvolvedores:

**Benefícios:**
- ✅ UX consistente com outras células (Status, StoryPoint)
- ✅ Prevenção de conflitos de alocação
- ✅ Feedback visual claro e imediato
- ✅ Mantém Clean Architecture
- ✅ Totalmente testável

**Pronto para implementação!** 🚀
