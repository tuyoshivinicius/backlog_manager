"""Worker thread para alocação de desenvolvedores."""
from PySide6.QtCore import QThread, Signal

from backlog_manager.application.use_cases.schedule.allocate_developers import (
    AllocateDevelopersUseCase,
)


class AllocationWorker(QThread):
    """
    Worker thread para executar alocação de desenvolvedores em background.

    Emite signals quando completa ou encontra erro.
    """

    # Signals para comunicação thread-safe
    finished = Signal(int, list)  # (allocated_count, warnings: List[AllocationWarning])
    error = Signal(str)  # (error_message)

    def __init__(self, allocate_use_case: AllocateDevelopersUseCase):
        """
        Inicializa worker.

        Args:
            allocate_use_case: Caso de uso de alocação (injetado)
        """
        super().__init__()
        self._use_case = allocate_use_case

    def run(self) -> None:
        """
        Executa alocação em thread separada.

        Emite 'finished' com resultados ou 'error' em caso de exceção.
        """
        try:
            # Executar alocação (pode demorar)
            # Retorna (total, warnings, metrics) - métricas já são logadas pelo use case
            allocated_count, warnings, _metrics = self._use_case.execute()

            # Sucesso - emitir resultado
            self.finished.emit(allocated_count, warnings)

        except Exception as e:
            # Erro - emitir mensagem
            self.error.emit(str(e))
