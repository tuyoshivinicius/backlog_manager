"""
Formulário para criação e edição de features.

Permite criar novas features ou editar existentes.
"""
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from backlog_manager.application.dto.feature_dto import FeatureDTO


class FeatureFormDialog(QDialog):
    """Formulário para criação/edição de feature."""

    # Sinais
    feature_saved = Signal(dict)  # Dados do formulário

    def __init__(self, parent=None, feature: Optional[FeatureDTO] = None):
        """
        Inicializa o formulário.

        Args:
            parent: Widget pai
            feature: Feature a editar (None para criar nova)
        """
        super().__init__(parent)
        self._feature = feature
        self._is_edit_mode = feature is not None

        self._setup_ui()
        if feature:
            self._populate_from_feature(feature)

    def _setup_ui(self) -> None:
        """Configura a interface do formulário."""
        title = "Editar Feature" if self._is_edit_mode else "Nova Feature"
        if self._is_edit_mode and self._feature:
            title = f"Editar Feature - {self._feature.name}"

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setMinimumHeight(250)

        # Layout principal
        main_layout = QVBoxLayout()

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # ID (apenas em modo edição, read-only)
        if self._is_edit_mode:
            self._id_label = QLabel(self._feature.id if self._feature else "")
            self._id_label.setStyleSheet("font-weight: bold;")
            form_layout.addRow("ID:", self._id_label)

        # Nome
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Ex: MVP - Core Features")
        form_layout.addRow("Nome*:", self._name_input)

        # Explicação sobre ID
        if not self._is_edit_mode:
            info_label = QLabel(
                "O ID será gerado automaticamente a partir das 3 primeiras letras do nome."
            )
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #757575; font-size: 9pt;")
            form_layout.addRow("", info_label)

        # Onda
        self._wave_input = QSpinBox()
        self._wave_input.setMinimum(1)
        self._wave_input.setMaximum(999)
        self._wave_input.setValue(1)
        self._wave_input.setSuffix("")
        wave_help = QLabel("Número da onda de entrega (1 = primeira onda)")
        wave_help.setStyleSheet("color: #757575; font-size: 9pt;")
        form_layout.addRow("Onda*:", self._wave_input)
        form_layout.addRow("", wave_help)

        main_layout.addLayout(form_layout)

        # Separador visual
        separator = QLabel()
        separator.setStyleSheet("border-bottom: 1px solid #e0e0e0; margin: 10px 0;")
        main_layout.addWidget(separator)

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
        self._wave_input.valueChanged.connect(self._validate)

        # Validação inicial
        self._validate()

    def _populate_from_feature(self, feature: FeatureDTO) -> None:
        """
        Preenche formulário com dados da feature.

        Args:
            feature: Feature a editar
        """
        self._name_input.setText(feature.name)
        self._wave_input.setValue(feature.wave)

    def _validate(self) -> None:
        """Valida campos do formulário."""
        name = self._name_input.text().strip()
        wave = self._wave_input.value()

        errors = []

        if not name:
            errors.append("Nome é obrigatório")
        elif len(name) < 3:
            errors.append("Nome deve ter pelo menos 3 caracteres")

        if wave < 1:
            errors.append("Onda deve ser um número positivo")

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
            "wave": self._wave_input.value(),
        }

        # Se modo edição, incluir ID
        if self._is_edit_mode and self._feature:
            form_data["id"] = self._feature.id

        # Emitir sinal
        self.feature_saved.emit(form_data)

        # Fechar dialog
        self.accept()
