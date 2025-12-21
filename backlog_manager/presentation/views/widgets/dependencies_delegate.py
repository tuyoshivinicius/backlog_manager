"""
Delegate para edição de dependências em células da tabela.

Abre dialog de seleção de dependências ao invés de editor de texto simples.
"""
from typing import List
from PySide6.QtWidgets import QStyledItemDelegate, QWidget
from PySide6.QtCore import Qt, QModelIndex

from backlog_manager.application.dto.story_dto import StoryDTO


class DependenciesDelegate(QStyledItemDelegate):
    """Delegate para edição de dependências."""

    def __init__(self, parent=None):
        """
        Inicializa o delegate.

        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self._all_stories: List[StoryDTO] = []

    def set_stories(self, stories: List[StoryDTO]) -> None:
        """
        Define lista de histórias disponíveis.

        Args:
            stories: Lista de todas as histórias
        """
        self._all_stories = stories

    def createEditor(
        self, parent: QWidget, option, index: QModelIndex
    ) -> QWidget:
        """
        Cria editor customizado (dialog) para a célula.

        Abre dialog imediatamente ao invés de criar editor inline.

        Args:
            parent: Widget pai
            option: Opções de estilo
            index: Índice da célula

        Returns:
            None - não usamos editor inline
        """
        from backlog_manager.presentation.views.dependencies_dialog import (
            DependenciesDialog,
        )

        # Obter tabela (parent do delegate)
        table = self.parent()
        if not table:
            return None

        # Obter ID da história da linha atual
        row = index.row()
        id_item = table.item(row, 1)  # COL_ID = 1
        if not id_item:
            return None

        current_story_id = id_item.text()

        # Encontrar StoryDTO correspondente
        current_story = next(
            (s for s in self._all_stories if s.id == current_story_id), None
        )
        if not current_story:
            return None

        # Obter dependências atuais da célula
        deps_text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        current_dependencies = [
            dep.strip() for dep in deps_text.split(",") if dep.strip()
        ]

        # Abrir dialog
        dialog = DependenciesDialog(
            table, current_story, self._all_stories, current_dependencies
        )

        if dialog.exec():
            # Usuário confirmou - obter novas dependências
            new_dependencies = dialog.get_dependencies()

            # Atualizar célula
            deps_text = ", ".join(new_dependencies)

            # Obter item da célula e atualizar diretamente
            deps_item = table.item(row, index.column())
            if deps_item:
                deps_item.setText(deps_text)

        # Retornar None - não criamos editor inline
        return None
