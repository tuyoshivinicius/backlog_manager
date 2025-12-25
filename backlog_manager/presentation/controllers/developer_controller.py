"""
Controlador de operações de desenvolvedores.

Orquestra a comunicação entre views e use cases relacionados a desenvolvedores.
"""
import logging
from typing import Optional, List
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

from backlog_manager.application.use_cases.developer.create_developer import (
    CreateDeveloperUseCase,
)
from backlog_manager.application.use_cases.developer.update_developer import (
    UpdateDeveloperUseCase,
)
from backlog_manager.application.use_cases.developer.delete_developer import (
    DeleteDeveloperUseCase,
)
from backlog_manager.application.use_cases.developer.get_developer import (
    GetDeveloperUseCase,
)
from backlog_manager.application.use_cases.developer.list_developers import (
    ListDevelopersUseCase,
)
from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.presentation.utils.message_box import MessageBox


class DeveloperController:
    """Controlador de desenvolvedores."""

    def __init__(
        self,
        create_developer_use_case: CreateDeveloperUseCase,
        update_developer_use_case: UpdateDeveloperUseCase,
        delete_developer_use_case: DeleteDeveloperUseCase,
        get_developer_use_case: GetDeveloperUseCase,
        list_developers_use_case: ListDevelopersUseCase,
    ):
        """
        Inicializa o controlador.

        Args:
            create_developer_use_case: Use case de criação
            update_developer_use_case: Use case de atualização
            delete_developer_use_case: Use case de deleção
            get_developer_use_case: Use case de obtenção
            list_developers_use_case: Use case de listagem
        """
        self._create_use_case = create_developer_use_case
        self._update_use_case = update_developer_use_case
        self._delete_use_case = delete_developer_use_case
        self._get_use_case = get_developer_use_case
        self._list_use_case = list_developers_use_case

        self._parent_widget: Optional[QWidget] = None
        self._refresh_callback: Optional[callable] = None

    def set_parent_widget(self, widget: QWidget) -> None:
        """
        Define o widget pai para dialogs.

        Args:
            widget: Widget pai
        """
        self._parent_widget = widget

    def set_refresh_callback(self, callback: callable) -> None:
        """
        Define callback para atualizar a view.

        Args:
            callback: Função a chamar para atualizar
        """
        self._refresh_callback = callback

    def create_developer(self, name: str) -> None:
        """
        Cria um novo desenvolvedor.

        Args:
            name: Nome do desenvolvedor
        """
        try:
            developer = self._create_use_case.execute(name)
            MessageBox.success(
                self._parent_widget,
                "Sucesso",
                f"Desenvolvedor '{developer.name}' criado com ID: {developer.id}",
            )
            self._refresh_view()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Criar Desenvolvedor", str(e)
            )

    def update_developer(self, dev_id: str, name: str) -> None:
        """
        Atualiza um desenvolvedor existente.

        Args:
            dev_id: ID do desenvolvedor
            name: Novo nome
        """
        try:
            self._update_use_case.execute(dev_id, name)
            MessageBox.success(
                self._parent_widget,
                "Sucesso",
                "Desenvolvedor atualizado com sucesso!",
            )
            self._refresh_view()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Atualizar Desenvolvedor", str(e)
            )

    def delete_developer(self, dev_id: str) -> None:
        """
        Deleta um desenvolvedor.

        Args:
            dev_id: ID do desenvolvedor a deletar
        """
        try:
            # Obter desenvolvedor para confirmar
            developer = self._get_use_case.execute(dev_id)

            # Confirmar deleção
            if not MessageBox.confirm_delete(self._parent_widget, developer.name):
                return

            # Deletar
            self._delete_use_case.execute(dev_id)
            MessageBox.success(
                self._parent_widget,
                "Sucesso",
                "Desenvolvedor deletado com sucesso!",
            )
            self._refresh_view()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Deletar Desenvolvedor", str(e)
            )

    def get_developer(self, dev_id: str) -> Optional[DeveloperDTO]:
        """
        Obtém um desenvolvedor pelo ID.

        Args:
            dev_id: ID do desenvolvedor

        Returns:
            Desenvolvedor ou None se não encontrado
        """
        try:
            return self._get_use_case.execute(dev_id)
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Obter Desenvolvedor", str(e)
            )
            return None

    def list_developers(self) -> List[DeveloperDTO]:
        """
        Lista todos os desenvolvedores.

        Returns:
            Lista de desenvolvedores
        """
        try:
            return self._list_use_case.execute()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Listar Desenvolvedores", str(e)
            )
            return []

    def _refresh_view(self) -> None:
        """Atualiza a view."""
        if self._refresh_callback:
            self._refresh_callback()
