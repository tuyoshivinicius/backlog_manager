"""
Delegate para edição de Desenvolvedor com dropdown.

Fornece um combobox com lista de desenvolvedores disponíveis.
Indica visualmente quais desenvolvedores estão disponíveis (verde) ou indisponíveis (vermelho).
"""
from typing import List, Optional
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QWidget
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor

from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.application.use_cases.story.validate_developer_allocation import (
    ValidateDeveloperAllocationUseCase
)
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository


class DeveloperDelegate(QStyledItemDelegate):
    """
    Delegate para edição de Desenvolvedor.

    Usa QComboBox com lista de desenvolvedores cadastrados.
    Permite selecionar desenvolvedor ou remover alocação com "(Nenhum)".
    """

    def __init__(
        self,
        validate_allocation_use_case: ValidateDeveloperAllocationUseCase,
        story_repository: StoryRepository,
        parent=None
    ):
        """
        Inicializa o delegate.

        Args:
            validate_allocation_use_case: Use case de validação de alocação
            story_repository: Repositório de histórias
            parent: Widget pai
        """
        super().__init__(parent)
        self._developers: List[DeveloperDTO] = []
        self._validate_allocation_use_case = validate_allocation_use_case
        self._story_repository = story_repository

    def set_developers(self, developers: List[DeveloperDTO]) -> None:
        """
        Define lista de desenvolvedores disponíveis.

        Args:
            developers: Lista de desenvolvedores
        """
        self._developers = developers

    def createEditor(
        self, parent: QWidget, option, index: QModelIndex
    ) -> QComboBox:
        """
        Cria combobox para selecionar desenvolvedor com cores de disponibilidade.

        Desenvolvedores disponíveis (sem conflito) = fundo verde
        Desenvolvedores indisponíveis (com conflito) = fundo vermelho

        Args:
            parent: Widget pai
            option: Opções de estilo
            index: Índice do modelo

        Returns:
            ComboBox com desenvolvedores coloridos
        """
        editor = QComboBox(parent)

        # Criar modelo customizado para permitir cores
        model = QStandardItemModel()

        # Adicionar opção "(Nenhum)" sem cor
        none_item = QStandardItem("(Nenhum)")
        none_item.setData(None, Qt.ItemDataRole.UserRole)
        model.appendRow(none_item)

        # Obter ID da história atual
        story_id = self._get_story_id_from_index(index)

        if not story_id:
            # Se não conseguir obter ID, adicionar todos sem cor
            for dev in self._developers:
                item = QStandardItem(f"{dev.name} ({dev.id})")
                item.setData(dev.id, Qt.ItemDataRole.UserRole)
                model.appendRow(item)
        else:
            # Buscar história para obter datas
            story = self._story_repository.find_by_id(story_id)

            # Adicionar desenvolvedores com cores
            for dev in self._developers:
                item = QStandardItem(f"{dev.name} ({dev.id})")
                item.setData(dev.id, Qt.ItemDataRole.UserRole)

                # Validar se desenvolvedor pode ser alocado
                is_available = self._check_developer_availability(
                    dev.id, story_id, story
                )

                # Aplicar cor de fundo
                if is_available:
                    item.setBackground(QColor("#c8e6c9"))  # Verde claro
                else:
                    item.setBackground(QColor("#ffcdd2"))  # Vermelho claro

                model.appendRow(item)

        editor.setModel(model)
        return editor

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        """
        Preenche combobox com valor atual.

        Args:
            editor: ComboBox
            index: Índice do modelo
        """
        value = index.data(Qt.ItemDataRole.EditRole)
        model = editor.model()

        # Encontrar índice correspondente no modelo customizado
        if value and value != "(Nenhum)" and isinstance(model, QStandardItemModel):
            for i in range(model.rowCount()):
                item = model.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == value:
                    editor.setCurrentIndex(i)
                    return

        # Se não encontrou ou é "(Nenhum)", selecionar primeiro item
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
        # Obter item selecionado do modelo customizado do combobox
        combo_model = editor.model()
        selected_index = editor.currentIndex()

        if selected_index >= 0 and isinstance(combo_model, QStandardItemModel):
            item = combo_model.item(selected_index)
            if item:
                selected_id = item.data(Qt.ItemDataRole.UserRole)

                if selected_id:
                    model.setData(index, selected_id, Qt.ItemDataRole.EditRole)
                else:
                    model.setData(index, "(Nenhum)", Qt.ItemDataRole.EditRole)

    def _get_story_id_from_index(self, index: QModelIndex) -> Optional[str]:
        """
        Obtém ID da história a partir do índice da tabela.

        Args:
            index: Índice do modelo (célula da coluna Desenvolvedor)

        Returns:
            ID da história ou None se não encontrado
        """
        # A coluna 1 (COL_ID) contém o ID da história
        # Obtém a célula da coluna ID na mesma linha
        id_index = index.siblingAtColumn(1)  # COL_ID = 1
        story_id = id_index.data(Qt.ItemDataRole.DisplayRole)

        return story_id if story_id else None

    def _check_developer_availability(
        self,
        developer_id: str,
        story_id: str,
        story
    ) -> bool:
        """
        Verifica se desenvolvedor está disponível para alocação.

        Um desenvolvedor está disponível se não há conflito de período
        com outras histórias já alocadas a ele.

        Args:
            developer_id: ID do desenvolvedor
            story_id: ID da história
            story: Entidade Story (pode ser None)

        Returns:
            True se disponível (sem conflito), False caso contrário
        """
        # Se história não existe ou não tem datas, sempre disponível
        if not story or not story.start_date or not story.end_date:
            return True

        # Validar alocação usando o use case
        is_valid, conflicts = self._validate_allocation_use_case.execute(
            story_id=story_id,
            developer_id=developer_id
        )

        return is_valid
