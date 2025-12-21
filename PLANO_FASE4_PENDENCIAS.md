# Fase 4 - Implementação de Funcionalidades Pendentes

## 📋 Análise de Requisitos Não Implementados

### Resumo Executivo

Analisando o `plano_fase4.md`, identifiquei funcionalidades críticas ainda não implementadas que impactam a usabilidade completa do sistema:

1. **DependenciesDelegate** - Essencial para gestão de dependências entre histórias
2. **Gerenciador de Desenvolvedores** - Dialog completo para CRUD de desenvolvedores
3. **Funcionalidades Secundárias** - Dialogs de ajuda, about, progress

---

## 🎯 Priorização

### Prioridade ALTA (Crítica para funcionalidade completa)

#### 1. DependenciesDelegate + DependenciesDialog
**Impacto:** Sem isso, não é possível gerenciar dependências visualmente
**Complexidade:** Alta (8 SP)
**Dependências:** CycleDetector (já implementado)

#### 2. Gerenciador de Desenvolvedores (Dialog Completo)
**Impacto:** Atualmente só é possível criar desenvolvedores, não editar/deletar
**Complexidade:** Média (5 SP)
**Dependências:** Nenhuma

### Prioridade MÉDIA (Melhoria de UX)

#### 3. ProgressDialog
**Impacto:** Operações longas (cálculo cronograma, import Excel) sem feedback visual
**Complexidade:** Baixa (2 SP)

#### 4. ShortcutsDialog + AboutDialog
**Impacto:** Documentação de uso e informações do sistema
**Complexidade:** Baixa (2 SP)

### Prioridade BAIXA (Nice to have)

#### 5. NotificationToast
**Impacto:** Feedback visual mais elegante (opcional)
**Complexidade:** Média (3 SP)

---

## 📝 PLANO DETALHADO DE IMPLEMENTAÇÃO

---

## 1. DependenciesDelegate + DependenciesDialog (8 SP)

### Objetivo
Implementar sistema completo de gestão de dependências com validação de ciclos em tempo real e interface visual intuitiva.

### Arquitetura

```
User → Clica duplo em célula Dependências
  ↓
DependenciesDelegate.createEditor()
  ↓
Abre DependenciesDialog
  ↓
Dialog mostra lista de histórias com checkboxes
  ↓
User seleciona/desseleciona histórias
  ↓
Validação de ciclos em tempo real (CycleDetector)
  ↓
Se válido → User clica "OK"
  ↓
Dialog retorna lista de IDs
  ↓
DependenciesDelegate.setModelData()
  ↓
Controller chama UpdateStoryUseCase
  ↓
Recálculo automático de cronograma
```

### Implementação

#### 1.1 DependenciesDialog

**Arquivo:** `backlog_manager/presentation/views/widgets/dependencies_dialog.py`

```python
"""
Dialog para seleção de dependências de uma história.

Permite seleção múltipla com validação de ciclos em tempo real.
"""
from typing import List, Set
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QWidget, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.domain.services.cycle_detector import CycleDetector


class DependenciesDialog(QDialog):
    """
    Dialog para seleção de dependências de uma história.

    Features:
    - Lista todas as histórias disponíveis (exceto a atual)
    - Checkboxes para seleção múltipla
    - Validação de ciclos em tempo real
    - Busca/filtro de histórias
    - Feedback visual de dependências inválidas
    """

    def __init__(
        self,
        parent: QWidget,
        current_story_id: str,
        all_stories: List[StoryDTO],
        current_dependencies: List[str],
        story_repository  # Para validação de ciclos
    ):
        """
        Inicializa dialog de dependências.

        Args:
            parent: Widget pai
            current_story_id: ID da história sendo editada
            all_stories: Lista de todas as histórias disponíveis
            current_dependencies: Lista de IDs de dependências atuais
            story_repository: Repository para validação de ciclos
        """
        super().__init__(parent)

        self._current_story_id = current_story_id
        self._all_stories = all_stories
        self._current_dependencies = set(current_dependencies)
        self._story_repository = story_repository
        self._cycle_detector = CycleDetector()

        self._setup_ui()
        self._populate_stories()

    def _setup_ui(self) -> None:
        """Configura a interface do dialog."""
        self.setWindowTitle("Gerenciar Dependências")
        self.setModal(True)
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        # Título e instruções
        title = QLabel(f"<h3>Dependências da História {self._current_story_id}</h3>")
        layout.addWidget(title)

        instructions = QLabel(
            "Selecione as histórias das quais esta história depende.\n"
            "A história atual só pode iniciar após TODAS as dependências serem concluídas."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Campo de busca
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Digite ID ou nome da história...")
        self._search_input.textChanged.connect(self._filter_stories)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_input)
        layout.addLayout(search_layout)

        # Lista de histórias com checkboxes
        self._stories_list = QListWidget()
        self._stories_list.itemChanged.connect(self._on_selection_changed)
        layout.addWidget(self._stories_list)

        # Label de validação
        self._validation_label = QLabel()
        self._validation_label.setWordWrap(True)
        layout.addWidget(self._validation_label)

        # Botões
        buttons_layout = QHBoxLayout()

        self._select_all_btn = QPushButton("Selecionar Todos")
        self._select_all_btn.clicked.connect(self._select_all)
        buttons_layout.addWidget(self._select_all_btn)

        self._clear_all_btn = QPushButton("Limpar Todos")
        self._clear_all_btn.clicked.connect(self._clear_all)
        buttons_layout.addWidget(self._clear_all_btn)

        buttons_layout.addStretch()

        self._ok_button = QPushButton("OK")
        self._ok_button.clicked.connect(self.accept)
        self._ok_button.setDefault(True)
        buttons_layout.addWidget(self._ok_button)

        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)

    def _populate_stories(self) -> None:
        """Popula lista de histórias com checkboxes."""
        self._stories_list.clear()

        for story in self._all_stories:
            # Não incluir a própria história
            if story.id == self._current_story_id:
                continue

            # Criar item com checkbox
            item = QListWidgetItem(f"{story.id} - {story.name}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            # Marcar se está nas dependências atuais
            if story.id in self._current_dependencies:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            # Armazenar story_id como data
            item.setData(Qt.ItemDataRole.UserRole, story.id)

            self._stories_list.addItem(item)

        # Validar estado inicial
        self._validate_selection()

    def _filter_stories(self, search_text: str) -> None:
        """
        Filtra lista de histórias baseado no texto de busca.

        Args:
            search_text: Texto para buscar
        """
        search_text = search_text.lower()

        for i in range(self._stories_list.count()):
            item = self._stories_list.item(i)
            item_text = item.text().lower()

            # Mostrar item se contém o texto de busca
            item.setHidden(search_text not in item_text)

    def _on_selection_changed(self, item: QListWidgetItem) -> None:
        """
        Callback quando seleção muda.
        Valida se não cria ciclos.

        Args:
            item: Item que mudou
        """
        self._validate_selection()

    def _validate_selection(self) -> None:
        """
        Valida se a seleção atual cria ciclos de dependências.

        Usa CycleDetector para verificar se adicionar as dependências
        selecionadas criaria um ciclo no grafo de dependências.
        """
        selected_deps = self._get_selected_dependencies()

        # Criar grafo temporário com todas as histórias
        all_stories = self._story_repository.find_all()

        # Criar cópia das histórias com dependências atualizadas
        temp_stories = []
        for story in all_stories:
            if story.id == self._current_story_id:
                # Atualizar dependências da história atual
                story_copy = story
                story_copy.dependencies = list(selected_deps)
                temp_stories.append(story_copy)
            else:
                temp_stories.append(story)

        # Detectar ciclos
        has_cycle = self._cycle_detector.has_cycle(temp_stories)

        if has_cycle:
            self._validation_label.setText(
                "⚠️ ERRO: A seleção atual cria um ciclo de dependências! "
                "Histórias não podem depender uma da outra de forma circular."
            )
            self._validation_label.setStyleSheet("color: red; font-weight: bold;")
            self._ok_button.setEnabled(False)
        else:
            count = len(selected_deps)
            if count == 0:
                self._validation_label.setText("✓ Nenhuma dependência selecionada.")
            else:
                self._validation_label.setText(
                    f"✓ {count} dependência(s) selecionada(s). Nenhum ciclo detectado."
                )
            self._validation_label.setStyleSheet("color: green;")
            self._ok_button.setEnabled(True)

    def _get_selected_dependencies(self) -> Set[str]:
        """
        Retorna conjunto de IDs de histórias selecionadas.

        Returns:
            Set de story IDs selecionados
        """
        selected = set()

        for i in range(self._stories_list.count()):
            item = self._stories_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                story_id = item.data(Qt.ItemDataRole.UserRole)
                selected.add(story_id)

        return selected

    def _select_all(self) -> None:
        """Seleciona todas as histórias visíveis."""
        for i in range(self._stories_list.count()):
            item = self._stories_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)

    def _clear_all(self) -> None:
        """Limpa todas as seleções."""
        for i in range(self._stories_list.count()):
            item = self._stories_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)

    def get_selected_dependencies(self) -> List[str]:
        """
        Retorna lista de IDs de dependências selecionadas.

        Returns:
            Lista de story IDs
        """
        return list(self._get_selected_dependencies())
```

#### 1.2 DependenciesDelegate

**Arquivo:** `backlog_manager/presentation/views/widgets/dependencies_delegate.py`

```python
"""
Delegate para edição de dependências de histórias.

Abre DependenciesDialog para seleção visual de dependências.
"""
from typing import List
from PySide6.QtWidgets import QStyledItemDelegate, QWidget
from PySide6.QtCore import QModelIndex, Qt

from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.presentation.views.widgets.dependencies_dialog import DependenciesDialog


class DependenciesDelegate(QStyledItemDelegate):
    """
    Delegate para edição de dependências.

    Ao editar, abre DependenciesDialog para seleção visual.
    Exibe dependências como texto: "S1, S2, A3"
    """

    def __init__(self, parent=None):
        """
        Inicializa o delegate.

        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self._all_stories: List[StoryDTO] = []
        self._story_repository = None  # Será injetado

    def set_stories(self, stories: List[StoryDTO]) -> None:
        """
        Define lista de histórias disponíveis.

        Args:
            stories: Lista de todas as histórias
        """
        self._all_stories = stories

    def set_story_repository(self, repository) -> None:
        """
        Injeta repository para validação de ciclos.

        Args:
            repository: StoryRepository
        """
        self._story_repository = repository

    def createEditor(
        self, parent: QWidget, option, index: QModelIndex
    ) -> QWidget:
        """
        Cria editor customizado (DependenciesDialog).

        Args:
            parent: Widget pai
            option: Opções de estilo
            index: Índice do modelo

        Returns:
            None (dialog é gerenciado manualmente)
        """
        # Não retornamos um widget, abrimos o dialog diretamente em setEditorData
        return None

    def setEditorData(self, editor, index: QModelIndex) -> None:
        """
        Abre DependenciesDialog para editar dependências.

        Args:
            editor: Editor (ignorado, usamos dialog)
            index: Índice do modelo
        """
        # Obter story_id da linha
        table = index.model().parent()
        row = index.row()

        # Assumindo que ID está na coluna 1
        id_item = table.item(row, 1)
        if not id_item:
            return

        story_id = id_item.text()

        # Obter dependências atuais
        current_deps_text = index.data(Qt.ItemDataRole.DisplayRole)
        current_deps = []
        if current_deps_text:
            current_deps = [dep.strip() for dep in current_deps_text.split(",") if dep.strip()]

        # Abrir dialog
        dialog = DependenciesDialog(
            parent=table,
            current_story_id=story_id,
            all_stories=self._all_stories,
            current_dependencies=current_deps,
            story_repository=self._story_repository
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Obter dependências selecionadas
            selected_deps = dialog.get_selected_dependencies()

            # Atualizar célula
            deps_text = ", ".join(selected_deps) if selected_deps else ""
            index.model().setData(index, deps_text, Qt.ItemDataRole.EditRole)

    def setModelData(self, editor, model, index: QModelIndex) -> None:
        """
        Não usado (dados já foram setados em setEditorData).

        Args:
            editor: Editor
            model: Modelo
            index: Índice
        """
        pass
```

#### 1.3 Integração na Tabela

**Arquivo:** `backlog_manager/presentation/views/widgets/editable_table.py`

```python
# Adicionar ao _setup_table() depois de configurar outros delegates:

# Dependencies Delegate
self._dependencies_delegate = DependenciesDelegate(self)
self.setItemDelegateForColumn(self.COL_DEPENDENCIES, self._dependencies_delegate)

# Método para atualizar lista de histórias no delegate
def refresh_dependencies_delegate(self) -> None:
    """Atualiza lista de histórias no DependenciesDelegate."""
    if self._dependencies_delegate and hasattr(self, '_stories'):
        self._dependencies_delegate.set_stories(self._stories)
```

### Testes

```python
# tests/unit/presentation/test_dependencies_dialog.py

def test_dependencies_dialog_opens(qapp):
    """Deve abrir dialog de dependências"""
    stories = [
        StoryDTO(id="S1", name="História 1", ...),
        StoryDTO(id="S2", name="História 2", ...),
    ]

    dialog = DependenciesDialog(
        parent=None,
        current_story_id="S1",
        all_stories=stories,
        current_dependencies=[],
        story_repository=mock_repo
    )

    assert dialog is not None
    assert dialog.windowTitle() == "Gerenciar Dependências"

def test_detects_cycle(qapp):
    """Deve detectar ciclo de dependências"""
    # S1 depende de S2
    # Tentar fazer S2 depender de S1 → ciclo!

    # Setup stories with S1 → S2
    # Open dialog for S2
    # Select S1 as dependency
    # Assert: validation error shown, OK button disabled
```

---

## 2. Gerenciador de Desenvolvedores (5 SP)

### Objetivo
Implementar dialog completo para gerenciar desenvolvedores (listar, criar, editar, deletar) em uma interface centralizada.

### Arquitetura

```
Menu "Desenvolvedor" → "Gerenciar Desenvolvedores"
  ↓
DeveloperManagerDialog abre
  ↓
Lista todos os desenvolvedores
  ↓
User pode: Adicionar, Editar, Deletar
  ↓
Operações chamam DeveloperController
  ↓
Controller chama use cases apropriados
  ↓
Dialog atualiza lista
```

### Implementação

#### 2.1 DeveloperManagerDialog

**Arquivo:** `backlog_manager/presentation/views/developer_manager_dialog.py`

```python
"""
Dialog para gerenciamento completo de desenvolvedores.

Permite listar, criar, editar e deletar desenvolvedores.
"""
from typing import List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal

from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.presentation.views.developer_form import DeveloperFormDialog
from backlog_manager.presentation.utils.message_box import MessageBox


class DeveloperManagerDialog(QDialog):
    """
    Dialog para gerenciamento de desenvolvedores.

    Features:
    - Lista todos os desenvolvedores
    - Botões: Adicionar, Editar, Deletar
    - Integração com DeveloperController
    - Confirmação antes de deletar
    - Atualização automática da lista
    """

    # Sinais
    developers_changed = Signal()  # Emitido quando lista muda

    def __init__(
        self,
        parent: QWidget,
        developer_controller  # DeveloperController injetado
    ):
        """
        Inicializa dialog de gerenciamento.

        Args:
            parent: Widget pai
            developer_controller: Controller de desenvolvedores
        """
        super().__init__(parent)

        self._developer_controller = developer_controller
        self._developers: List[DeveloperDTO] = []

        self._setup_ui()
        self._load_developers()

    def _setup_ui(self) -> None:
        """Configura interface do dialog."""
        self.setWindowTitle("Gerenciar Desenvolvedores")
        self.setModal(True)
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("<h2>Desenvolvedores</h2>")
        layout.addWidget(title)

        # Lista de desenvolvedores
        self._dev_list = QListWidget()
        self._dev_list.itemDoubleClicked.connect(self._on_edit_developer)
        layout.addWidget(self._dev_list)

        # Botões de ação
        buttons_layout = QHBoxLayout()

        self._add_btn = QPushButton("➕ Adicionar")
        self._add_btn.clicked.connect(self._on_add_developer)
        buttons_layout.addWidget(self._add_btn)

        self._edit_btn = QPushButton("✏️ Editar")
        self._edit_btn.clicked.connect(self._on_edit_developer)
        self._edit_btn.setEnabled(False)
        buttons_layout.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("🗑️ Deletar")
        self._delete_btn.clicked.connect(self._on_delete_developer)
        self._delete_btn.setEnabled(False)
        buttons_layout.addWidget(self._delete_btn)

        buttons_layout.addStretch()

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

        # Conectar seleção
        self._dev_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _load_developers(self) -> None:
        """Carrega lista de desenvolvedores."""
        self._developers = self._developer_controller.list_developers()
        self._update_list()

    def _update_list(self) -> None:
        """Atualiza lista visual de desenvolvedores."""
        self._dev_list.clear()

        for dev in self._developers:
            item = QListWidgetItem(f"{dev.id} - {dev.name}")
            item.setData(Qt.ItemDataRole.UserRole, dev.id)
            self._dev_list.addItem(item)

        # Atualizar contador
        count_label = f"Total: {len(self._developers)} desenvolvedor(es)"
        self.setWindowTitle(f"Gerenciar Desenvolvedores - {count_label}")

    def _on_selection_changed(self) -> None:
        """Callback quando seleção muda."""
        has_selection = len(self._dev_list.selectedItems()) > 0
        self._edit_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)

    def _on_add_developer(self) -> None:
        """Callback para adicionar desenvolvedor."""
        dialog = DeveloperFormDialog(self)
        dialog.developer_saved.connect(self._on_developer_created)
        dialog.exec()

    def _on_developer_created(self, data: dict) -> None:
        """
        Callback quando desenvolvedor é criado.

        Args:
            data: Dados do desenvolvedor
        """
        try:
            self._developer_controller.create_developer(data["name"])
            self._load_developers()
            self.developers_changed.emit()
        except Exception as e:
            MessageBox.error(self, "Erro ao Criar Desenvolvedor", str(e))

    def _on_edit_developer(self) -> None:
        """Callback para editar desenvolvedor."""
        selected_items = self._dev_list.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        dev_id = item.data(Qt.ItemDataRole.UserRole)

        # Buscar desenvolvedor
        developer = next((d for d in self._developers if d.id == dev_id), None)
        if not developer:
            return

        # Abrir dialog de edição
        dialog = DeveloperFormDialog(self, developer)
        dialog.developer_saved.connect(
            lambda data: self._on_developer_updated(dev_id, data)
        )
        dialog.exec()

    def _on_developer_updated(self, dev_id: str, data: dict) -> None:
        """
        Callback quando desenvolvedor é atualizado.

        Args:
            dev_id: ID do desenvolvedor
            data: Novos dados
        """
        try:
            self._developer_controller.update_developer(dev_id, data["name"])
            self._load_developers()
            self.developers_changed.emit()
        except Exception as e:
            MessageBox.error(self, "Erro ao Atualizar Desenvolvedor", str(e))

    def _on_delete_developer(self) -> None:
        """Callback para deletar desenvolvedor."""
        selected_items = self._dev_list.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        dev_id = item.data(Qt.ItemDataRole.UserRole)

        # Buscar desenvolvedor
        developer = next((d for d in self._developers if d.id == dev_id), None)
        if not developer:
            return

        # Confirmação
        if not MessageBox.confirm_delete(self, developer.name):
            return

        try:
            self._developer_controller.delete_developer(dev_id)
            MessageBox.success(
                self,
                "Sucesso",
                f"Desenvolvedor '{developer.name}' deletado com sucesso!"
            )
            self._load_developers()
            self.developers_changed.emit()
        except Exception as e:
            MessageBox.error(self, "Erro ao Deletar Desenvolvedor", str(e))
```

#### 2.2 Integração no MainController

**Arquivo:** `backlog_manager/presentation/controllers/main_controller.py`

```python
# Atualizar método _on_manage_developers:

def _on_manage_developers(self) -> None:
    """Callback de gerenciar desenvolvedores."""
    from backlog_manager.presentation.views.developer_manager_dialog import DeveloperManagerDialog

    dialog = DeveloperManagerDialog(self._main_window, self._developer_controller)
    dialog.developers_changed.connect(self._on_developers_changed)
    dialog.exec()
```

### Testes

```python
# tests/unit/presentation/test_developer_manager.py

def test_manager_dialog_opens(qapp):
    """Deve abrir dialog de gerenciamento"""
    controller = Mock()
    controller.list_developers.return_value = []

    dialog = DeveloperManagerDialog(None, controller)

    assert dialog.windowTitle() == "Gerenciar Desenvolvedores - Total: 0 desenvolvedor(es)"

def test_add_developer_opens_form(qapp):
    """Clicar em Adicionar deve abrir formulário"""
    # Mock controller
    # Click add button
    # Assert: DeveloperFormDialog opened

def test_delete_developer_requires_confirmation(qapp):
    """Deletar deve pedir confirmação"""
    # Setup dialog with 1 developer
    # Select developer
    # Click delete
    # Assert: confirmation dialog shown
```

---

## 3. ProgressDialog (2 SP)

### Implementação Rápida

**Arquivo:** `backlog_manager/presentation/utils/progress_dialog.py`

Já existe um esboço no plano, implementar conforme especificação:

```python
# Uso no MainController para operações longas:

def _on_calculate_schedule(self) -> None:
    """Callback de calcular cronograma."""
    progress = ProgressDialog(
        self._main_window,
        title="Calculando Cronograma",
        message="Ordenando histórias e calculando datas...",
        cancelable=False
    )
    progress.show()

    try:
        self._schedule_controller.calculate_schedule()
        progress.close()
        MessageBox.success(self._main_window, "Sucesso", "Cronograma calculado!")
    except Exception as e:
        progress.close()
        MessageBox.error(self._main_window, "Erro", str(e))
```

---

## 📊 RESUMO E CRONOGRAMA

### Estimativas

| Item | Complexidade | SP | Tempo Estimado |
|------|-------------|-----|----------------|
| DependenciesDialog + Delegate | Alta | 8 | 2-3 dias |
| DeveloperManagerDialog | Média | 5 | 1-2 dias |
| ProgressDialog | Baixa | 2 | 4-6 horas |
| ShortcutsDialog + AboutDialog | Baixa | 2 | 4-6 horas |
| **TOTAL** | - | **17** | **4-6 dias** |

### Ordem de Implementação Recomendada

1. **DeveloperManagerDialog** (mais simples, ganho rápido)
   - Implementar dialog
   - Conectar ao MainController
   - Testar CRUD completo

2. **DependenciesDialog + DependenciesDelegate** (mais complexo)
   - Implementar DependenciesDialog
   - Implementar validação de ciclos
   - Implementar DependenciesDelegate
   - Integrar na tabela
   - Testar seleção e validação

3. **ProgressDialog** (polimento)
   - Implementar dialog básico
   - Integrar em operações longas

4. **ShortcutsDialog + AboutDialog** (documentação)
   - Implementar dialogs simples
   - Adicionar ao menu Ajuda

---

## 🧪 CHECKLIST DE TESTES

### DependenciesDialog
- [ ] Dialog abre e exibe histórias
- [ ] Checkboxes funcionam
- [ ] Busca filtra corretamente
- [ ] Detecção de ciclos funciona
- [ ] Botão OK desabilitado quando há ciclo
- [ ] Seleções são salvas corretamente

### DeveloperManagerDialog
- [ ] Dialog lista todos os desenvolvedores
- [ ] Adicionar abre formulário e cria desenvolvedor
- [ ] Editar abre formulário com dados preenchidos
- [ ] Deletar pede confirmação e remove desenvolvedor
- [ ] Lista atualiza após operações

### ProgressDialog
- [ ] Dialog aparece durante operações longas
- [ ] Mensagem é clara
- [ ] Dialog fecha automaticamente

---

## 🚀 PRÓXIMOS PASSOS

Após implementar esses itens, a Fase 4 estará **completa** com todas as funcionalidades críticas.

**Funcionalidades Restantes (Fase 5 - Opcional):**
- Timeline/Roadmap visualization
- Sistema de filtros avançados
- Export para outros formatos (PDF, CSV)
- Temas customizáveis
- Undo/Redo

**Pronto para implementar?** Sugiro começar pelo **DeveloperManagerDialog** por ser mais simples e dar ganho rápido de funcionalidade!
