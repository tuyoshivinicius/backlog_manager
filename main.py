"""
Ponto de entrada da aplicação Backlog Manager.

Inicializa a aplicação Qt e exibe a janela principal.
"""
import sys
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox

from backlog_manager.presentation.di_container import DIContainer


def exception_hook(exctype, value, tb):
    """
    Hook global para capturar exceções não tratadas.

    Args:
        exctype: Tipo da exceção
        value: Valor da exceção
        tb: Traceback
    """
    print("\n" + "="*60)
    print("EXCEÇÃO NÃO TRATADA CAPTURADA PELO HOOK GLOBAL!")
    print("="*60)
    print(f"Tipo: {exctype.__name__}")
    print(f"Mensagem: {str(value)}")
    print("\nStack trace completo:")
    traceback.print_exception(exctype, value, tb)
    print("="*60 + "\n")

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
    # Instalar hook de exceção global
    sys.excepthook = exception_hook

    try:
        # Criar aplicação Qt
        app = QApplication(sys.argv)
        app.setApplicationName("Backlog Manager")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Backlog Manager")

        # Criar container de dependências
        di_container = DIContainer()

        # Obter controlador principal e inicializar interface
        main_controller = di_container.get_main_controller()
        main_window = main_controller.initialize_ui()

        # Exibir janela principal
        main_window.show()

        # Executar aplicação
        sys.exit(app.exec())

    except Exception as e:
        print(f"\nErro fatal: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

        QMessageBox.critical(
            None,
            "Erro Fatal",
            f"Falha ao inicializar aplicação:\n\n{str(e)}",
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
