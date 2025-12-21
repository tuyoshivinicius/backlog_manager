"""Script para testar a migration do banco de dados."""
import sys
from pathlib import Path

# Adicionar root ao path
sys.path.insert(0, str(Path(__file__).parent))

from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


def test_migration():
    """Testa a aplicação da migration."""
    print("=" * 60)
    print("TESTE DE MIGRATION - roadmap_start_date")
    print("=" * 60)

    # Conectar ao banco (ou criar se não existir)
    db_path = Path(__file__).parent / "backlog_manager.db"
    print(f"\nBanco de dados: {db_path}")

    # Resetar singleton
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None

    # Conectar
    connection = SQLiteConnection(str(db_path))
    conn = connection.get_connection()

    print("\nAplicando migration...")

    # Importar e executar migration
    try:
        import importlib

        migration_module = importlib.import_module(
            "backlog_manager.infrastructure.database.migrations.001_add_roadmap_start_date"
        )
        apply_if_needed = migration_module.apply_if_needed

        result = apply_if_needed(conn)

        if result:
            print("[OK] Migration aplicada com sucesso!")
        else:
            print("[INFO] Migration ja estava aplicada (coluna ja existe)")

    except Exception as e:
        print(f"[ERROR] Erro ao aplicar migration: {e}")
        return False

    # Verificar estrutura da tabela
    print("\nVerificando estrutura da tabela configuration...")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(configuration)")
    columns = cursor.fetchall()

    print("\nColunas da tabela:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

    # Verificar se roadmap_start_date existe
    column_names = [col[1] for col in columns]
    if "roadmap_start_date" in column_names:
        print("\n[OK] Coluna roadmap_start_date encontrada!")
        return True
    else:
        print("\n[ERROR] Coluna roadmap_start_date NAO encontrada!")
        return False


if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)
