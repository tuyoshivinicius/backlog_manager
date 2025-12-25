"""Script para verificar violações de dependências após alocação."""
import sqlite3
from datetime import datetime

# Conectar ao banco
conn = sqlite3.connect('backlog.db')
cursor = conn.cursor()

# Buscar todas as histórias
cursor.execute("""
    SELECT id, start_date, end_date, dependencies
    FROM stories
    WHERE dependencies IS NOT NULL AND dependencies != '[]'
    ORDER BY id
""")

stories = cursor.fetchall()

# Criar dicionário de histórias para lookup rápido
story_dict = {}
cursor.execute("SELECT id, start_date, end_date, dependencies FROM stories")
for row in cursor.fetchall():
    story_dict[row[0]] = {
        'start_date': row[1],
        'end_date': row[2],
        'dependencies': row[3]
    }

print("=" * 80)
print("VERIFICAÇÃO DE DEPENDÊNCIAS")
print("=" * 80)

violations = []

for story_id, start_date, end_date, dependencies_json in stories:
    if not start_date:
        continue

    # Parse dependencies
    import json
    try:
        dependencies = json.loads(dependencies_json)
    except:
        continue

    if not dependencies:
        continue

    # Converter start_date para datetime
    story_start = datetime.fromisoformat(start_date).date()

    # Verificar cada dependência
    for dep_id in dependencies:
        if dep_id not in story_dict:
            print(f"⚠️  {story_id}: Dependência {dep_id} não encontrada!")
            continue

        dep_end = story_dict[dep_id]['end_date']
        if not dep_end:
            continue

        dep_end_date = datetime.fromisoformat(dep_end).date()

        # Verificar violação
        if story_start <= dep_end_date:
            violations.append({
                'story': story_id,
                'start': story_start,
                'dependency': dep_id,
                'dep_end': dep_end_date
            })
            print(f"❌ VIOLAÇÃO: {story_id} inicia {story_start} antes/com {dep_id} que termina {dep_end_date}")

print()
print("=" * 80)
print(f"Total de histórias: {len(story_dict)}")
print(f"Histórias com dependências: {len(stories)}")
print(f"Violações encontradas: {len(violations)}")
print("=" * 80)

if violations:
    print()
    print("RESUMO DAS VIOLAÇÕES:")
    for v in violations:
        days_diff = (v['dep_end'] - v['start']).days
        print(f"  {v['story']} inicia {days_diff} dias antes de {v['dependency']} terminar")
else:
    print()
    print("✅ NENHUMA VIOLAÇÃO ENCONTRADA!")

conn.close()
