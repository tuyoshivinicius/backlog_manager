"""Script para verificar o banco de dados."""
import sqlite3

db_path = "backlog.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print("VERIFICAÇÃO DO BANCO DE DADOS")
    print(f"{'='*60}")

    # Verificar quantas histórias existem
    cursor.execute("SELECT COUNT(*) FROM stories")
    count = cursor.fetchone()[0]
    print(f"\nTotal de histórias no banco: {count}")

    # Listar todas as histórias
    cursor.execute("SELECT id, feature, name, status, priority FROM stories ORDER BY priority")
    stories = cursor.fetchall()

    if stories:
        print("\nHistórias encontradas:")
        for story in stories:
            print(f"  - {story[0]}: {story[2]} (Feature: {story[1]}, Status: {story[3]}, Prioridade: {story[4]})")
    else:
        print("\nNenhuma história encontrada no banco.")

    conn.close()
    print(f"\n{'='*60}\n")

except Exception as e:
    print(f"\nErro ao verificar banco: {type(e).__name__}: {e}\n")
