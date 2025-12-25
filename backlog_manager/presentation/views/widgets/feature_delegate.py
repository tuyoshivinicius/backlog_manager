"""
Delegate para edição de Feature com dropdown.

Fornece um combobox com lista de features disponíveis organizadas por onda.
"""
from typing import List
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QWidget
from PySide6.QtCore import QModelIndex, Qt

from backlog_manager.application.dto.feature_dto import FeatureDTO


class FeatureDelegate(QStyledItemDelegate):
    """
    Delegate para edição de Feature.

    Usa QComboBox com lista de features cadastradas.
    Permite selecionar feature ou remover com "(Nenhuma)".
    """

    def __init__(self, parent=None):
        """
        Inicializa o delegate.

        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self._features: List[FeatureDTO] = []

    def set_features(self, features: List[FeatureDTO]) -> None:
        """
        Define lista de features disponíveis.

        Args:
            features: Lista de features
        """
        self._features = features

    def createEditor(
        self, parent: QWidget, option, index: QModelIndex
    ) -> QComboBox:
        """
        Cria combobox para selecionar feature.

        Args:
            parent: Widget pai
            option: Opções de estilo
            index: Índice do modelo

        Returns:
            ComboBox com features
        """
        editor = QComboBox(parent)

        # Adicionar opção "(Nenhuma)"
        editor.addItem("(Nenhuma)", None)

        # Ordenar features por onda
        sorted_features = sorted(self._features, key=lambda f: f.wave)

        # Adicionar features no formato "Onda X: Nome (ID: XXX)"
        for feature in sorted_features:
            display_text = f"Onda {feature.wave}: {feature.name} (ID: {feature.id})"
            editor.addItem(display_text, feature.id)

        return editor

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        """
        Preenche combobox com valor atual.

        Args:
            editor: ComboBox
            index: Índice do modelo
        """
        value = index.data(Qt.ItemDataRole.EditRole)

        # Encontrar índice correspondente pelo feature_id (UserRole)
        if value and value != "(Nenhuma)":
            for i in range(editor.count()):
                if editor.itemData(i, Qt.ItemDataRole.UserRole) == value:
                    editor.setCurrentIndex(i)
                    return

        # Se não encontrou ou é "(Nenhuma)", selecionar primeiro item
        editor.setCurrentIndex(0)

    def setModelData(
        self, editor: QComboBox, model, index: QModelIndex
    ) -> None:
        """
        Salva valor selecionado no modelo.

        Args:
            editor: ComboBox
            model: Modelo de dados da tabela
            index: Índice do modelo
        """
        selected_index = editor.currentIndex()
        feature_id = editor.itemData(selected_index, Qt.ItemDataRole.UserRole)

        if feature_id:
            model.setData(index, feature_id, Qt.ItemDataRole.EditRole)
        else:
            model.setData(index, "(Nenhuma)", Qt.ItemDataRole.EditRole)
