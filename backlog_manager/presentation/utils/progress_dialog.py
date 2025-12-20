"""
Dialog de progresso para operações longas.

Exibe uma barra de progresso indeterminada enquanto uma operação
está sendo executada.
"""
from typing import Optional
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PySide6.QtCore import Qt


class ProgressDialog(QDialog):
    """Dialog de progresso para operações longas."""

    def __init__(
        self,
        parent: Optional[QDialog],
        title: str = "Processando...",
        message: str = "Por favor, aguarde...",
        cancelable: bool = False,
    ):
        """
        Inicializa o dialog de progresso.

        Args:
            parent: Widget pai
            title: Título do dialog
            message: Mensagem a exibir
            cancelable: Se True, permite cancelar a operação
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        # Layout principal
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Label de mensagem
        self._message_label = QLabel(message)
        self._message_label.setWordWrap(True)
        layout.addWidget(self._message_label)

        # Barra de progresso indeterminada
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminado
        self._progress_bar.setTextVisible(False)
        layout.addWidget(self._progress_bar)

        # Botão cancelar (opcional)
        if cancelable:
            cancel_button = QPushButton("Cancelar")
            cancel_button.clicked.connect(self.reject)
            layout.addWidget(cancel_button)

        self.setLayout(layout)

    def update_message(self, message: str) -> None:
        """
        Atualiza a mensagem exibida.

        Args:
            message: Nova mensagem
        """
        self._message_label.setText(message)
