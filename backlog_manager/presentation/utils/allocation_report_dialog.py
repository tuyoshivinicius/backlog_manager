"""Dialog para mostrar relatório de alocação."""
from typing import List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QWidget
)
from PySide6.QtCore import Qt
from backlog_manager.domain.services.idleness_detector import IdlenessWarning


class AllocationReportDialog(QDialog):
    """
    Dialog para exibir relatório de alocação de desenvolvedores.

    Mostra warnings de ociosidade detectados.
    """

    def __init__(self, parent: QWidget, allocated_count: int, warnings: List[IdlenessWarning]):
        """
        Inicializa dialog.

        Args:
            parent: Widget pai
            allocated_count: Número de histórias alocadas
            warnings: Lista de warnings de ociosidade
        """
        super().__init__(parent)
        self.setWindowTitle("Relatório de Alocação")
        self.setModal(True)
        self.setMinimumSize(600, 400)

        self._warnings = warnings
        self._allocated_count = allocated_count

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura interface."""
        layout = QVBoxLayout(self)

        # Título
        title = QLabel(f"✓ {self._allocated_count} história(s) alocada(s) com sucesso!")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: green;")
        layout.addWidget(title)

        # Warnings (se houver)
        if self._warnings:
            warning_label = QLabel(
                f"⚠️ {len(self._warnings)} aviso(s) de ociosidade detectado(s):"
            )
            warning_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: orange;")
            layout.addWidget(warning_label)

            # Text edit com warnings
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)

            warning_text = "\n\n".join([
                f"• {warning}" for warning in self._warnings
            ])
            text_edit.setPlainText(warning_text)

            layout.addWidget(text_edit)
        else:
            success_label = QLabel("✓ Nenhum gap de ociosidade detectado!")
            success_label.setStyleSheet("font-size: 11pt; color: green;")
            layout.addWidget(success_label)

        # Botão OK
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignRight)
