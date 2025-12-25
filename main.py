"""
Ponto de entrada da aplicação Backlog Manager.

Inicializa a aplicação Qt e exibe a janela principal.
"""
import logging
import logging.handlers
import os
import sys
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox

from backlog_manager.presentation.di_container import DIContainer

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Configura sistema de logging da aplicação.

    Args:
        log_level: Nível de logging (DEBUG, INFO, WARNING, ERROR). Default: INFO
        log_file: Caminho para arquivo de log (opcional). Se fornecido, usa RotatingFileHandler
                  com 10MB max size e 5 backups.

    Environment Variables:
        BACKLOG_MANAGER_LOG_LEVEL: Define nível de log (DEBUG, INFO, WARNING, ERROR)
        BACKLOG_MANAGER_LOG_FILE: Define caminho para arquivo de log (opcional)

    Examples:
        # Windows
        set BACKLOG_MANAGER_LOG_LEVEL=DEBUG
        set BACKLOG_MANAGER_LOG_FILE=logs/backlog.log
        python -m backlog_manager.main

        # Linux/Mac
        export BACKLOG_MANAGER_LOG_LEVEL=DEBUG
        export BACKLOG_MANAGER_LOG_FILE=logs/backlog.log
        python -m backlog_manager.main
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Formato detalhado para debugging
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (sempre ativo)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (opcional)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Silenciar bibliotecas third-party
    logging.getLogger('PySide6').setLevel(logging.WARNING)


def exception_hook(exctype, value, tb):
    """
    Hook global para capturar exceções não tratadas.

    Args:
        exctype: Tipo da exceção
        value: Valor da exceção
        tb: Traceback
    """
    logger.critical("="*60)
    logger.critical("EXCEÇÃO NÃO TRATADA CAPTURADA PELO HOOK GLOBAL!")
    logger.critical("="*60)
    logger.critical(f"Tipo: {exctype.__name__}")
    logger.critical(f"Mensagem: {str(value)}")
    logger.critical("Stack trace completo:")

    # Formatar traceback como string para o logger
    tb_lines = traceback.format_exception(exctype, value, tb)
    for line in tb_lines:
        logger.critical(line.rstrip())

    logger.critical("="*60)

    # Tentar mostrar dialog (pode falhar se Qt já está destruído)
    try:
        QMessageBox.critical(
            None,
            "Erro Fatal",
            f"Erro não tratado: {exctype.__name__}\n\n{str(value)}\n\nVerifique o console para detalhes.",
        )
    except:
        pass

    # Chamar o hook original
    sys.__excepthook__(exctype, value, tb)


def main():
    """Função principal da aplicação."""
    # Ler nível de log de variável de ambiente (default: INFO)
    log_level = os.getenv("BACKLOG_MANAGER_LOG_LEVEL", "INFO")
    log_file = os.getenv("BACKLOG_MANAGER_LOG_FILE")  # Opcional

    # Configurar logging ANTES de criar QApplication
    setup_logging(log_level=log_level, log_file=log_file)

    # Instalar hook de exceção global
    sys.excepthook = exception_hook

    logger.info(f"Iniciando Backlog Manager (log level: {log_level})")

    try:
        # Criar aplicação Qt
        logger.info("Criando aplicação Qt")
        app = QApplication(sys.argv)
        app.setApplicationName("Backlog Manager")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Backlog Manager")

        # Criar container de dependências
        logger.debug("Criando container de dependências")
        di_container = DIContainer()

        # Obter controlador principal e inicializar interface
        logger.debug("Inicializando interface principal")
        main_controller = di_container.get_main_controller()
        main_window = main_controller.initialize_ui()

        # Exibir janela principal
        logger.info("Exibindo janela principal")
        main_window.show()

        # Executar aplicação
        logger.info("Aplicação iniciada com sucesso")
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Erro fatal ao inicializar aplicação: {type(e).__name__}: {str(e)}", exc_info=True)

        QMessageBox.critical(
            None,
            "Erro Fatal",
            f"Falha ao inicializar aplicação:\n\n{str(e)}",
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
