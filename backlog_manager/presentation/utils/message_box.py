"""
Sistema centralizado de mensagens para a aplicação.

Fornece métodos estáticos para exibir mensagens de sucesso, erro,
aviso e confirmação de forma consistente.
"""
from typing import Optional
from PySide6.QtWidgets import QMessageBox, QWidget


class MessageBox:
    """Sistema centralizado de mensagens."""

    @staticmethod
    def success(parent: Optional[QWidget], title: str, message: str) -> None:
        """
        Exibe mensagem de sucesso.

        Args:
            parent: Widget pai
            title: Título da mensagem
            message: Conteúdo da mensagem
        """
        QMessageBox.information(parent, title, message)

    @staticmethod
    def error(parent: Optional[QWidget], title: str, message: str) -> None:
        """
        Exibe mensagem de erro.

        Args:
            parent: Widget pai
            title: Título da mensagem
            message: Conteúdo da mensagem
        """
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def warning(parent: Optional[QWidget], title: str, message: str) -> None:
        """
        Exibe mensagem de aviso.

        Args:
            parent: Widget pai
            title: Título da mensagem
            message: Conteúdo da mensagem
        """
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def info(parent: Optional[QWidget], title: str, message: str) -> None:
        """
        Exibe mensagem informativa.

        Args:
            parent: Widget pai
            title: Título da mensagem
            message: Conteúdo da mensagem
        """
        QMessageBox.information(parent, title, message)

    @staticmethod
    def confirm(
        parent: Optional[QWidget], title: str, message: str
    ) -> bool:
        """
        Exibe diálogo de confirmação.

        Args:
            parent: Widget pai
            title: Título da confirmação
            message: Mensagem de confirmação

        Returns:
            True se usuário confirmou, False caso contrário
        """
        result = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,  # Padrão
        )
        return result == QMessageBox.StandardButton.Yes

    @staticmethod
    def confirm_delete(parent: Optional[QWidget], item_name: str) -> bool:
        """
        Confirmação específica para deleção.

        Args:
            parent: Widget pai
            item_name: Nome do item a ser deletado

        Returns:
            True se usuário confirmou a deleção
        """
        return MessageBox.confirm(
            parent,
            "Confirmar Deleção",
            f"Tem certeza que deseja deletar '{item_name}'?\n\n"
            "Esta ação não pode ser desfeita.",
        )
