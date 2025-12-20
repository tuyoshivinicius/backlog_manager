"""
Delegate para edição de Story Points.

Fornece um combobox com valores válidos (3, 5, 8, 13).
"""
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QWidget
from PySide6.QtCore import QModelIndex, Qt


class StoryPointDelegate(QStyledItemDelegate):
    """Delegate para edição de Story Points."""

    VALID_VALUES = [3, 5, 8, 13]

    def createEditor(
        self, parent: QWidget, option, index: QModelIndex
    ) -> QComboBox:
        """
        Cria o editor (combobox) para Story Points.

        Args:
            parent: Widget pai
            option: Opções de estilo
            index: Índice do modelo

        Returns:
            ComboBox com valores válidos
        """
        combo = QComboBox(parent)
        combo.addItems([str(val) for val in self.VALID_VALUES])
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
            try:
                current_value = str(int(value))
                idx = editor.findText(current_value)
                if idx >= 0:
                    editor.setCurrentIndex(idx)
            except (ValueError, TypeError):
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
