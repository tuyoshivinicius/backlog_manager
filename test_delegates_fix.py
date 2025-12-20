"""
Script de teste para verificar se os delegates corrigidos funcionam.
"""
import sys
from PySide6.QtWidgets import QApplication

from backlog_manager.presentation.di_container import DIContainer


def main():
    """Testa a inicialização com delegates corrigidos."""
    print("=" * 60)
    print("TESTE DE DELEGATES CORRIGIDOS")
    print("=" * 60)

    try:
        print("\n1. Criando aplicação Qt...")
        app = QApplication(sys.argv)
        print("   ✓ Aplicação Qt criada")

        print("\n2. Criando DIContainer...")
        di_container = DIContainer()
        print("   ✓ DIContainer criado")

        print("\n3. Obtendo MainController...")
        main_controller = di_container.get_main_controller()
        print("   ✓ MainController criado")

        print("\n4. Inicializando UI (MOMENTO CRÍTICO - delegates serão configurados)...")
        main_window = main_controller.initialize_ui()
        print("   ✓ UI inicializada SEM CRASH!")

        print("\n5. Verificando delegates configurados...")
        table = main_window.centralWidget()
        if table:
            print("   ✓ Tabela obtida")

            # Verificar se delegates estão configurados
            story_point_delegate = table.itemDelegateForColumn(7)  # COL_STORY_POINT
            status_delegate = table.itemDelegateForColumn(4)  # COL_STATUS
            dev_delegate = table.itemDelegateForColumn(5)  # COL_DEVELOPER

            print(f"   - StoryPointDelegate: {type(story_point_delegate).__name__}")
            print(f"   - StatusDelegate: {type(status_delegate).__name__}")
            print(f"   - DeveloperDelegate: {type(dev_delegate).__name__}")

        print("\n6. Exibindo janela...")
        main_window.show()
        print("   ✓ Janela exibida")

        print("\n" + "=" * 60)
        print("✓✓✓ SUCESSO! Delegates funcionando sem crash!")
        print("=" * 60)
        print("\nAplicação está rodando. Feche a janela para encerrar o teste.")

        # Executar event loop
        sys.exit(app.exec())

    except Exception as e:
        print(f"\n❌ ERRO: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
