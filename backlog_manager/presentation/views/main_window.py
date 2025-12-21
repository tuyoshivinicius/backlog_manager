"""
Janela principal da aplicação Backlog Manager.

Contém menu, toolbar, tabela de backlog e status bar.
"""
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QMenuBar,
    QMenu,
    QToolBar,
    QStatusBar,
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Signal, Qt

from backlog_manager.presentation.utils.status_bar_manager import StatusBarManager


class MainWindow(QMainWindow):
    """Janela principal da aplicação."""

    # Sinais para comunicação com controllers
    new_story_requested = Signal()
    edit_story_requested = Signal()
    duplicate_story_requested = Signal()
    delete_story_requested = Signal()
    move_priority_up_requested = Signal()
    move_priority_down_requested = Signal()

    new_developer_requested = Signal()
    manage_developers_requested = Signal()

    calculate_schedule_requested = Signal()
    allocate_developers_requested = Signal()

    import_excel_requested = Signal()
    export_excel_requested = Signal()

    show_configuration_requested = Signal()
    show_shortcuts_requested = Signal()
    show_about_requested = Signal()

    def __init__(self):
        """Inicializa a janela principal."""
        super().__init__()
        self._status_bar_manager: Optional[StatusBarManager] = None
        self._setup_ui()
        self._load_styles()

    def _setup_ui(self) -> None:
        """Configura a interface da janela."""
        # Configurações da janela
        self.setWindowTitle("Backlog Manager")
        self.setMinimumSize(1024, 600)
        self.resize(1280, 720)

        # Criar menu
        self._create_menu_bar()

        # Criar toolbar
        self._create_toolbar()

        # Criar status bar
        self._create_status_bar()

        # Widget central (será definido pelo controller)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

    def _create_menu_bar(self) -> None:
        """Cria a barra de menus."""
        menu_bar = self.menuBar()

        # Menu Arquivo
        file_menu = menu_bar.addMenu("&Arquivo")

        import_action = QAction("&Importar Excel...", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.setStatusTip("Importa histórias de arquivo Excel")
        import_action.triggered.connect(self.import_excel_requested.emit)
        file_menu.addAction(import_action)

        export_action = QAction("&Exportar Excel...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.setStatusTip("Exporta backlog para Excel")
        export_action.triggered.connect(self.export_excel_requested.emit)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("&Sair", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.setStatusTip("Fecha a aplicação")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu História
        story_menu = menu_bar.addMenu("&História")

        new_story_action = QAction("&Nova História", self)
        new_story_action.setShortcut(QKeySequence("Ctrl+N"))
        new_story_action.setStatusTip("Cria nova história")
        new_story_action.triggered.connect(self.new_story_requested.emit)
        story_menu.addAction(new_story_action)

        edit_story_action = QAction("&Editar História", self)
        edit_story_action.setShortcut(QKeySequence("Return"))
        edit_story_action.setStatusTip("Edita história selecionada")
        edit_story_action.triggered.connect(self.edit_story_requested.emit)
        story_menu.addAction(edit_story_action)

        duplicate_story_action = QAction("&Duplicar História", self)
        duplicate_story_action.setShortcut(QKeySequence("Ctrl+D"))
        duplicate_story_action.setStatusTip("Duplica história selecionada")
        duplicate_story_action.triggered.connect(self.duplicate_story_requested.emit)
        story_menu.addAction(duplicate_story_action)

        delete_story_action = QAction("D&eletar História", self)
        delete_story_action.setShortcut(QKeySequence("Delete"))
        delete_story_action.setStatusTip("Deleta história selecionada")
        delete_story_action.triggered.connect(self.delete_story_requested.emit)
        story_menu.addAction(delete_story_action)

        story_menu.addSeparator()

        move_up_action = QAction("Mover para &Cima", self)
        move_up_action.setShortcut(QKeySequence("Ctrl+Up"))
        move_up_action.setStatusTip("Aumenta prioridade da história")
        move_up_action.triggered.connect(self.move_priority_up_requested.emit)
        story_menu.addAction(move_up_action)

        move_down_action = QAction("Mover para &Baixo", self)
        move_down_action.setShortcut(QKeySequence("Ctrl+Down"))
        move_down_action.setStatusTip("Diminui prioridade da história")
        move_down_action.triggered.connect(self.move_priority_down_requested.emit)
        story_menu.addAction(move_down_action)

        # Menu Desenvolvedor
        dev_menu = menu_bar.addMenu("&Desenvolvedor")

        new_dev_action = QAction("&Novo Desenvolvedor", self)
        new_dev_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_dev_action.setStatusTip("Cria novo desenvolvedor")
        new_dev_action.triggered.connect(self.new_developer_requested.emit)
        dev_menu.addAction(new_dev_action)

        manage_devs_action = QAction("&Gerenciar Desenvolvedores", self)
        manage_devs_action.setStatusTip("Abre diálogo de gerenciamento de desenvolvedores")
        manage_devs_action.triggered.connect(self.manage_developers_requested.emit)
        dev_menu.addAction(manage_devs_action)

        # Menu Cronograma
        schedule_menu = menu_bar.addMenu("C&ronograma")

        calculate_action = QAction("&Calcular Cronograma", self)
        calculate_action.setShortcut(QKeySequence("F5"))
        calculate_action.setStatusTip("Recalcula todo o cronograma")
        calculate_action.triggered.connect(self.calculate_schedule_requested.emit)
        schedule_menu.addAction(calculate_action)

        allocate_action = QAction("&Alocar Desenvolvedores", self)
        allocate_action.setStatusTip("Aloca desenvolvedores automaticamente")
        allocate_action.triggered.connect(self.allocate_developers_requested.emit)
        schedule_menu.addAction(allocate_action)

        # Menu Configurações
        settings_menu = menu_bar.addMenu("&Configurações")

        config_action = QAction("&Configurações do Sistema...", self)
        config_action.setShortcut(QKeySequence("Ctrl+,"))
        config_action.setStatusTip("Abre configurações do sistema")
        config_action.triggered.connect(self.show_configuration_requested.emit)
        settings_menu.addAction(config_action)

        # Menu Ajuda
        help_menu = menu_bar.addMenu("Aj&uda")

        shortcuts_action = QAction("&Atalhos de Teclado", self)
        shortcuts_action.setShortcut(QKeySequence("F1"))
        shortcuts_action.setStatusTip("Mostra lista de atalhos")
        shortcuts_action.triggered.connect(self.show_shortcuts_requested.emit)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        about_action = QAction("&Sobre", self)
        about_action.setStatusTip("Sobre o Backlog Manager")
        about_action.triggered.connect(self.show_about_requested.emit)
        help_menu.addAction(about_action)

    def _create_toolbar(self) -> None:
        """Cria a barra de ferramentas."""
        toolbar = QToolBar("Ferramentas Principais")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        # Botão Nova História
        new_story_action = QAction("Nova História", self)
        new_story_action.setStatusTip("Cria nova história (Ctrl+N)")
        new_story_action.triggered.connect(self.new_story_requested.emit)
        toolbar.addAction(new_story_action)

        # Botão Editar História
        edit_story_action = QAction("Editar", self)
        edit_story_action.setStatusTip("Edita história selecionada (Enter)")
        edit_story_action.triggered.connect(self.edit_story_requested.emit)
        toolbar.addAction(edit_story_action)

        # Botão Deletar História
        delete_story_action = QAction("Deletar", self)
        delete_story_action.setStatusTip("Deleta história selecionada (Delete)")
        delete_story_action.triggered.connect(self.delete_story_requested.emit)
        toolbar.addAction(delete_story_action)

        toolbar.addSeparator()

        # Botão Importar Excel
        import_action = QAction("Importar Excel", self)
        import_action.setStatusTip("Importa histórias de Excel (Ctrl+I)")
        import_action.triggered.connect(self.import_excel_requested.emit)
        toolbar.addAction(import_action)

        # Botão Exportar Excel
        export_action = QAction("Exportar Excel", self)
        export_action.setStatusTip("Exporta backlog para Excel (Ctrl+E)")
        export_action.triggered.connect(self.export_excel_requested.emit)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        # Botão Calcular Cronograma
        calculate_action = QAction("Calcular Cronograma", self)
        calculate_action.setStatusTip("Recalcula cronograma (F5)")
        calculate_action.triggered.connect(self.calculate_schedule_requested.emit)
        toolbar.addAction(calculate_action)

        # Botão Alocar Desenvolvedores
        allocate_action = QAction("Alocar Desenvolvedores", self)
        allocate_action.setStatusTip("Distribui desenvolvedores automaticamente (Shift+F5)")
        allocate_action.triggered.connect(self.allocate_developers_requested.emit)
        toolbar.addAction(allocate_action)

        toolbar.addSeparator()

        # Botão Configurações
        config_action = QAction("⚙️ Configurações", self)
        config_action.setStatusTip("Configurar velocidade do time e data de início do roadmap")
        config_action.triggered.connect(self.show_configuration_requested.emit)
        toolbar.addAction(config_action)

    def _create_status_bar(self) -> None:
        """Cria a barra de status."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self._status_bar_manager = StatusBarManager(status_bar)
        self._status_bar_manager.clear()

    def _load_styles(self) -> None:
        """Carrega e aplica estilos QSS."""
        styles_path = Path(__file__).parent.parent / "styles" / "app_styles.qss"
        if styles_path.exists():
            with open(styles_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    @property
    def status_bar_manager(self) -> StatusBarManager:
        """
        Retorna o gerenciador de status bar.

        Returns:
            Gerenciador de status bar
        """
        if self._status_bar_manager is None:
            raise RuntimeError("StatusBarManager não inicializado")
        return self._status_bar_manager

    def set_central_widget(self, widget: QWidget) -> None:
        """
        Define o widget central da janela.

        Args:
            widget: Widget a ser definido como central
        """
        self.setCentralWidget(widget)

    def closeEvent(self, event) -> None:
        """
        Evento de fechamento da janela.

        Pode ser usado para confirmações ou salvamento de dados.

        Args:
            event: Evento de fechamento
        """
        # Por enquanto, apenas fecha. Pode adicionar confirmação depois.
        event.accept()
