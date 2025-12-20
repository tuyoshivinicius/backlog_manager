"""
Delegate para edição de Desenvolvedor.

Fornece um combobox com lista de desenvolvedores disponíveis.
NOTA: Por enquanto permite edição por texto livre. Delegate dinâmico será
implementado após investigação completa do crash.
"""
from PySide6.QtWidgets import QStyledItemDelegate, QLineEdit, QWidget
from PySide6.QtCore import QModelIndex, Qt


class DeveloperDelegate(QStyledItemDelegate):
    """
    Delegate para edição de Desenvolvedor.

    VERSÃO SIMPLIFICADA: Usa QLineEdit em vez de QComboBox para evitar crashes.
    Usuário digita o ID do desenvolvedor diretamente.
    """

    def createEditor(
        self, parent: QWidget, option, index: QModelIndex
    ) -> QLineEdit:
        """
        Cria o editor (text field) para Desenvolvedor.

        Args:
            parent: Widget pai
            option: Opções de estilo
            index: Índice do modelo

        Returns:
            LineEdit para texto livre
        """
        editor = QLineEdit(parent)
        editor.setPlaceholderText("Digite o ID do desenvolvedor")
        return editor

    def setEditorData(self, editor: QLineEdit, index: QModelIndex) -> None:
        """
        Preenche o editor com o valor atual.

        Args:
            editor: Editor (line edit)
            index: Índice do modelo
        """
        value = index.data(Qt.ItemDataRole.EditRole)
        if value and value != "(Nenhum)":
            editor.setText(str(value))
        else:
            editor.setText("")

    def setModelData(
        self, editor: QLineEdit, model, index: QModelIndex
    ) -> None:
        """
        Salva o valor do editor de volta no modelo.

        Args:
            editor: Editor (line edit)
            model: Modelo de dados
            index: Índice do modelo
        """
        value = editor.text().strip()
        if value:
            model.setData(index, value, Qt.ItemDataRole.EditRole)
        else:
            model.setData(index, "(Nenhum)", Qt.ItemDataRole.EditRole)
