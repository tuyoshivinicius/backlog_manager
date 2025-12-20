"""
Controlador de operações de cronograma.

Orquestra operações relacionadas a cálculo de cronograma e alocação.
"""
from typing import Optional
from PySide6.QtWidgets import QWidget

from backlog_manager.application.use_cases.schedule.calculate_schedule import (
    CalculateScheduleUseCase,
)
from backlog_manager.application.use_cases.schedule.allocate_developers import (
    AllocateDevelopersUseCase,
)
from backlog_manager.presentation.utils.message_box import MessageBox


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
            MessageBox.error(
                self._parent_widget, "Erro ao Calcular Cronograma", str(e)
            )

    def allocate_developers(self) -> None:
        """Aloca desenvolvedores automaticamente."""
        try:
            count = self._allocate_use_case.execute()
            MessageBox.success(
                self._parent_widget,
                "Sucesso",
                f"{count} histórias alocadas automaticamente!",
            )
            self._refresh_view()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Alocar Desenvolvedores", str(e)
            )

    def _refresh_view(self) -> None:
        """Atualiza a view."""
        if self._refresh_callback:
            self._refresh_callback()
