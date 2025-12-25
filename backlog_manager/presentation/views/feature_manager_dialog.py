"""
Dialog para gerenciamento completo de features.

Permite criar, editar e deletar features com interface de lista.
"""
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from backlog_manager.application.dto.feature_dto import FeatureDTO
from backlog_manager.presentation.views.feature_form import FeatureFormDialog


class FeatureManagerDialog(QDialog):
    """Dialog para gerenciamento de features."""

    # Sinais
    feature_created = Signal(str, int)  # name, wave
    feature_updated = Signal(str, str, int)  # feature_id, new_name, new_wave
    feature_deleted = Signal(str)  # feature_id
    features_changed = Signal()  # Notifica quando lista muda

    def __init__(self, parent, features: List[FeatureDTO]):
        """
        Inicializa o dialog.

        Args:
            parent: Widget pai
            features: Lista de features existentes
        """
        super().__init__(parent)
        self._features = features
        self.setWindowTitle("Gerenciar Features")
        self.setModal(True)
        self.resize(600, 450)

        self._setup_ui()
        self._populate_list()

    def _setup_ui(self) -> None:
        """Configura interface do dialog."""
        layout = QVBoxLayout(self)

        # Título e descrição
        title = QLabel("Features e Ondas de Entrega")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title)

        description = QLabel(
            "Features organizam histórias em ondas de entrega.\n"
            "Cada onda representa um marco incremental do projeto."
        )
        description.setStyleSheet("color: #757575; margin-bottom: 10px;")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Lista de features
        self._list_widget = QListWidget()
        self._list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self._list_widget.itemDoubleClicked.connect(self._on_edit)
        layout.addWidget(self._list_widget)

        # Label de informação
        info_label = QLabel("Dica: Clique duas vezes para editar uma feature")
        info_label.setStyleSheet("color: #757575; font-size: 9pt; font-style: italic;")
        layout.addWidget(info_label)

        # Botões de ação
        button_layout = QHBoxLayout()

        self._add_button = QPushButton("Nova Feature")
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
        close_button.setProperty("primary", True)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _populate_list(self) -> None:
        """Popula lista de features ordenada por onda."""
        self._list_widget.clear()

        # Ordenar por onda
        sorted_features = sorted(self._features, key=lambda f: f.wave)

        for feature in sorted_features:
            # Formato: "Onda 1: MVP - Core Features (ID: MVP)"
            item_text = f"Onda {feature.wave}: {feature.name} (ID: {feature.id})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, feature.id)
            self._list_widget.addItem(item)

    def _on_selection_changed(self) -> None:
        """Callback quando seleção muda."""
        has_selection = bool(self._list_widget.selectedItems())
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

    def _on_add(self) -> None:
        """Callback para adicionar feature."""
        dialog = FeatureFormDialog(self)
        dialog.feature_saved.connect(self._handle_feature_created)
        dialog.exec()

    def _on_edit(self) -> None:
        """Callback para editar feature."""
        selected_items = self._list_widget.selectedItems()
        if not selected_items:
            return

        feature_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # Buscar feature
        feature = next((f for f in self._features if f.id == feature_id), None)
        if not feature:
            return

        dialog = FeatureFormDialog(self, feature)
        dialog.feature_saved.connect(self._handle_feature_updated)
        dialog.exec()

    def _on_delete(self) -> None:
        """Callback para deletar feature."""
        selected_items = self._list_widget.selectedItems()
        if not selected_items:
            return

        feature_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.feature_deleted.emit(feature_id)
        self.features_changed.emit()

    def _handle_feature_created(self, form_data: dict) -> None:
        """
        Trata criação de feature.

        Args:
            form_data: Dados do formulário
        """
        self.feature_created.emit(form_data["name"], form_data["wave"])
        self.features_changed.emit()

    def _handle_feature_updated(self, form_data: dict) -> None:
        """
        Trata atualização de feature.

        Args:
            form_data: Dados do formulário
        """
        self.feature_updated.emit(form_data["id"], form_data["name"], form_data["wave"])
        self.features_changed.emit()

    def refresh(self, features: List[FeatureDTO]) -> None:
        """
        Atualiza lista de features.

        Args:
            features: Nova lista de features
        """
        self._features = features
        self._populate_list()
