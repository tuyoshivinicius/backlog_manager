"""
Diálogo de configurações do sistema.

Permite configurar velocidade do time (SP por sprint e dias úteis).
"""
from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
)
from PySide6.QtCore import Signal

from backlog_manager.application.dto.configuration_dto import ConfigurationDTO


class ConfigurationDialog(QDialog):
    """Diálogo de configurações do sistema."""

    # Sinais
    configuration_saved = Signal(dict)  # Dados da configuração

    DEFAULT_SP_PER_SPRINT = 21
    DEFAULT_WORKDAYS_PER_SPRINT = 15

    def __init__(self, parent=None, configuration: Optional[ConfigurationDTO] = None):
        """
        Inicializa o diálogo.

        Args:
            parent: Widget pai
            configuration: Configuração atual (None para valores padrão)
        """
        super().__init__(parent)
        self._configuration = configuration
        self._setup_ui()

        if configuration:
            self._populate_from_configuration(configuration)

    def _setup_ui(self) -> None:
        """Configura a interface do diálogo."""
        self.setWindowTitle("Configurações do Sistema")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)

        # Layout principal
        main_layout = QVBoxLayout()

        # Título
        title_label = QLabel("Configurações de Velocidade do Time")
        title_label.setProperty("heading", True)
        main_layout.addWidget(title_label)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Story Points por Sprint
        self._sp_per_sprint_spin = QSpinBox()
        self._sp_per_sprint_spin.setRange(1, 100)
        self._sp_per_sprint_spin.setValue(self.DEFAULT_SP_PER_SPRINT)
        self._sp_per_sprint_spin.setSuffix(" SP")
        form_layout.addRow("Story Points por Sprint:", self._sp_per_sprint_spin)

        # Dias Úteis por Sprint
        self._workdays_per_sprint_spin = QSpinBox()
        self._workdays_per_sprint_spin.setRange(1, 30)
        self._workdays_per_sprint_spin.setValue(self.DEFAULT_WORKDAYS_PER_SPRINT)
        self._workdays_per_sprint_spin.setSuffix(" dias")
        form_layout.addRow("Dias Úteis por Sprint:", self._workdays_per_sprint_spin)

        # Velocidade calculada
        self._velocity_label = QLabel()
        self._velocity_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow("Velocidade por Dia:", self._velocity_label)

        main_layout.addLayout(form_layout)

        # Explicação
        help_text = (
            "A velocidade por dia é calculada automaticamente dividindo "
            "os Story Points por Sprint pelos Dias Úteis. "
            "Este valor é usado para calcular a duração das histórias."
        )
        help_label = QLabel(help_text)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #757575; font-size: 9pt; margin-top: 8px;")
        main_layout.addWidget(help_label)

        main_layout.addStretch()

        # Botões
        button_layout = QHBoxLayout()

        restore_button = QPushButton("Restaurar Padrões")
        restore_button.setProperty("secondary", True)
        restore_button.clicked.connect(self._restore_defaults)
        button_layout.addWidget(restore_button)

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

        # Conectar sinais para atualizar velocidade
        self._sp_per_sprint_spin.valueChanged.connect(self._update_velocity_label)
        self._workdays_per_sprint_spin.valueChanged.connect(self._update_velocity_label)

        # Atualizar velocidade inicial
        self._update_velocity_label()

    def _populate_from_configuration(self, configuration: ConfigurationDTO) -> None:
        """
        Preenche formulário com configuração atual.

        Args:
            configuration: Configuração atual
        """
        self._sp_per_sprint_spin.setValue(configuration.story_points_per_sprint)
        self._workdays_per_sprint_spin.setValue(configuration.workdays_per_sprint)

    def _update_velocity_label(self) -> None:
        """Atualiza label de velocidade calculada."""
        sp = self._sp_per_sprint_spin.value()
        workdays = self._workdays_per_sprint_spin.value()

        if workdays > 0:
            velocity = sp / workdays
            self._velocity_label.setText(f"{velocity:.2f} SP/dia")
        else:
            self._velocity_label.setText("N/A")

    def _restore_defaults(self) -> None:
        """Restaura valores padrão."""
        self._sp_per_sprint_spin.setValue(self.DEFAULT_SP_PER_SPRINT)
        self._workdays_per_sprint_spin.setValue(self.DEFAULT_WORKDAYS_PER_SPRINT)

    def _on_save(self) -> None:
        """Callback de salvamento."""
        # Coletar dados
        config_data = {
            "story_points_per_sprint": self._sp_per_sprint_spin.value(),
            "workdays_per_sprint": self._workdays_per_sprint_spin.value(),
        }

        # Emitir sinal
        self.configuration_saved.emit(config_data)

        # Fechar dialog
        self.accept()
