"""
Tabela editável de backlog tipo Excel.

Permite visualização e edição inline de histórias com validações em tempo real.
"""
from typing import List, Optional
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMenu,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction, QColor

from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.presentation.styles.themes import StatusColors


class EditableTableWidget(QTableWidget):
    """Tabela editável tipo Excel para histórias do backlog."""

    # Sinais
    story_field_changed = Signal(str, str, object)  # story_id, field, new_value
    story_selected = Signal(str)  # story_id
    edit_story_requested = Signal(str)  # story_id
    duplicate_story_requested = Signal(str)  # story_id
    delete_story_requested = Signal(str)  # story_id
    manage_dependencies_requested = Signal(str)  # story_id

    # Stylesheets
    _STYLE_NORMAL = """
        QTableWidget::item:selected {
            background-color: palette(highlight);
            color: palette(highlighted-text);
            padding: 0px;
        }

        QTableWidget::item {
            padding: 0px;
            font-size: 11pt;
        }

        QTableWidget::branch {
            background: transparent;
            width: 0px;
        }

        QTableWidget {
            gridline-color: #d0d0d0;
        }
    """

    _STYLE_PRIORITY_CHANGE = """
        QTableWidget::item:selected {
            background-color: #FF5555;
            color: white;
            padding: 0px;
        }

        QTableWidget::item {
            padding: 0px;
            font-size: 11pt;
        }

        QTableWidget::branch {
            background: transparent;
            width: 0px;
        }

        QTableWidget {
            gridline-color: #d0d0d0;
        }
    """

    # Índices das colunas
    COL_PRIORITY = 0
    COL_ID = 1
    COL_FEATURE = 2
    COL_NAME = 3
    COL_STATUS = 4
    COL_DEVELOPER = 5
    COL_DEPENDENCIES = 6
    COL_STORY_POINT = 7
    COL_START_DATE = 8
    COL_END_DATE = 9
    COL_DURATION = 10

    # Mapeamento de índice para nome de campo
    COLUMN_TO_FIELD = {
        COL_FEATURE: "feature",
        COL_NAME: "name",
        COL_STATUS: "status",
        COL_DEVELOPER: "developer_id",
        COL_DEPENDENCIES: "dependencies",
        COL_STORY_POINT: "story_point",
    }

    def __init__(self):
        """Inicializa a tabela."""
        super().__init__()
        self._stories: List[StoryDTO] = []
        self._ctrl_feedback_active = False  # Flag para feedback de Ctrl
        self._priority_change_feedback_active = False  # Flag para feedback de mudança de prioridade
        self._setup_table()

    def _setup_table(self) -> None:
        """Configura propriedades da tabela."""
        # Configurações gerais
        self.setColumnCount(11)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.setSortingEnabled(False)

        # Aumentar altura das linhas para melhorar espaço de edição
        self.verticalHeader().setDefaultSectionSize(32)

        # Cabeçalhos
        headers = [
            "Prioridade",
            "ID",
            "Feature",
            "Nome",
            "Status",
            "Desenvolvedor",
            "Dependências",
            "SP",
            "Início",
            "Fim",
            "Duração",
        ]
        self.setHorizontalHeaderLabels(headers)

        # Configurar larguras de coluna
        self.setColumnWidth(self.COL_PRIORITY, 80)
        self.setColumnWidth(self.COL_ID, 60)
        self.setColumnWidth(self.COL_FEATURE, 120)
        self.setColumnWidth(self.COL_NAME, 250)
        self.setColumnWidth(self.COL_STATUS, 100)
        self.setColumnWidth(self.COL_DEVELOPER, 120)
        self.setColumnWidth(self.COL_DEPENDENCIES, 150)
        self.setColumnWidth(self.COL_STORY_POINT, 80)
        self.setColumnWidth(self.COL_START_DATE, 100)
        self.setColumnWidth(self.COL_END_DATE, 100)
        self.setColumnWidth(self.COL_DURATION, 80)

        # Política de redimensionamento
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)

        # Conectar sinais
        self.itemChanged.connect(self._on_item_changed)
        self.itemSelectionChanged.connect(self._on_selection_changed)

        # Menu de contexto
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Aplicar stylesheet padrão (remove padding-left indesejado)
        self.setStyleSheet(self._STYLE_NORMAL)

    def populate_from_stories(self, stories: List[StoryDTO]) -> None:
        """
        Popula a tabela com histórias.

        Args:
            stories: Lista de histórias para exibir
        """
        self._stories = stories
        self.setRowCount(len(stories))

        # Desconectar sinal temporariamente para evitar triggers
        self.itemChanged.disconnect(self._on_item_changed)

        for row, story in enumerate(stories):
            self._populate_row(row, story)

        # Reconectar sinal
        self.itemChanged.connect(self._on_item_changed)

    def _populate_row(self, row: int, story: StoryDTO) -> None:
        """
        Popula uma linha da tabela com dados de uma história.

        Args:
            row: Índice da linha
            story: Dados da história
        """
        # Prioridade (read-only)
        priority_item = QTableWidgetItem(str(story.priority))
        priority_item.setFlags(priority_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, self.COL_PRIORITY, priority_item)

        # ID (read-only)
        id_item = QTableWidgetItem(story.id)
        id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, self.COL_ID, id_item)

        # Feature (editável)
        self.setItem(row, self.COL_FEATURE, QTableWidgetItem(story.feature))

        # Nome (editável)
        self.setItem(row, self.COL_NAME, QTableWidgetItem(story.name))

        # Status (editável com cores)
        status_item = QTableWidgetItem(story.status)
        self._apply_status_color(status_item, story.status)
        self.setItem(row, self.COL_STATUS, status_item)

        # Desenvolvedor (editável)
        dev_text = story.developer_id if story.developer_id else "(Nenhum)"
        self.setItem(row, self.COL_DEVELOPER, QTableWidgetItem(dev_text))

        # Dependências (editável)
        deps_text = ", ".join(story.dependencies) if story.dependencies else ""
        self.setItem(row, self.COL_DEPENDENCIES, QTableWidgetItem(deps_text))

        # Story Point (editável)
        self.setItem(row, self.COL_STORY_POINT, QTableWidgetItem(str(story.story_point)))

        # Data Início (read-only, calculado)
        start_text = story.start_date.strftime("%d/%m/%Y") if story.start_date else ""
        start_item = QTableWidgetItem(start_text)
        start_item.setFlags(start_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, self.COL_START_DATE, start_item)

        # Data Fim (read-only, calculado)
        end_text = story.end_date.strftime("%d/%m/%Y") if story.end_date else ""
        end_item = QTableWidgetItem(end_text)
        end_item.setFlags(end_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, self.COL_END_DATE, end_item)

        # Duração (read-only, calculado)
        duration_text = f"{story.duration} dias" if story.duration else ""
        duration_item = QTableWidgetItem(duration_text)
        duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, self.COL_DURATION, duration_item)

    def _apply_status_color(self, item: QTableWidgetItem, status: str) -> None:
        """
        Aplica cor de fundo baseada no status.

        Args:
            item: Item da tabela
            status: Status da história
        """
        color_hex = StatusColors.get_color(status)
        color = QColor(color_hex)
        color.setAlpha(50)  # Transparência
        item.setBackground(color)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        """
        Callback quando um item é alterado.

        Args:
            item: Item que foi alterado
        """
        row = item.row()
        col = item.column()

        # Verificar se é uma coluna editável
        if col not in self.COLUMN_TO_FIELD:
            return

        # Obter story_id
        id_item = self.item(row, self.COL_ID)
        if not id_item:
            return
        story_id = id_item.text()

        # Obter nome do campo
        field_name = self.COLUMN_TO_FIELD[col]

        # Obter novo valor
        new_value = item.text()

        # Converter valor se necessário
        if field_name == "story_point":
            try:
                new_value = int(new_value)
            except ValueError:
                return

        # Emitir sinal
        self.story_field_changed.emit(story_id, field_name, new_value)

    def _on_selection_changed(self) -> None:
        """Callback quando seleção muda."""
        selected_items = self.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            id_item = self.item(row, self.COL_ID)
            if id_item:
                self.story_selected.emit(id_item.text())

    def _show_context_menu(self, position) -> None:
        """
        Exibe menu de contexto (clique direito).

        Args:
            position: Posição do clique
        """
        # Verificar se há linha selecionada
        row = self.rowAt(position.y())
        if row < 0:
            return

        id_item = self.item(row, self.COL_ID)
        if not id_item:
            return

        story_id = id_item.text()

        # Criar menu
        menu = QMenu(self)

        edit_action = QAction("Editar História", self)
        edit_action.triggered.connect(lambda: self.edit_story_requested.emit(story_id))
        menu.addAction(edit_action)

        duplicate_action = QAction("Duplicar História", self)
        duplicate_action.triggered.connect(
            lambda: self.duplicate_story_requested.emit(story_id)
        )
        menu.addAction(duplicate_action)

        delete_action = QAction("Deletar História", self)
        delete_action.triggered.connect(
            lambda: self.delete_story_requested.emit(story_id)
        )
        menu.addAction(delete_action)

        menu.addSeparator()

        # Ações de dependências
        manage_deps_action = QAction("Gerenciar Dependências...", self)
        manage_deps_action.triggered.connect(
            lambda: self.manage_dependencies_requested.emit(story_id)
        )
        menu.addAction(manage_deps_action)

        # Exibir menu na posição do cursor
        menu.exec(self.mapToGlobal(position))

    def get_selected_story_id(self) -> Optional[str]:
        """
        Retorna o ID da história selecionada.

        Returns:
            ID da história ou None se nenhuma selecionada
        """
        selected_items = self.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        id_item = self.item(row, self.COL_ID)
        return id_item.text() if id_item else None

    def select_story_by_id(self, story_id: str) -> bool:
        """
        Seleciona a linha da tabela que contém a história especificada.

        Args:
            story_id: ID da história a selecionar

        Returns:
            True se encontrou e selecionou, False caso contrário
        """
        for row in range(self.rowCount()):
            id_item = self.item(row, self.COL_ID)
            if id_item and id_item.text() == story_id:
                # Limpar seleção atual
                self.clearSelection()
                # Selecionar a linha
                self.selectRow(row)
                # Scroll para garantir visibilidade
                self.scrollToItem(id_item, QAbstractItemView.ScrollHint.PositionAtCenter)
                return True
        return False

    def apply_priority_change_feedback(self, active: bool, source: str = "priority") -> None:
        """
        Aplica ou remove feedback visual.

        Args:
            active: True para ativar feedback (vermelho), False para remover
            source: "priority" ou "ctrl" - fonte do feedback
        """
        if source == "priority":
            self._priority_change_feedback_active = active
        elif source == "ctrl":
            self._ctrl_feedback_active = active

        # Aplicar vermelho se QUALQUER feedback está ativo
        should_be_red = self._priority_change_feedback_active or self._ctrl_feedback_active
        self.setStyleSheet(self._STYLE_PRIORITY_CHANGE if should_be_red else self._STYLE_NORMAL)

    def keyPressEvent(self, event) -> None:
        """
        Captura eventos de tecla pressionada.

        Args:
            event: Evento de tecla
        """
        # Detectar Ctrl pressionado
        if event.key() == Qt.Key.Key_Control:
            self.apply_priority_change_feedback(True, source="ctrl")

        # Chamar implementação padrão
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:
        """
        Captura eventos de tecla solta.

        Args:
            event: Evento de tecla
        """
        # Detectar Ctrl solto
        if event.key() == Qt.Key.Key_Control:
            self.apply_priority_change_feedback(False, source="ctrl")

        # Chamar implementação padrão
        super().keyReleaseEvent(event)

    def refresh(self) -> None:
        """Atualiza a tabela (força repaint)."""
        self.viewport().update()
