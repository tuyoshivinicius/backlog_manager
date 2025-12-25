"""
Controlador de operações de cronograma.

Orquestra operações relacionadas a cálculo de cronograma e alocação.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

from backlog_manager.application.use_cases.schedule.allocate_developers import (
    AllocateDevelopersUseCase,
)
from backlog_manager.application.use_cases.schedule.calculate_schedule import (
    CalculateScheduleUseCase,
)
from backlog_manager.presentation.utils.allocation_worker import AllocationWorker
from backlog_manager.presentation.utils.message_box import MessageBox
from backlog_manager.presentation.utils.progress_dialog import ProgressDialog


class ScheduleController:
    """Controlador de cronograma."""

    def __init__(
        self,
        calculate_schedule_use_case: CalculateScheduleUseCase,
        allocate_developers_use_case: AllocateDevelopersUseCase,
    ):
        """
        Inicializa o controlador.

        Args:
            calculate_schedule_use_case: Use case de cálculo
            allocate_developers_use_case: Use case de alocação
        """
        self._calculate_use_case = calculate_schedule_use_case
        self._allocate_use_case = allocate_developers_use_case

        self._parent_widget: Optional[QWidget] = None
        self._refresh_callback: Optional[callable] = None
        self._show_loading_callback: Optional[callable] = None
        self._hide_loading_callback: Optional[callable] = None

        # Threading support
        self._worker: Optional[AllocationWorker] = None
        self._progress_dialog: Optional[ProgressDialog] = None

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

    def set_loading_callbacks(self, show: callable, hide: callable) -> None:
        """
        Define callbacks de indicador de loading.

        Args:
            show: Callback para mostrar loading
            hide: Callback para esconder loading
        """
        self._show_loading_callback = show
        self._hide_loading_callback = hide

    def calculate_schedule(self) -> None:
        """Calcula o cronograma completo."""
        try:
            if self._show_loading_callback:
                self._show_loading_callback()

            self._calculate_use_case.execute()

            if self._hide_loading_callback:
                self._hide_loading_callback()

            MessageBox.success(
                self._parent_widget,
                "Sucesso",
                "Cronograma calculado com sucesso!",
            )
            self._refresh_view()
        except Exception as e:
            if self._hide_loading_callback:
                self._hide_loading_callback()
            MessageBox.error(self._parent_widget, "Erro ao Calcular Cronograma", str(e))

    def allocate_developers(self) -> None:
        """Aloca desenvolvedores automaticamente e mostra relatório."""
        # 1. Criar ProgressDialog (modal, spinner)
        self._progress_dialog = ProgressDialog(
            parent=self._parent_widget,
            title="Alocando Desenvolvedores",
            message="Calculando alocações e balanceamento de carga...",
            cancelable=False,  # Não permite cancelar (por enquanto)
        )

        # 2. Criar Worker (thread separada)
        self._worker = AllocationWorker(self._allocate_use_case)

        # 3. Conectar signals
        self._worker.finished.connect(self._on_allocation_finished)
        self._worker.error.connect(self._on_allocation_error)

        # 4. Garantir cleanup quando thread terminar
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.error.connect(self._worker.deleteLater)

        # 5. Iniciar worker (executa em background)
        self._worker.start()

        # 6. Mostrar dialog (modal - bloqueia input mas não trava UI)
        self._progress_dialog.exec()

    def _on_allocation_finished(self, allocated_count: int, warnings: list) -> None:
        """
        Callback quando alocação termina com sucesso.

        Args:
            allocated_count: Número de histórias alocadas
            warnings: Lista de avisos de ociosidade
        """
        # Fechar progress dialog
        if self._progress_dialog:
            self._progress_dialog.close()

        # Mostrar relatório com resultados
        from backlog_manager.presentation.utils.allocation_report_dialog import (
            AllocationReportDialog,
        )

        dialog = AllocationReportDialog(self._parent_widget, allocated_count, warnings)
        dialog.exec()

        # Atualizar view
        self._refresh_view()

    def _on_allocation_error(self, error_message: str) -> None:
        """
        Callback quando alocação falha.

        Args:
            error_message: Mensagem de erro
        """
        # Fechar progress dialog
        if self._progress_dialog:
            self._progress_dialog.close()

        # Mostrar erro
        MessageBox.error(self._parent_widget, "Erro ao Alocar Desenvolvedores", error_message)

    def _refresh_view(self) -> None:
        """Atualiza a view."""
        if self._refresh_callback:
            self._refresh_callback()
