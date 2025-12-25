"""Script para testar a migration 003."""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection


def main():
    """Testa a migration 003."""
    print("\n" + "="*60)
    print("TESTANDO MIGRATION 003 - Features e Ondas")
    print("="*60 + "\n")

    # 1. Resetar singleton para forçar nova conexão
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None

    # 2. Criar conexão (isso vai aplicar a migration automaticamente)
    print("[*] Inicializando conexao com banco de dados...")
    conn = SQLiteConnection("backlog.db")
    db = conn.get_connection()
    print()

    # 3. Verificar se tabela features foi criada
    print("[*] Verificando se tabela 'features' foi criada...")
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='features'")
    if cursor.fetchone():
        print("[OK] Tabela 'features' existe!")
    else:
        print("[ERRO] Tabela 'features' NAO foi criada!")
        return

    # 4. Verificar se coluna feature_id existe em stories
    print("\n[*] Verificando se coluna 'feature_id' foi adicionada em 'stories'...")
    cursor.execute("PRAGMA table_info(stories)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'feature_id' in columns:
        print("[OK] Coluna 'feature_id' existe em stories!")
    else:
        print("[ERRO] Coluna 'feature_id' NAO foi adicionada!")
        return

    # 5. Verificar feature padrão
    print("\n[*] Verificando feature padrao 'Backlog Inicial'...")
    cursor.execute("SELECT * FROM features WHERE id = 'feature_default'")
    feature = cursor.fetchone()
    if feature:
        print(f"[OK] Feature padrao encontrada:")
        print(f"   - ID: {feature['id']}")
        print(f"   - Nome: {feature['name']}")
        print(f"   - Onda: {feature['wave']}")
    else:
        print("[ERRO] Feature padrao NAO foi criada!")
        return

    # 6. Verificar histórias associadas à feature padrão
    print("\n[*] Verificando historias associadas a feature padrao...")
    cursor.execute("SELECT COUNT(*) as count FROM stories WHERE feature_id = 'feature_default'")
    count = cursor.fetchone()['count']
    print(f"[OK] {count} historias associadas a feature padrao")

    # 7. Verificar histórias sem feature_id
    cursor.execute("SELECT COUNT(*) as count FROM stories WHERE feature_id IS NULL")
    orphan_count = cursor.fetchone()['count']
    if orphan_count == 0:
        print("[OK] Nenhuma historia orfa (sem feature_id)")
    else:
        print(f"[AVISO] {orphan_count} historias sem feature_id!")

    # 8. Listar todas as features
    print("\n[*] Features cadastradas:")
    cursor.execute("SELECT * FROM features ORDER BY wave ASC")
    features = cursor.fetchall()
    if features:
        for f in features:
            cursor.execute("SELECT COUNT(*) as count FROM stories WHERE feature_id = ?", (f['id'],))
            story_count = cursor.fetchone()['count']
            print(f"   - {f['name']} (Onda {f['wave']}) - {story_count} historias")
    else:
        print("   (Nenhuma feature cadastrada)")

    # 9. Verificar constraints
    print("\n[*] Verificando constraints...")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='features'")
    features_sql = cursor.fetchone()['sql']
    if 'UNIQUE' in features_sql and 'wave' in features_sql:
        print("[OK] Constraint UNIQUE em 'wave' presente")
    else:
        print("[AVISO] Constraint UNIQUE em 'wave' pode estar ausente")

    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='stories'")
    stories_sql = cursor.fetchone()['sql']
    if 'FOREIGN KEY' in stories_sql and 'feature_id' in stories_sql:
        print("[OK] Foreign key 'feature_id' presente em stories")
    else:
        print("[AVISO] Foreign key 'feature_id' pode estar ausente")

    print("\n" + "="*60)
    print("[OK] MIGRATION 003 APLICADA COM SUCESSO!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERRO] Falha ao executar migration: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
