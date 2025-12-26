"""
Controlador principal da aplicação.

Coordena todos os sub-controllers e gerencia a janela principal.
"""
import logging
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import QFileDialog

logger = logging.getLogger(__name__)

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
from backlog_manager.application.use_cases.story.validate_developer_allocation import (
    ValidateDeveloperAllocationUseCase,
)
from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
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
from backlog_manager.presentation.views.widgets.dependencies_delegate import (
    DependenciesDelegate,
)
from backlog_manager.presentation.views.widgets.feature_delegate import (
    FeatureDelegate,
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
from backlog_manager.presentation.controllers.feature_controller import (
    FeatureController,
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
        feature_controller: FeatureController,
        schedule_controller: ScheduleController,
        import_excel_use_case: ImportFromExcelUseCase,
        export_excel_use_case: ExportToExcelUseCase,
        get_configuration_use_case: GetConfigurationUseCase,
        update_configuration_use_case: UpdateConfigurationUseCase,
        validate_allocation_use_case: ValidateDeveloperAllocationUseCase,
        story_repository: StoryRepository,
    ):
        """
        Inicializa o controlador principal.

        Args:
            story_controller: Controlador de histórias
            developer_controller: Controlador de desenvolvedores
            feature_controller: Controlador de features
            schedule_controller: Controlador de cronograma
            import_excel_use_case: Use case de importação Excel
            export_excel_use_case: Use case de exportação Excel
            get_configuration_use_case: Use case de obter configuração
            update_configuration_use_case: Use case de atualizar configuração
            validate_allocation_use_case: Use case de validação de alocação
            story_repository: Repositório de histórias
        """
        self._story_controller = story_controller
        self._developer_controller = developer_controller
        self._feature_controller = feature_controller
        self._schedule_controller = schedule_controller
        self._import_use_case = import_excel_use_case
        self._export_use_case = export_excel_use_case
        self._get_config_use_case = get_configuration_use_case
        self._update_config_use_case = update_configuration_use_case
        self._validate_allocation_use_case = validate_allocation_use_case
        self._story_repository = story_repository

        self._main_window: Optional[MainWindow] = None
        self._table: Optional[EditableTableWidget] = None

        # Manter referências aos delegates para evitar garbage collection
        self._story_point_delegate = None
        self._status_delegate = None
        self._developer_delegate = None
        self._dependencies_delegate = None
        self._feature_delegate = None

    def initialize_ui(self) -> MainWindow:
        """
        Inicializa a interface gráfica.

        Returns:
            Janela principal
        """
        logger.info("Inicializando interface gráfica")

        # Criar janela principal
        logger.debug("Criando janela principal")
        self._main_window = MainWindow()

        # Criar tabela
        logger.debug("Criando tabela editável")
        self._table = EditableTableWidget()

        # Definir tabela como widget central
        self._main_window.set_central_widget(self._table)

        # Conectar sinais
        logger.debug("Conectando sinais")
        self._connect_signals()

        # Configurar controllers
        logger.debug("Configurando controllers")
        self._setup_controllers()

        # Carregar dados iniciais ANTES de configurar delegates
        logger.debug("Carregando dados iniciais")
        self.refresh_backlog()

        # Configurar delegates APÓS popular tabela (pode ajudar com crashes)
        logger.debug("Configurando delegates")
        self._setup_delegates()

        logger.info("Interface gráfica inicializada com sucesso")
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

        # Developer Delegate - ComboBox com lista de desenvolvedores (com cores de disponibilidade)
        self._developer_delegate = DeveloperDelegate(
            validate_allocation_use_case=self._validate_allocation_use_case,
            story_repository=self._story_repository
        )
        developers = self._developer_controller.list_developers()
        self._developer_delegate.set_developers(developers)
        self._table.setItemDelegateForColumn(
            EditableTableWidget.COL_DEVELOPER, self._developer_delegate
        )

        # Dependencies Delegate - Abre dialog para seleção de dependências
        self._dependencies_delegate = DependenciesDelegate()
        self._table.setItemDelegateForColumn(
            EditableTableWidget.COL_DEPENDENCIES, self._dependencies_delegate
        )

        # Feature Delegate - ComboBox com lista de features
        self._feature_delegate = FeatureDelegate()
        features = self._feature_controller.list_features()
        self._feature_delegate.set_features(features)
        self._table.setItemDelegateForColumn(
            EditableTableWidget.COL_FEATURE, self._feature_delegate
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

        self._main_window.manage_features_requested.connect(
            self._on_manage_features
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
        self._table.manage_dependencies_requested.connect(
            self._on_manage_dependencies
        )

    def _setup_controllers(self) -> None:
        """Configura controllers com callbacks."""
        if not self._main_window:
            return

        # Story Controller
        self._story_controller.set_parent_widget(self._main_window)
        self._story_controller.set_table_widget(self._table)
        self._story_controller.set_refresh_callback(self.refresh_backlog)
        self._story_controller.set_loading_callbacks(
            self._show_recalculating, self._hide_recalculating
        )

        # Developer Controller
        self._developer_controller.set_parent_widget(self._main_window)
        self._developer_controller.set_refresh_callback(
            self._on_developers_changed
        )

        # Feature Controller
        self._feature_controller.set_parent_widget(self._main_window)
        self._feature_controller.set_refresh_callback(
            self._on_features_changed
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
            logger.warning("Tentativa de refresh sem tabela inicializada")
            return

        logger.debug("Atualizando tabela de backlog")
        stories = self._story_controller.list_stories()
        logger.debug(f"Carregadas {len(stories)} histórias")
        self._table.populate_from_stories(stories)

        # Atualizar lista de histórias no DependenciesDelegate
        if self._dependencies_delegate:
            self._dependencies_delegate.set_stories(stories)

        # Atualizar lista de desenvolvedores no DeveloperDelegate
        if self._developer_delegate:
            developers = self._developer_controller.list_developers()
            self._developer_delegate.set_developers(developers)
            logger.debug(f"Atualizados {len(developers)} desenvolvedores no delegate")

        # Atualizar lista de features no FeatureDelegate
        if self._feature_delegate:
            features = self._feature_controller.list_features()
            self._feature_delegate.set_features(features)
            logger.debug(f"Atualizadas {len(features)} features no delegate")

        # Atualizar contador na status bar
        if self._main_window:
            self._main_window.status_bar_manager.show_story_count(len(stories))

        logger.info(f"Backlog atualizado: {len(stories)} histórias exibidas")

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
        logger.info("Usuário solicitou criação de nova história")

        developers = self._developer_controller.list_developers()
        features = self._feature_controller.list_features()
        all_stories = self._story_controller.list_stories()
        logger.debug(f"Abrindo dialog com {len(developers)} devs, {len(features)} features, {len(all_stories)} histórias")

        dialog = StoryFormDialog(self._main_window, None, developers, features, all_stories)
        dialog.setModal(True)

        form_data_received = None

        def on_story_saved(form_data):
            nonlocal form_data_received
            form_data_received = form_data

        dialog.story_saved.connect(on_story_saved)
        result = dialog.exec()

        # Dialog fechou completamente, agora processar
        if result == 1 and form_data_received:
            logger.info("Usuário confirmou criação de história")
            self._story_controller.create_story(form_data_received)
        else:
            logger.debug("Criação de história cancelada pelo usuário")

    def _on_edit_story(self) -> None:
        """Callback de editar história selecionada."""
        if not self._table:
            return

        story_id = self._table.get_selected_story_id()
        if not story_id:
            logger.warning("Tentativa de editar sem história selecionada")
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
        logger.info(f"Usuário solicitou edição da história: id='{story_id}'")

        story = self._story_controller.get_story(story_id)
        if not story:
            logger.warning(f"História não encontrada para edição: id='{story_id}'")
            return

        developers = self._developer_controller.list_developers()
        features = self._feature_controller.list_features()
        all_stories = self._story_controller.list_stories()
        logger.debug(f"Abrindo dialog de edição para '{story_id}'")

        dialog = StoryFormDialog(self._main_window, story, developers, features, all_stories)
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
            logger.warning("Tentativa de duplicar sem história selecionada")
            MessageBox.warning(
                self._main_window,
                "Nenhuma História Selecionada",
                "Selecione uma história para duplicar.",
            )
            return

        logger.info(f"Usuário solicitou duplicação da história: id='{story_id}'")
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
            logger.warning("Tentativa de deletar sem história selecionada")
            MessageBox.warning(
                self._main_window,
                "Nenhuma História Selecionada",
                "Selecione uma história para deletar.",
            )
            return

        logger.info(f"Usuário solicitou deleção da história: id='{story_id}'")
        self._story_controller.delete_story(story_id)

    def _on_delete_story_by_id(self, story_id: str) -> None:
        """
        Deleta história por ID.

        Args:
            story_id: ID da história
        """
        self._story_controller.delete_story(story_id)

    def _on_manage_dependencies(self, story_id: str) -> None:
        """
        Abre dialog de gerenciamento de dependências.

        Args:
            story_id: ID da história
        """
        from backlog_manager.presentation.views.dependencies_dialog import (
            DependenciesDialog,
        )

        # Obter história atual
        story = self._story_controller.get_story(story_id)
        if not story:
            return

        # Obter todas as histórias
        all_stories = self._story_controller.list_stories()

        # Abrir dialog
        dialog = DependenciesDialog(
            self._main_window, story, all_stories, story.dependencies
        )

        if dialog.exec():
            # Atualizar dependências
            new_deps = dialog.get_dependencies()
            self._story_controller.on_story_field_changed(
                story_id, "dependencies", new_deps
            )

    def _on_move_priority_up(self) -> None:
        """Callback de mover prioridade para cima."""
        if not self._table:
            return

        # 1. Capturar story_id ANTES da operação
        story_id = self._table.get_selected_story_id()
        if not story_id:
            return

        # 2. Executar mudança de prioridade (refresh acontece automaticamente)
        self._story_controller.move_priority_up(story_id)

        # 3. Reselecionar história na nova posição
        self._table.select_story_by_id(story_id)

        # 4. Aplicar feedback visual vermelho
        self._table.apply_priority_change_feedback(True, source="priority")

        # 5. Remover feedback após 1 segundo
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self._table.apply_priority_change_feedback(False, source="priority"))

    def _on_move_priority_down(self) -> None:
        """Callback de mover prioridade para baixo."""
        if not self._table:
            return

        # 1. Capturar story_id ANTES da operação
        story_id = self._table.get_selected_story_id()
        if not story_id:
            return

        # 2. Executar mudança de prioridade (refresh acontece automaticamente)
        self._story_controller.move_priority_down(story_id)

        # 3. Reselecionar história na nova posição
        self._table.select_story_by_id(story_id)

        # 4. Aplicar feedback visual vermelho
        self._table.apply_priority_change_feedback(True, source="priority")

        # 5. Remover feedback após 1 segundo
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self._table.apply_priority_change_feedback(False, source="priority"))

    def _restore_selection_after_priority_change(self, story_id: str) -> None:
        """
        Restaura seleção e remove feedback visual após alteração de prioridade.

        Args:
            story_id: ID da história a reselecionar
        """
        if not self._table:
            return

        # Tentar reselecionar história em sua nova posição
        success = self._table.select_story_by_id(story_id)

        if not success:
            # Fallback: selecionar primeira linha se história não foi encontrada
            if self._table.rowCount() > 0:
                self._table.selectRow(0)

        # Sempre remover feedback visual de mudança de prioridade (voltar cor padrão)
        self._table.apply_priority_change_feedback(False, source="priority")

    def _on_new_developer(self) -> None:
        """Callback de novo desenvolvedor."""
        dialog = DeveloperFormDialog(self._main_window)
        dialog.developer_saved.connect(
            lambda data: self._developer_controller.create_developer(data["name"])
        )
        dialog.exec()

    def _on_manage_developers(self) -> None:
        """Callback de gerenciar desenvolvedores."""
        from backlog_manager.presentation.views.developer_manager_dialog import (
            DeveloperManagerDialog,
        )

        developers = self._developer_controller.list_developers()
        dialog = DeveloperManagerDialog(self._main_window, developers)

        # Definir callbacks locais para ter acesso ao dialog
        def on_created(name: str) -> None:
            self._developer_controller.create_developer(name)
            # Atualizar lista no dialog
            updated_devs = self._developer_controller.list_developers()
            dialog.refresh_developers(updated_devs)

        def on_updated(developer_id: str, new_name: str) -> None:
            self._developer_controller.update_developer(developer_id, new_name)
            # Atualizar lista no dialog
            updated_devs = self._developer_controller.list_developers()
            dialog.refresh_developers(updated_devs)

        def on_deleted(developer_id: str) -> None:
            self._developer_controller.delete_developer(developer_id)
            # Atualizar lista no dialog
            updated_devs = self._developer_controller.list_developers()
            dialog.refresh_developers(updated_devs)

        # Conectar sinais com callbacks locais
        dialog.developer_created.connect(on_created)
        dialog.developer_updated.connect(on_updated)
        dialog.developer_deleted.connect(on_deleted)

        dialog.exec()

        # Após fechar o dialog, atualizar tabela principal
        self.refresh_backlog()

    def _on_developers_changed(self) -> None:
        """Callback quando lista de desenvolvedores muda."""
        # Atualizar lista de desenvolvedores no delegate
        if self._developer_delegate:
            developers = self._developer_controller.list_developers()
            self._developer_delegate.set_developers(developers)

        self.refresh_backlog()

    def _on_manage_features(self) -> None:
        """Callback de gerenciar features."""
        from backlog_manager.presentation.views.feature_manager_dialog import (
            FeatureManagerDialog,
        )

        features = self._feature_controller.list_features()
        dialog = FeatureManagerDialog(self._main_window, features)

        # Definir callbacks locais para ter acesso ao dialog
        def on_created(name: str, wave: int) -> None:
            self._feature_controller.create_feature(name, wave)
            # Atualizar lista no dialog
            updated_features = self._feature_controller.list_features()
            dialog.refresh(updated_features)

        def on_updated(feature_id: str, new_name: str, new_wave: int) -> None:
            self._feature_controller.update_feature(feature_id, new_name, new_wave)
            # Atualizar lista no dialog
            updated_features = self._feature_controller.list_features()
            dialog.refresh(updated_features)

        def on_deleted(feature_id: str) -> None:
            self._feature_controller.delete_feature(feature_id)
            # Atualizar lista no dialog
            updated_features = self._feature_controller.list_features()
            dialog.refresh(updated_features)

        # Conectar sinais com callbacks locais
        dialog.feature_created.connect(on_created)
        dialog.feature_updated.connect(on_updated)
        dialog.feature_deleted.connect(on_deleted)

        dialog.exec()

        # Após fechar o dialog, atualizar tabela principal
        self.refresh_backlog()

    def _on_features_changed(self) -> None:
        """Callback quando lista de features muda."""
        # Atualizar lista de features no delegate
        if self._feature_delegate:
            features = self._feature_controller.list_features()
            self._feature_delegate.set_features(features)

        self.refresh_backlog()

    def _on_calculate_schedule(self) -> None:
        """Callback de calcular cronograma."""
        logger.info("Usuário solicitou cálculo de cronograma")
        self._schedule_controller.calculate_schedule()

    def _on_allocate_developers(self) -> None:
        """Callback de alocar desenvolvedores."""
        logger.info("Usuário solicitou alocação automática de desenvolvedores")
        self._schedule_controller.allocate_developers()

    def _on_import_excel(self) -> None:
        """Callback de importar Excel."""
        logger.info("Usuário solicitou importação de Excel")

        file_path, _ = QFileDialog.getOpenFileName(
            self._main_window,
            "Importar Histórias de Excel",
            str(Path.home()),
            "Arquivos Excel (*.xlsx *.xls)",
        )

        if not file_path:
            logger.debug("Importação de Excel cancelada pelo usuário")
            return

        logger.info(f"Iniciando importação de: {file_path}")

        try:
            result = self._import_use_case.execute(file_path)

            # Extrair estatísticas de importação
            if result.import_stats:
                total_importadas = result.import_stats.get("total_importadas", 0)
                ignoradas_duplicadas = result.import_stats.get("ignoradas_duplicadas", 0)
                ignoradas_invalidas = result.import_stats.get("ignoradas_invalidas", 0)
                total_falhas = ignoradas_duplicadas + ignoradas_invalidas

                logger.info(f"Importação concluída: {total_importadas} importadas, {total_falhas} falhas")

                MessageBox.success(
                    self._main_window,
                    "Sucesso",
                    f"Importadas {total_importadas} histórias com sucesso!\n"
                    f"Falhas: {total_falhas}",
                )
            else:
                logger.info(f"Importação concluída: {result.total_count} histórias")

                MessageBox.success(
                    self._main_window,
                    "Sucesso",
                    f"Importadas {result.total_count} histórias com sucesso!",
                )

            self.refresh_backlog()
        except Exception as e:
            logger.error(f"Erro ao importar Excel: {e}", exc_info=True)
            MessageBox.error(
                self._main_window, "Erro ao Importar Excel", str(e)
            )

    def _on_export_excel(self) -> None:
        """Callback de exportar Excel."""
        logger.info("Usuário solicitou exportação de Excel")

        file_path, _ = QFileDialog.getSaveFileName(
            self._main_window,
            "Exportar Backlog para Excel",
            str(Path.home() / "backlog.xlsx"),
            "Arquivos Excel (*.xlsx)",
        )

        if not file_path:
            logger.debug("Exportação de Excel cancelada pelo usuário")
            return

        logger.info(f"Iniciando exportação para: {file_path}")

        try:
            self._export_use_case.execute(file_path)
            logger.info(f"Exportação concluída com sucesso: {file_path}")

            MessageBox.success(
                self._main_window,
                "Sucesso",
                f"Backlog exportado com sucesso para:\n{file_path}",
            )
        except Exception as e:
            logger.error(f"Erro ao exportar Excel: {e}", exc_info=True)
            MessageBox.error(
                self._main_window, "Erro ao Exportar Excel", str(e)
            )

    def _on_show_configuration(self) -> None:
        """Callback de mostrar configurações."""
        config = self._get_config_use_case.execute()
        dialog = ConfigurationDialog(self._main_window, config)
        dialog.configuration_saved.connect(self._on_configuration_saved)
        dialog.exec()

    def _on_configuration_saved(self, data: dict) -> None:
        """
        Callback quando configuração é salva.

        Args:
            data: Dicionário com story_points_per_sprint, workdays_per_sprint,
                  roadmap_start_date, allocation_criteria
        """
        try:
            # Extrair dados
            sp_per_sprint = data["story_points_per_sprint"]
            workdays_per_sprint = data["workdays_per_sprint"]
            roadmap_start_date = data.get("roadmap_start_date")  # Opcional
            allocation_criteria = data.get("allocation_criteria")  # Opcional

            # Atualizar configuração
            updated_config, requires_recalc = self._update_config_use_case.execute(
                story_points_per_sprint=sp_per_sprint,
                workdays_per_sprint=workdays_per_sprint,
                roadmap_start_date=roadmap_start_date,
                allocation_criteria=allocation_criteria,
            )

            # Se houve mudança que requer recálculo, executar automaticamente
            if requires_recalc:
                try:
                    # Recalcular cronograma usando a nova configuração
                    self._on_calculate_schedule()

                    # Mostrar mensagem de sucesso com recálculo
                    MessageBox.success(
                        self._main_window,
                        "Configuração Salva",
                        "Configurações atualizadas com sucesso!\n\n"
                        "O cronograma foi recalculado automaticamente.",
                    )
                except Exception as e:
                    MessageBox.error(
                        self._main_window,
                        "Erro ao Recalcular",
                        f"Configuração salva, mas houve erro ao recalcular cronograma:\n{e}",
                    )
            else:
                # Nenhuma mudança relevante, apenas confirmar
                MessageBox.success(
                    self._main_window,
                    "Configuração Salva",
                    "Configurações atualizadas com sucesso!",
                )

            # Atualizar status bar
            self._main_window.status_bar_manager.show_message("Configuração atualizada", 3000)

        except ValueError as e:
            MessageBox.error(self._main_window, "Erro de Validação", str(e))
