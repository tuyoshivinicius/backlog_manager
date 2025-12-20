"""
Gerenciador da barra de status.

Facilita a exibição de mensagens temporárias e permanentes
na barra de status da janela principal.
"""
from PySide6.QtWidgets import QStatusBar


class StatusBarManager:
    """Gerencia mensagens na barra de status."""

    def __init__(self, status_bar: QStatusBar):
        """
        Inicializa o gerenciador.

        Args:
            status_bar: Barra de status a gerenciar
        """
        self._status_bar = status_bar
        self._default_message = "Pronto"

    def show_message(self, message: str, timeout: int = 3000) -> None:
        """
        Exibe mensagem temporária.

        Args:
            message: Mensagem a exibir
            timeout: Tempo em ms antes de limpar (0 = permanente)
        """
        self._status_bar.showMessage(message, timeout)

    def show_permanent(self, message: str) -> None:
        """
        Exibe mensagem permanente.

        Args:
            message: Mensagem a exibir
        """
        self._status_bar.showMessage(message, 0)

    def show_loading(self, message: str = "Carregando...") -> None:
        """
        Exibe indicador de carregamento.

        Args:
            message: Mensagem de carregamento
        """
        self._status_bar.showMessage(f"⏳ {message}", 0)

    def show_recalculating(self) -> None:
        """Exibe indicador de recálculo de cronograma."""
        self.show_loading("Recalculando cronograma...")

    def clear(self) -> None:
        """Limpa a barra de status, mostrando mensagem padrão."""
        self._status_bar.showMessage(self._default_message)

    def show_story_count(self, count: int) -> None:
        """
        Exibe contagem de histórias.

        Args:
            count: Número de histórias
        """
        self.show_permanent(f"{count} história(s)")
