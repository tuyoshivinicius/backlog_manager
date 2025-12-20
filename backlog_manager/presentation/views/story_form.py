"""
Formulário para criação e edição de histórias.

Permite criar novas histórias ou editar histórias existentes
com validações em tempo real.
"""
from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
)
from PySide6.QtCore import Signal, Qt

from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.domain.value_objects.story_status import StoryStatus


class StoryFormDialog(QDialog):
    """Formulário para criação/edição de história."""

    # Sinais
    story_saved = Signal(dict)  # Dados do formulário

    def __init__(
        self,
        parent=None,
        story: Optional[StoryDTO] = None,
        developers: Optional[List[DeveloperDTO]] = None,
    ):
        """
        Inicializa o formulário.

        Args:
            parent: Widget pai
            story: História a editar (None para criar nova)
            developers: Lista de desenvolvedores disponíveis
        """
        super().__init__(parent)
        self._story = story
        self._developers = developers or []
        self._is_edit_mode = story is not None

        self._setup_ui()
        if story:
            self._populate_from_story(story)

    def _setup_ui(self) -> None:
        """Configura a interface do formulário."""
        title = "Editar História" if self._is_edit_mode else "Nova História"
        if self._is_edit_mode and self._story:
            title = f"Editar História - {self._story.id}"

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        # Layout principal
        main_layout = QVBoxLayout()

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # ID (apenas em modo edição, read-only)
        if self._is_edit_mode:
            self._id_label = QLabel(self._story.id if self._story else "")
            form_layout.addRow("ID:", self._id_label)

        # Feature
        self._feature_input = QLineEdit()
        self._feature_input.setPlaceholderText("Ex: Login, Dashboard")
        form_layout.addRow("Feature*:", self._feature_input)

        # Nome
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Ex: Implementar tela de login")
        form_layout.addRow("Nome*:", self._name_input)

        # Story Point
        self._story_point_combo = QComboBox()
        self._story_point_combo.addItems(["3", "5", "8", "13"])
        form_layout.addRow("Story Point*:", self._story_point_combo)

        # Status
        self._status_combo = QComboBox()
        self._status_combo.addItems([status.value for status in StoryStatus])
        form_layout.addRow("Status*:", self._status_combo)

        # Desenvolvedor
        self._developer_combo = QComboBox()
        self._developer_combo.addItem("(Nenhum)", None)
        for dev in self._developers:
            self._developer_combo.addItem(dev.name, dev.id)
        form_layout.addRow("Desenvolvedor:", self._developer_combo)

        # Prioridade
        self._priority_spin = QSpinBox()
        self._priority_spin.setRange(1, 1000)
        self._priority_spin.setValue(1)
        form_layout.addRow("Prioridade:", self._priority_spin)

        main_layout.addLayout(form_layout)

        # Campos calculados (apenas em modo edição)
        if self._is_edit_mode and self._story:
            calc_layout = QFormLayout()
            calc_layout.setSpacing(8)

            # Data início
            start_text = (
                self._story.start_date.strftime("%d/%m/%Y")
                if self._story.start_date
                else "Não calculado"
            )
            self._start_date_label = QLabel(start_text)
            calc_layout.addRow("Data Início:", self._start_date_label)

            # Data fim
            end_text = (
                self._story.end_date.strftime("%d/%m/%Y")
                if self._story.end_date
                else "Não calculado"
            )
            self._end_date_label = QLabel(end_text)
            calc_layout.addRow("Data Fim:", self._end_date_label)

            # Duração
            duration_text = (
                f"{self._story.duration} dias"
                if self._story.duration
                else "Não calculado"
            )
            self._duration_label = QLabel(duration_text)
            calc_layout.addRow("Duração:", self._duration_label)

            main_layout.addLayout(calc_layout)

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
        self._feature_input.textChanged.connect(self._validate)
        self._name_input.textChanged.connect(self._validate)

        # Validação inicial
        self._validate()

    def _populate_from_story(self, story: StoryDTO) -> None:
        """
        Preenche formulário com dados da história.

        Args:
            story: História a editar
        """
        self._feature_input.setText(story.feature)
        self._name_input.setText(story.name)

        # Story Point
        sp_idx = self._story_point_combo.findText(str(story.story_point))
        if sp_idx >= 0:
            self._story_point_combo.setCurrentIndex(sp_idx)

        # Status
        status_idx = self._status_combo.findText(story.status)
        if status_idx >= 0:
            self._status_combo.setCurrentIndex(status_idx)

        # Desenvolvedor
        if story.developer_id:
            for i in range(self._developer_combo.count()):
                if self._developer_combo.itemData(i) == story.developer_id:
                    self._developer_combo.setCurrentIndex(i)
                    break

        # Prioridade
        self._priority_spin.setValue(story.priority)

    def _validate(self) -> None:
        """Valida campos do formulário."""
        feature = self._feature_input.text().strip()
        name = self._name_input.text().strip()

        errors = []

        if not feature:
            errors.append("Feature é obrigatória")
        if not name:
            errors.append("Nome é obrigatório")
        elif len(name) < 5:
            errors.append("Nome deve ter pelo menos 5 caracteres")

        if errors:
            self._error_label.setText("\n".join(errors))
            self._error_label.show()
            self._save_button.setEnabled(False)
        else:
            self._error_label.hide()
            self._save_button.setEnabled(True)

    def _on_save(self) -> None:
        """Callback de salvamento."""
        print("\n" + "="*60)
        print("DEBUG: StoryFormDialog._on_save() INICIADO")
        print("="*60)

        # Coletar dados
        print("\n1. Coletando dados do formulário...")
        form_data = {
            "feature": self._feature_input.text().strip(),
            "name": self._name_input.text().strip(),
            "story_point": int(self._story_point_combo.currentText()),
            "status": self._status_combo.currentText(),
            "developer_id": self._developer_combo.currentData(),
            "priority": self._priority_spin.value(),
        }
        print(f"[OK] Dados coletados: {form_data}")

        # Se modo edição, incluir ID
        if self._is_edit_mode and self._story:
            form_data["id"] = self._story.id
            print(f"[INFO] Modo edição - ID incluído: {form_data['id']}")

        # Emitir sinal
        print("\n2. Emitindo sinal story_saved...")
        self.story_saved.emit(form_data)
        print("[OK] Sinal emitido")

        # Fechar dialog
        print("\n3. Fechando dialog (accept)...")
        self.accept()
        print("[OK] Dialog fechado")

        print("\n" + "="*60)
        print("DEBUG: StoryFormDialog._on_save() CONCLUÍDO")
        print("="*60 + "\n")
