"""Script de teste para debug de criação de história."""
import sys
import traceback

from backlog_manager.presentation.di_container import DIContainer


def test_create_story():
    """Testa criação de história."""
    print("=" * 60)
    print("TESTE DE CRIAÇÃO DE HISTÓRIA")
    print("=" * 60)

    try:
        # 1. Inicializar DI Container
        print("\n1. Inicializando DI Container...")
        di = DIContainer("test_backlog.db")
        print("[OK] DI Container inicializado")

        # 2. Obter use case
        print("\n2. Obtendo CreateStoryUseCase...")
        create_story = di.create_story_use_case
        print("[OK] Use case obtido")

        # 3. Preparar dados (simulando formulário)
        print("\n3. Preparando dados da historia...")
        form_data = {
            "feature": "Login",
            "name": "Implementar tela de login",
            "story_point": 5,
            "status": "BACKLOG",
            "developer_id": None,
            "priority": 1,
        }
        print(f"[OK] Dados preparados: {form_data}")

        # 4. Tentar criar história
        print("\n4. Criando historia...")
        story_dto = create_story.execute(form_data)
        print(f"[OK] Historia criada com sucesso!")
        print(f"  ID: {story_dto.id}")
        print(f"  Feature: {story_dto.feature}")
        print(f"  Nome: {story_dto.name}")
        print(f"  SP: {story_dto.story_point}")
        print(f"  Status: {story_dto.status}")

        # 5. Verificar se foi salva
        print("\n5. Verificando se foi salva no banco...")
        list_stories = di.list_stories_use_case
        stories = list_stories.execute()
        print(f"[OK] Total de historias no banco: {len(stories)}")

        for s in stories:
            print(f"  - {s.id}: {s.name}")

        print("\n" + "=" * 60)
        print("TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)

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

    return True


if __name__ == "__main__":
    success = test_create_story()
    sys.exit(0 if success else 1)
