"""
Controlador principal da aplicação.

Coordena todos os sub-controllers e gerencia a janela principal.
"""
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QFileDialog

from backlog_manager.application.use_cases.excel.import_from_excel import (
    ImportFromExcelUseCase,
)
from backlog_manager.application.use_cases.excel.export_to_excel import (
    ExportToExcelUseCase,
)
from backlog_manager.application.use_cases.configuration.get_configuration import (
    GetConfigurationUseCase,
)
from backlog_manager.application.use_cases.configuration.update_configuration import (
    UpdateConfigurationUseCase,
)
from backlog_manager.presentation.views.main_window import MainWindow
from backlog_manager.presentation.views.widgets.editable_table import (
    EditableTableWidget,
)
from backlog_manager.presentation.views.widgets.story_point_delegate import (
    StoryPointDelegate,
)
from backlog_manager.presentation.views.widgets.status_delegate import StatusDelegate
from backlog_manager.presentation.views.widgets.developer_delegate import (
    DeveloperDelegate,
)
from backlog_manager.presentation.views.story_form import StoryFormDialog
from backlog_manager.presentation.views.developer_form import DeveloperFormDialog
from backlog_manager.presentation.views.configuration_dialog import (
    ConfigurationDialog,
)
from backlog_manager.presentation.controllers.story_controller import StoryController
from backlog_manager.presentation.controllers.developer_controller import (
    DeveloperController,
)
from backlog_manager.presentation.controllers.schedule_controller import (
    ScheduleController,
)
from backlog_manager.presentation.utils.message_box import MessageBox
from backlog_manager.presentation.utils.progress_dialog import ProgressDialog


class MainController:
    """Controlador principal da aplicação."""

    def __init__(
        self,
        story_controller: StoryController,
        developer_controller: DeveloperController,
        schedule_controller: ScheduleController,
        import_excel_use_case: ImportFromExcelUseCase,
        export_excel_use_case: ExportToExcelUseCase,
        get_configuration_use_case: GetConfigurationUseCase,
        update_configuration_use_case: UpdateConfigurationUseCase,
    ):
        """
        Inicializa o controlador principal.

        Args:
            story_controller: Controlador de histórias
            developer_controller: Controlador de desenvolvedores
            schedule_controller: Controlador de cronograma
            import_excel_use_case: Use case de importação Excel
            export_excel_use_case: Use case de exportação Excel
            get_configuration_use_case: Use case de obter configuração
            update_configuration_use_case: Use case de atualizar configuração
        """
        self._story_controller = story_controller
        self._developer_controller = developer_controller
        self._schedule_controller = schedule_controller
        self._import_use_case = import_excel_use_case
        self._export_use_case = export_excel_use_case
        self._get_config_use_case = get_configuration_use_case
        self._update_config_use_case = update_configuration_use_case

        self._main_window: Optional[MainWindow] = None
        self._table: Optional[EditableTableWidget] = None

        # Manter referências aos delegates para evitar garbage collection
        self._story_point_delegate = None
        self._status_delegate = None
        self._developer_delegate = None

    def initialize_ui(self) -> MainWindow:
        """
        Inicializa a interface gráfica.

        Returns:
            Janela principal
        """
        # Criar janela principal
        self._main_window = MainWindow()

        # Criar tabela
        self._table = EditableTableWidget()

        # Definir tabela como widget central
        self._main_window.set_central_widget(self._table)

        # Conectar sinais
        self._connect_signals()

        # Configurar controllers
        self._setup_controllers()

        # Carregar dados iniciais ANTES de configurar delegates
        self.refresh_backlog()

        # Configurar delegates APÓS popular tabela (pode ajudar com crashes)
        self._setup_delegates()

        return self._main_window

    def _setup_delegates(self) -> None:
        """Configura delegates da tabela APÓS popular com dados."""
        if not self._table:
            return

        # Story Point Delegate - FUNCIONA
        # IMPORTANTE: Armazenar referência como atributo para evitar GC
        self._story_point_delegate = StoryPointDelegate()
        self._table.setItemDelegateForColumn(
            EditableTableWidget.COL_STORY_POINT, self._story_point_delegate
        )

        # Status Delegate - Agora deve funcionar com ordem correta!
        self._status_delegate = StatusDelegate()
        self._table.setItemDelegateForColumn(
            EditableTableWidget.COL_STATUS, self._status_delegate
        )

        # Developer Delegate - Funciona com QLineEdit
        self._developer_delegate = DeveloperDelegate()
        self._table.setItemDelegateForColumn(
            EditableTableWidget.COL_DEVELOPER, self._developer_delegate
        )


    def _connect_signals(self) -> None:
        """Conecta sinais da view com callbacks."""
        if not self._main_window or not self._table:
            return

        # Sinais da MainWindow
        self._main_window.new_story_requested.connect(self._on_new_story)
        self._main_window.edit_story_requested.connect(self._on_edit_story)
        self._main_window.duplicate_story_requested.connect(
            self._on_duplicate_story
        )
        self._main_window.delete_story_requested.connect(self._on_delete_story)
        self._main_window.move_priority_up_requested.connect(
            self._on_move_priority_up
        )
        self._main_window.move_priority_down_requested.connect(
            self._on_move_priority_down
        )

        self._main_window.new_developer_requested.connect(
            self._on_new_developer
        )
        self._main_window.manage_developers_requested.connect(
            self._on_manage_developers
        )

        self._main_window.calculate_schedule_requested.connect(
            self._on_calculate_schedule
        )
        self._main_window.allocate_developers_requested.connect(
            self._on_allocate_developers
        )

        self._main_window.import_excel_requested.connect(self._on_import_excel)
        self._main_window.export_excel_requested.connect(self._on_export_excel)

        self._main_window.show_configuration_requested.connect(
            self._on_show_configuration
        )

        # Sinais da tabela
        self._table.story_field_changed.connect(
            self._story_controller.on_story_field_changed
        )
        self._table.edit_story_requested.connect(self._on_edit_story)
        self._table.duplicate_story_requested.connect(
            self._on_duplicate_story_by_id
        )
        self._table.delete_story_requested.connect(
            self._on_delete_story_by_id
        )

    def _setup_controllers(self) -> None:
        """Configura controllers com callbacks."""
        if not self._main_window:
            return

        # Story Controller
        self._story_controller.set_parent_widget(self._main_window)
        self._story_controller.set_refresh_callback(self.refresh_backlog)
        self._story_controller.set_loading_callbacks(
            self._show_recalculating, self._hide_recalculating
        )

        # Developer Controller
        self._developer_controller.set_parent_widget(self._main_window)
        self._developer_controller.set_refresh_callback(
            self._on_developers_changed
        )

        # Schedule Controller
        self._schedule_controller.set_parent_widget(self._main_window)
        self._schedule_controller.set_refresh_callback(self.refresh_backlog)
        self._schedule_controller.set_loading_callbacks(
            self._show_recalculating, self._hide_recalculating
        )

    def refresh_backlog(self) -> None:
        """Atualiza a tabela de backlog."""
        if not self._table:
            return

        stories = self._story_controller.list_stories()
        self._table.populate_from_stories(stories)

        # Atualizar contador na status bar
        if self._main_window:
            self._main_window.status_bar_manager.show_story_count(len(stories))

    def _show_recalculating(self) -> None:
        """Mostra indicador de recálculo."""
        if self._main_window:
            self._main_window.status_bar_manager.show_recalculating()

    def _hide_recalculating(self) -> None:
        """Esconde indicador de recálculo."""
        if self._main_window:
            self._main_window.status_bar_manager.clear()

    def _on_new_story(self) -> None:
        """Callback de nova história."""
        developers = self._developer_controller.list_developers()
        dialog = StoryFormDialog(self._main_window, None, developers)
        dialog.setModal(True)

        form_data_received = None

        def on_story_saved(form_data):
            nonlocal form_data_received
            form_data_received = form_data

        dialog.story_saved.connect(on_story_saved)
        result = dialog.exec()

        # Dialog fechou completamente, agora processar
        if result == 1 and form_data_received:
            self._story_controller.create_story(form_data_received)

    def _on_edit_story(self) -> None:
        """Callback de editar história selecionada."""
        if not self._table:
            return

        story_id = self._table.get_selected_story_id()
        if not story_id:
            MessageBox.warning(
                self._main_window,
                "Nenhuma História Selecionada",
                "Selecione uma história para editar.",
            )
            return

        self._on_edit_story_by_id(story_id)

    def _on_edit_story_by_id(self, story_id: str) -> None:
        """
        Abre formulário de edição.

        Args:
            story_id: ID da história a editar
        """
        story = self._story_controller.get_story(story_id)
        if not story:
            return

        developers = self._developer_controller.list_developers()
        dialog = StoryFormDialog(self._main_window, story, developers)
        dialog.story_saved.connect(
            lambda data: self._story_controller.update_story(story_id, data)
        )
        dialog.exec()

    def _on_duplicate_story(self) -> None:
        """Callback de duplicar história selecionada."""
        if not self._table:
            return

        story_id = self._table.get_selected_story_id()
        if not story_id:
            MessageBox.warning(
                self._main_window,
                "Nenhuma História Selecionada",
                "Selecione uma história para duplicar.",
            )
            return

        self._story_controller.duplicate_story(story_id)

    def _on_duplicate_story_by_id(self, story_id: str) -> None:
        """
        Duplica história por ID.

        Args:
            story_id: ID da história
        """
        self._story_controller.duplicate_story(story_id)

    def _on_delete_story(self) -> None:
        """Callback de deletar história selecionada."""
        if not self._table:
            return

        story_id = self._table.get_selected_story_id()
        if not story_id:
            MessageBox.warning(
                self._main_window,
                "Nenhuma História Selecionada",
                "Selecione uma história para deletar.",
            )
            return

        self._story_controller.delete_story(story_id)

    def _on_delete_story_by_id(self, story_id: str) -> None:
        """
        Deleta história por ID.

        Args:
            story_id: ID da história
        """
        self._story_controller.delete_story(story_id)

    def _on_move_priority_up(self) -> None:
        """Callback de mover prioridade para cima."""
        if not self._table:
            return

        story_id = self._table.get_selected_story_id()
        if not story_id:
            return

        self._story_controller.move_priority_up(story_id)

    def _on_move_priority_down(self) -> None:
        """Callback de mover prioridade para baixo."""
        if not self._table:
            return

        story_id = self._table.get_selected_story_id()
        if not story_id:
            return

        self._story_controller.move_priority_down(story_id)

    def _on_new_developer(self) -> None:
        """Callback de novo desenvolvedor."""
        dialog = DeveloperFormDialog(self._main_window)
        dialog.developer_saved.connect(
            lambda data: self._developer_controller.create_developer(data["name"])
        )
        dialog.exec()

    def _on_manage_developers(self) -> None:
        """Callback de gerenciar desenvolvedores."""
        # TODO: Implementar diálogo de gerenciamento de desenvolvedores
        MessageBox.info(
            self._main_window,
            "Em Desenvolvimento",
            "Gerenciamento de desenvolvedores será implementado em breve.",
        )

    def _on_developers_changed(self) -> None:
        """Callback quando lista de desenvolvedores muda."""
        self.refresh_backlog()

    def _on_calculate_schedule(self) -> None:
        """Callback de calcular cronograma."""
        self._schedule_controller.calculate_schedule()

    def _on_allocate_developers(self) -> None:
        """Callback de alocar desenvolvedores."""
        self._schedule_controller.allocate_developers()

    def _on_import_excel(self) -> None:
        """Callback de importar Excel."""
        file_path, _ = QFileDialog.getOpenFileName(
            self._main_window,
            "Importar Histórias de Excel",
            str(Path.home()),
            "Arquivos Excel (*.xlsx *.xls)",
        )

        if not file_path:
            return

        try:
            result = self._import_use_case.execute(file_path)
            MessageBox.success(
                self._main_window,
                "Sucesso",
                f"Importadas {result.success_count} histórias com sucesso!\n"
                f"Falhas: {result.error_count}",
            )
            self.refresh_backlog()
        except Exception as e:
            MessageBox.error(
                self._main_window, "Erro ao Importar Excel", str(e)
            )

    def _on_export_excel(self) -> None:
        """Callback de exportar Excel."""
        file_path, _ = QFileDialog.getSaveFileName(
            self._main_window,
            "Exportar Backlog para Excel",
            str(Path.home() / "backlog.xlsx"),
            "Arquivos Excel (*.xlsx)",
        )

        if not file_path:
            return

        try:
            self._export_use_case.execute(file_path)
            MessageBox.success(
                self._main_window,
                "Sucesso",
                f"Backlog exportado com sucesso para:\n{file_path}",
            )
        except Exception as e:
            MessageBox.error(
                self._main_window, "Erro ao Exportar Excel", str(e)
            )

    def _on_show_configuration(self) -> None:
        """Callback de mostrar configurações."""
        config = self._get_config_use_case.execute()
        dialog = ConfigurationDialog(self._main_window, config)
        dialog.configuration_saved.connect(
            lambda data: self._update_config_use_case.execute(data)
        )
        dialog.exec()
