"""Script de teste simulando fluxo completo da UI."""
import sys
import traceback
from pathlib import Path

# Limpar banco de teste se existir
test_db = Path("test_ui_flow.db")
if test_db.exists():
    test_db.unlink()

from backlog_manager.presentation.di_container import DIContainer


def test_ui_flow():
    """Testa fluxo completo como na UI."""
    print("=" * 60)
    print("TESTE DE FLUXO DA UI")
    print("=" * 60)

    try:
        # 1. Inicializar DI Container (como main.py faz)
        print("\n1. Inicializando DI Container...")
        di = DIContainer("test_ui_flow.db")
        print("[OK] DI Container inicializado")

        # 2. Obter main controller (como main.py faz)
        print("\n2. Obtendo MainController...")
        main_controller = di.get_main_controller()
        print("[OK] MainController obtido")

        # 3. Obter story controller diretamente
        print("\n3. Obtendo StoryController...")
        story_controller = di.story_controller
        print(f"[OK] StoryController obtido")
        print(f"    Parent widget: {story_controller._parent_widget}")
        print(f"    Refresh callback: {story_controller._refresh_callback}")

        # 4. Simular formulário (exatamente como StoryFormDialog faz)
        print("\n4. Preparando dados do formulário...")
        form_data = {
            "feature": "Login",
            "name": "Implementar tela de login",
            "story_point": 5,
            "status": "BACKLOG",
            "developer_id": None,
            "priority": 1,
        }
        print(f"[OK] Dados preparados: {form_data}")

        # 5. Chamar story_controller.create_story (como o signal faz)
        print("\n5. Chamando story_controller.create_story()...")
        print("    (Este é o ponto onde o bug deve ocorrer)")

        # Adicionar debugging ao método
        print(f"    Executando create_story com parent_widget={story_controller._parent_widget}")

        story_controller.create_story(form_data)

        print("[OK] create_story executado sem exceção!")

        # 6. Verificar se foi salva
        print("\n6. Verificando se foi salva...")
        stories = story_controller.list_stories()
        print(f"[OK] Total de histórias: {len(stories)}")

        for s in stories:
            print(f"    - {s.id}: {s.name}")

        print("\n" + "=" * 60)
        print("TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print("ERRO ENCONTRADO!")
        print("=" * 60)
        print(f"\nTipo: {type(e).__name__}")
        print(f"Mensagem: {str(e)}")
        print("\nStack trace completo:")
        traceback.print_exc()
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_ui_flow()
    sys.exit(0 if success else 1)
