"""
Diálogo de configurações do sistema.

Permite configurar velocidade do time (SP por sprint e dias úteis).
"""
from datetime import date, timedelta
from typing import Optional

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from backlog_manager.application.dto.configuration_dto import ConfigurationDTO
from backlog_manager.domain.value_objects.allocation_criteria import AllocationCriteria


class ConfigurationDialog(QDialog):
    """Diálogo de configurações do sistema."""

    # Sinais
    configuration_saved = Signal(dict)  # Dados da configuração

    DEFAULT_SP_PER_SPRINT = 21
    DEFAULT_WORKDAYS_PER_SPRINT = 15
    DEFAULT_MAX_IDLE_DAYS = 3

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

        # Data de Início do Roadmap
        date_layout = QHBoxLayout()
        self._roadmap_start_date_edit = QDateEdit()
        self._roadmap_start_date_edit.setCalendarPopup(True)
        self._roadmap_start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self._roadmap_start_date_edit.setMinimumDate(QDate.currentDate())
        self._roadmap_start_date_edit.setDate(QDate.currentDate())
        self._roadmap_start_date_edit.dateChanged.connect(self._validate_workday)
        date_layout.addWidget(self._roadmap_start_date_edit)

        self._use_current_date_btn = QPushButton("Usar Data Atual")
        self._use_current_date_btn.setProperty("secondary", True)
        self._use_current_date_btn.clicked.connect(self._set_current_date)
        date_layout.addWidget(self._use_current_date_btn)

        form_layout.addRow("Data de Início do Roadmap:", date_layout)

        # Velocidade calculada
        self._velocity_label = QLabel()
        self._velocity_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow("Velocidade por Dia:", self._velocity_label)

        # Critério de Alocação de Desenvolvedores
        self._allocation_criteria_combo = QComboBox()
        for criteria in AllocationCriteria:
            display_name = AllocationCriteria.get_display_name(criteria)
            self._allocation_criteria_combo.addItem(display_name, criteria.value)

        # Tooltip com descrição de cada critério
        tooltip_text = "\n\n".join(
            f"{AllocationCriteria.get_display_name(c)}: {AllocationCriteria.get_description(c)}"
            for c in AllocationCriteria
        )
        self._allocation_criteria_combo.setToolTip(tooltip_text)
        form_layout.addRow("Critério de Alocação:", self._allocation_criteria_combo)

        # Máximo de Dias Ociosos (dentro da mesma onda)
        self._max_idle_days_spin = QSpinBox()
        self._max_idle_days_spin.setRange(2, 30)  # Mínimo de 2 dias
        self._max_idle_days_spin.setValue(self.DEFAULT_MAX_IDLE_DAYS)
        self._max_idle_days_spin.setSuffix(" dias")
        self._max_idle_days_spin.setToolTip(
            "Máximo de dias úteis ociosos permitidos DENTRO DA MESMA ONDA.\n\n"
            "Este limite só se aplica entre histórias da mesma onda.\n"
            "A ociosidade entre ondas diferentes é permitida normalmente,\n"
            "pois as ondas são processadas sequencialmente.\n\n"
            "Se todos os desenvolvedores excederem este limite na onda,\n"
            "será escolhido o com menor ociosidade."
        )
        form_layout.addRow("Ociosidade Máxima na Onda:", self._max_idle_days_spin)

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

        # Aviso sobre dias úteis
        warning_label = QLabel(
            "⚠️ A data de início deve ser um dia útil (segunda a sexta). "
            "Se selecionar fim de semana, será ajustada automaticamente."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(
            "color: #FF8C00; padding: 10px; background-color: #FFF8DC; "
            "border-radius: 5px; margin-top: 8px;"
        )
        main_layout.addWidget(warning_label)

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

        # Carregar data de início do roadmap se existir
        if hasattr(configuration, "roadmap_start_date") and configuration.roadmap_start_date:
            # ConfigurationDTO pode ter roadmap_start_date como string ISO ou date
            if isinstance(configuration.roadmap_start_date, str):
                start_date = date.fromisoformat(configuration.roadmap_start_date)
            else:
                start_date = configuration.roadmap_start_date

            qdate = QDate(start_date.year, start_date.month, start_date.day)
            self._roadmap_start_date_edit.setDate(qdate)

        # Carregar critério de alocação
        if hasattr(configuration, "allocation_criteria") and configuration.allocation_criteria:
            # Encontrar o índice do item com o valor correspondente
            index = self._allocation_criteria_combo.findData(configuration.allocation_criteria)
            if index >= 0:
                self._allocation_criteria_combo.setCurrentIndex(index)

        # Carregar máximo de dias ociosos
        if hasattr(configuration, "max_idle_days") and configuration.max_idle_days is not None:
            self._max_idle_days_spin.setValue(configuration.max_idle_days)

    def _update_velocity_label(self) -> None:
        """Atualiza label de velocidade calculada."""
        sp = self._sp_per_sprint_spin.value()
        workdays = self._workdays_per_sprint_spin.value()

        if workdays > 0:
            velocity = sp / workdays
            self._velocity_label.setText(f"{velocity:.2f} SP/dia")
        else:
            self._velocity_label.setText("N/A")

    def _validate_workday(self, qdate: QDate) -> None:
        """
        Valida se a data selecionada é um dia útil.
        Se for fim de semana, ajusta para próxima segunda-feira.

        Args:
            qdate: Data selecionada no QDateEdit
        """
        python_date = date(qdate.year(), qdate.month(), qdate.day())

        # Se for fim de semana (sábado=5, domingo=6), ajustar
        if python_date.weekday() >= 5:
            # Calcular próxima segunda-feira
            days_until_monday = 7 - python_date.weekday()
            next_monday = python_date + timedelta(days=days_until_monday)

            # Atualizar QDateEdit
            self._roadmap_start_date_edit.setDate(QDate(next_monday.year, next_monday.month, next_monday.day))

            QMessageBox.information(
                self,
                "Dia Útil Requerido",
                f"Fim de semana não é permitido. Data ajustada para {next_monday.strftime('%d/%m/%Y')} (segunda-feira).",
            )

    def _set_current_date(self) -> None:
        """Define data de início como data atual (ou próxima segunda se hoje for fim de semana)."""
        current_date = date.today()

        # Se hoje for fim de semana, ajustar para próxima segunda
        if current_date.weekday() >= 5:
            days_until_monday = 7 - current_date.weekday()
            current_date = current_date + timedelta(days=days_until_monday)

        self._roadmap_start_date_edit.setDate(QDate(current_date.year, current_date.month, current_date.day))

    def _restore_defaults(self) -> None:
        """Restaura valores padrão."""
        self._sp_per_sprint_spin.setValue(self.DEFAULT_SP_PER_SPRINT)
        self._workdays_per_sprint_spin.setValue(self.DEFAULT_WORKDAYS_PER_SPRINT)
        self._max_idle_days_spin.setValue(self.DEFAULT_MAX_IDLE_DAYS)
        self._set_current_date()

    def _on_save(self) -> None:
        """Callback de salvamento."""
        # Converter QDate para date
        qdate = self._roadmap_start_date_edit.date()
        python_date = date(qdate.year(), qdate.month(), qdate.day())

        # Última validação de dia útil
        if python_date.weekday() >= 5:
            QMessageBox.warning(self, "Data Inválida", "A data de início deve ser um dia útil (segunda a sexta).")
            return

        # Obter critério de alocação selecionado
        allocation_criteria = self._allocation_criteria_combo.currentData()

        # Coletar dados
        config_data = {
            "story_points_per_sprint": self._sp_per_sprint_spin.value(),
            "workdays_per_sprint": self._workdays_per_sprint_spin.value(),
            "roadmap_start_date": python_date,
            "allocation_criteria": allocation_criteria,
            "max_idle_days": self._max_idle_days_spin.value(),
        }

        # Emitir sinal
        self.configuration_saved.emit(config_data)

        # Fechar dialog
        self.accept()
