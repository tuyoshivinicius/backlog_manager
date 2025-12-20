"""
Formulário para criação e edição de desenvolvedores.

Permite criar novos desenvolvedores ou editar existentes.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
)
from PySide6.QtCore import Signal

from backlog_manager.application.dto.developer_dto import DeveloperDTO


class DeveloperFormDialog(QDialog):
    """Formulário para criação/edição de desenvolvedor."""

    # Sinais
    developer_saved = Signal(dict)  # Dados do formulário

    def __init__(self, parent=None, developer: Optional[DeveloperDTO] = None):
        """
        Inicializa o formulário.

        Args:
            parent: Widget pai
            developer: Desenvolvedor a editar (None para criar novo)
        """
        super().__init__(parent)
        self._developer = developer
        self._is_edit_mode = developer is not None

        self._setup_ui()
        if developer:
            self._populate_from_developer(developer)

    def _setup_ui(self) -> None:
        """Configura a interface do formulário."""
        title = "Editar Desenvolvedor" if self._is_edit_mode else "Novo Desenvolvedor"
        if self._is_edit_mode and self._developer:
            title = f"Editar Desenvolvedor - {self._developer.name}"

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)

        # Layout principal
        main_layout = QVBoxLayout()

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # ID (apenas em modo edição, read-only)
        if self._is_edit_mode:
            self._id_label = QLabel(self._developer.id if self._developer else "")
            form_layout.addRow("ID:", self._id_label)

        # Nome
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Ex: Gabriel Alves")
        form_layout.addRow("Nome*:", self._name_input)

        # Explicação sobre ID
        if not self._is_edit_mode:
            info_label = QLabel("O ID será gerado automaticamente baseado no nome.")
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #757575; font-size: 9pt;")
            form_layout.addRow("", info_label)

        main_layout.addLayout(form_layout)

        # Label de erro
        self._error_label = QLabel()
        self._error_label.setProperty("error", True)
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        main_layout.addWidget(self._error_label)

        # Botões
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._save_button = QPushButton("Salvar")
        self._save_button.clicked.connect(self._on_save)
        button_layout.addWidget(self._save_button)

        cancel_button = QPushButton("Cancelar")
        cancel_button.setProperty("secondary", True)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Conectar validações
        self._name_input.textChanged.connect(self._validate)

        # Validação inicial
        self._validate()

    def _populate_from_developer(self, developer: DeveloperDTO) -> None:
        """
        Preenche formulário com dados do desenvolvedor.

        Args:
            developer: Desenvolvedor a editar
        """
        self._name_input.setText(developer.name)

    def _validate(self) -> None:
        """Valida campos do formulário."""
        name = self._name_input.text().strip()

        errors = []

        if not name:
            errors.append("Nome é obrigatório")
        elif len(name) < 2:
            errors.append("Nome deve ter pelo menos 2 caracteres")

        if errors:
            self._error_label.setText("\n".join(errors))
            self._error_label.show()
            self._save_button.setEnabled(False)
        else:
            self._error_label.hide()
            self._save_button.setEnabled(True)

    def _on_save(self) -> None:
        """Callback de salvamento."""
        # Coletar dados
        form_data = {
            "name": self._name_input.text().strip(),
        }

        # Se modo edição, incluir ID
        if self._is_edit_mode and self._developer:
            form_data["id"] = self._developer.id

        # Emitir sinal
        self.developer_saved.emit(form_data)

        # Fechar dialog
        self.accept()
