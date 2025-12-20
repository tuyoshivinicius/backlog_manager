"""
Delegate para edição de Status.

Fornece um combobox com valores válidos de status.
"""
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QWidget
from PySide6.QtCore import QModelIndex, Qt

from backlog_manager.domain.value_objects.story_status import StoryStatus


class StatusDelegate(QStyledItemDelegate):
    """Delegate para edição de Status - SEGUINDO PADRÃO DO StoryPointDelegate."""

    VALID_VALUES = ["BACKLOG", "EXECUÇÃO", "TESTES", "CONCLUÍDO", "IMPEDIDO"]

    def createEditor(
        self, parent: QWidget, option, index: QModelIndex
    ) -> QComboBox:
        """
        Cria o editor (combobox) para Status.

        Args:
            parent: Widget pai
            option: Opções de estilo
            index: Índice do modelo

        Returns:
            ComboBox com valores válidos
        """
        combo = QComboBox(parent)
        combo.addItems(self.VALID_VALUES)
        return combo

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        """
        Preenche o editor com o valor atual.

        Args:
            editor: Editor (combobox)
            index: Índice do modelo
        """
        value = index.data(Qt.ItemDataRole.EditRole)
        if value:
            idx = editor.findText(str(value))
            if idx >= 0:
                editor.setCurrentIndex(idx)
            else:
                editor.setCurrentIndex(0)

    def setModelData(
        self, editor: QComboBox, model, index: QModelIndex
    ) -> None:
        """
        Salva o valor do editor de volta no modelo.

        Args:
            editor: Editor (combobox)
            model: Modelo de dados
            index: Índice do modelo
        """
        value = editor.currentText()
        model.setData(index, value, Qt.ItemDataRole.EditRole)
