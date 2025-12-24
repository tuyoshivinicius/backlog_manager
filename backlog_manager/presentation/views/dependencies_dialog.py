"""
Dialog para seleção de dependências de uma história.

Permite selecionar histórias das quais a história atual depende,
com validação em tempo real de ciclos de dependências.
"""
from typing import List, Set
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLabel,
)
from PySide6.QtCore import Qt

from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.domain.services.cycle_detector import CycleDetector


class DependenciesDialog(QDialog):
    """Dialog para seleção de dependências de uma história."""

    def __init__(
        self,
        parent,
        current_story: StoryDTO,
        all_stories: List[StoryDTO],
        current_dependencies: List[str],
    ):
        """
        Inicializa o dialog.

        Args:
            parent: Widget pai
            current_story: História atual sendo editada
            all_stories: Lista de todas as histórias disponíveis
            current_dependencies: Lista de IDs das dependências atuais
        """
        super().__init__(parent)
        self._current_story = current_story
        self._all_stories = all_stories
        self._current_dependencies = set(current_dependencies)
        self._cycle_detector = CycleDetector()

        self.setWindowTitle(f"Dependências - {current_story.id}")
        self.setModal(True)
        self.resize(600, 500)

        self._setup_ui()
        self._populate_list()
        self._validate_selection()

    def _setup_ui(self) -> None:
        """Configura interface do dialog."""
        layout = QVBoxLayout(self)

        # Título e descrição
        title = QLabel(f"Selecione as dependências para: {self._current_story.name}")
        title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        title.setWordWrap(True)
        layout.addWidget(title)

        info = QLabel(
            "Marque as histórias das quais esta história depende. "
            "Histórias dependentes devem ser concluídas antes desta."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)

        # Lista de histórias com checkboxes
        self._list_widget = QListWidget()
        self._list_widget.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._list_widget)

        # Label de erro/aviso
        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(
            "color: #d32f2f; background-color: #ffebee; "
            "padding: 8px; border-radius: 4px; font-weight: bold;"
        )
        self._error_label.hide()
        layout.addWidget(self._error_label)

        # Label de informação
        self._info_label = QLabel()
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet(
            "color: #1976d2; background-color: #e3f2fd; "
            "padding: 8px; border-radius: 4px;"
        )
        self._info_label.hide()
        layout.addWidget(self._info_label)

        # Botões
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._ok_button = QPushButton("OK")
        self._ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self._ok_button)

        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def _populate_list(self) -> None:
        """Popula lista de histórias disponíveis."""
        # Desconectar temporariamente o sinal
        self._list_widget.itemChanged.disconnect(self._on_item_changed)

        for story in self._all_stories:
            # Não mostrar a própria história na lista
            if story.id == self._current_story.id:
                continue

            # Criar item com checkbox
            text = f"{story.id} - {story.component} - {story.name}"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            # Marcar se é dependência atual
            if story.id in self._current_dependencies:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            # Armazenar ID no item
            item.setData(Qt.ItemDataRole.UserRole, story.id)

            self._list_widget.addItem(item)

        # Reconectar sinal
        self._list_widget.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        """
        Callback quando checkbox é alterado.

        Args:
            item: Item que foi alterado
        """
        self._validate_selection()

    def _validate_selection(self) -> None:
        """Valida se a seleção atual cria ciclos de dependências."""
        # Obter seleção atual
        selected_ids = self._get_selected_dependencies()

        # Criar dicionário de dependências para o CycleDetector
        dependencies_map = {}
        for story_dto in self._all_stories:
            # Se for a história atual, usar dependências selecionadas
            if story_dto.id == self._current_story.id:
                dependencies_map[story_dto.id] = list(selected_ids)
            else:
                dependencies_map[story_dto.id] = list(story_dto.dependencies)

        # Verificar ciclos
        has_cycle = self._cycle_detector.has_cycle(dependencies_map)

        if has_cycle:
            # Mostrar erro e desabilitar OK
            self._error_label.setText(
                "⚠️ ERRO: A seleção atual cria um ciclo de dependências! "
                "Remova algumas dependências para resolver."
            )
            self._error_label.show()
            self._info_label.hide()
            self._ok_button.setEnabled(False)

            # Destacar itens que causam problema (todos os selecionados)
            for i in range(self._list_widget.count()):
                item = self._list_widget.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    item.setBackground(Qt.GlobalColor.red)
                    item.setForeground(Qt.GlobalColor.white)
                else:
                    item.setBackground(Qt.GlobalColor.transparent)
                    item.setForeground(Qt.GlobalColor.black)

        else:
            # Limpar erro e habilitar OK
            self._error_label.hide()
            self._ok_button.setEnabled(True)

            # Remover destaques
            for i in range(self._list_widget.count()):
                item = self._list_widget.item(i)
                item.setBackground(Qt.GlobalColor.transparent)
                item.setForeground(Qt.GlobalColor.black)

            # Mostrar informação se houver dependências
            if selected_ids:
                self._info_label.setText(
                    f"✓ {len(selected_ids)} dependência(s) selecionada(s). "
                    "Nenhum ciclo detectado."
                )
                self._info_label.show()
            else:
                self._info_label.hide()

    def _get_selected_dependencies(self) -> Set[str]:
        """
        Obtém conjunto de IDs das dependências selecionadas.

        Returns:
            Conjunto de IDs selecionados
        """
        selected = set()
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                story_id = item.data(Qt.ItemDataRole.UserRole)
                selected.add(story_id)
        return selected

    def get_dependencies(self) -> List[str]:
        """
        Retorna lista de dependências selecionadas.

        Returns:
            Lista de IDs das histórias selecionadas
        """
        return sorted(list(self._get_selected_dependencies()))
