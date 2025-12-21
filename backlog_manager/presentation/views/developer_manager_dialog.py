"""
Dialog para gerenciamento completo de desenvolvedores.

Permite criar, editar e deletar desenvolvedores com interface de lista.
"""
from typing import List, Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
)
from PySide6.QtCore import Signal, Qt

from backlog_manager.application.dto.developer_dto import DeveloperDTO


class DeveloperManagerDialog(QDialog):
    """Dialog para gerenciamento de desenvolvedores."""

    # Sinais
    developer_created = Signal(str)  # name
    developer_updated = Signal(str, str)  # developer_id, new_name
    developer_deleted = Signal(str)  # developer_id
    developers_changed = Signal()  # Notifica quando lista muda

    def __init__(self, parent, developers: List[DeveloperDTO]):
        """
        Inicializa o dialog.

        Args:
            parent: Widget pai
            developers: Lista de desenvolvedores existentes
        """
        super().__init__(parent)
        self._developers = developers
        self.setWindowTitle("Gerenciar Desenvolvedores")
        self.setModal(True)
        self.resize(500, 400)

        self._setup_ui()
        self._populate_list()

    def _setup_ui(self) -> None:
        """Configura interface do dialog."""
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Desenvolvedores Cadastrados")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title)

        # Lista de desenvolvedores
        self._list_widget = QListWidget()
        self._list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list_widget)

        # Botões de ação
        button_layout = QHBoxLayout()

        self._add_button = QPushButton("Adicionar")
        self._add_button.clicked.connect(self._on_add)
        button_layout.addWidget(self._add_button)

        self._edit_button = QPushButton("Editar")
        self._edit_button.setEnabled(False)
        self._edit_button.clicked.connect(self._on_edit)
        button_layout.addWidget(self._edit_button)

        self._delete_button = QPushButton("Deletar")
        self._delete_button.setEnabled(False)
        self._delete_button.clicked.connect(self._on_delete)
        button_layout.addWidget(self._delete_button)

        button_layout.addStretch()

        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _populate_list(self) -> None:
        """Popula lista de desenvolvedores."""
        self._list_widget.clear()
        for dev in self._developers:
            item = QListWidgetItem(f"{dev.name} ({dev.id})")
            item.setData(Qt.ItemDataRole.UserRole, dev.id)
            self._list_widget.addItem(item)

    def _on_selection_changed(self) -> None:
        """Callback quando seleção muda."""
        has_selection = bool(self._list_widget.selectedItems())
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

    def _on_add(self) -> None:
        """Callback de adicionar desenvolvedor."""
        from backlog_manager.presentation.views.developer_form import (
            DeveloperFormDialog,
        )

        dialog = DeveloperFormDialog(self)
        dialog.developer_saved.connect(self._on_developer_created)
        dialog.exec()

    def _on_edit(self) -> None:
        """Callback de editar desenvolvedor."""
        selected_items = self._list_widget.selectedItems()
        if not selected_items:
            return

        # Obter ID do desenvolvedor selecionado
        item = selected_items[0]
        developer_id = item.data(Qt.ItemDataRole.UserRole)

        # Buscar desenvolvedor na lista
        developer = next((d for d in self._developers if d.id == developer_id), None)
        if not developer:
            return

        # Abrir formulário de edição
        from backlog_manager.presentation.views.developer_form import (
            DeveloperFormDialog,
        )

        dialog = DeveloperFormDialog(self, developer)
        dialog.developer_saved.connect(
            lambda data: self._on_developer_updated(developer_id, data["name"])
        )
        dialog.exec()

    def _on_delete(self) -> None:
        """Callback de deletar desenvolvedor."""
        selected_items = self._list_widget.selectedItems()
        if not selected_items:
            return

        # Obter ID do desenvolvedor selecionado
        item = selected_items[0]
        developer_id = item.data(Qt.ItemDataRole.UserRole)

        # Buscar desenvolvedor na lista
        developer = next((d for d in self._developers if d.id == developer_id), None)
        if not developer:
            return

        # Emitir sinal de deleção (confirmação será feita pelo controller)
        self.developer_deleted.emit(developer_id)

    def _on_developer_created(self, form_data: dict) -> None:
        """
        Callback quando desenvolvedor é criado.

        Args:
            form_data: Dados do formulário
        """
        # Emitir sinal
        self.developer_created.emit(form_data["name"])

    def _on_developer_updated(self, developer_id: str, new_name: str) -> None:
        """
        Callback quando desenvolvedor é atualizado.

        Args:
            developer_id: ID do desenvolvedor
            new_name: Novo nome
        """
        # Emitir sinal
        self.developer_updated.emit(developer_id, new_name)

    def refresh_developers(self, developers: List[DeveloperDTO]) -> None:
        """
        Atualiza lista de desenvolvedores.

        Args:
            developers: Nova lista de desenvolvedores
        """
        self._developers = developers
        self._populate_list()
