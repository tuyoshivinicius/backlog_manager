"""
Script de análise completa da funcionalidade de alocação de desenvolvedores.

Verifica:
1. Violações de dependência
2. Conflitos de período (sobreposição)
3. Violações de max_idle_days
4. Balanceamento de carga
5. Métricas gerais
"""

import os
import sys
from datetime import date
from collections import defaultdict

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection
from backlog_manager.infrastructure.database.unit_of_work import UnitOfWork
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator


def analyze_allocation():
    """Executa análise completa da alocação."""
    print("=" * 80)
    print("ANÁLISE COMPLETA DA ALOCAÇÃO DE DESENVOLVEDORES")
    print("=" * 80)

    # Conectar ao banco de dados
    db_path = os.path.join(os.path.dirname(__file__), "backlog.db")

    # Resetar singleton para usar o banco correto
    SQLiteConnection._instance = None
    SQLiteConnection._connection = None

    with UnitOfWork(db_path) as uow:
        stories = uow.stories.find_all()
        developers = uow.developers.find_all()
        config = uow.configuration.get()

        # Carregar features
        for story in stories:
            uow.stories.load_feature(story)

    # Criar mapa de histórias
    story_map = {s.id: s for s in stories}

    # Instanciar calculadora de cronograma
    schedule_calculator = ScheduleCalculator()

    print(f"\n[INFO] Total de histórias: {len(stories)}")
    print(f"[INFO] Total de desenvolvedores: {len(developers)}")
    print(f"[INFO] max_idle_days configurado: {config.max_idle_days}")
    print(f"[INFO] Critério de alocação: {config.allocation_criteria.value}")

    # 1. ANÁLISE DE VIOLAÇÕES DE DEPENDÊNCIA
    print("\n" + "=" * 80)
    print("1. ANÁLISE DE VIOLAÇÕES DE DEPENDÊNCIA")
    print("=" * 80)

    dep_violations = []
    for story in stories:
        if not story.dependencies or not story.start_date:
            continue

        for dep_id in story.dependencies:
            dep_story = story_map.get(dep_id)
            if dep_story and dep_story.end_date:
                if story.start_date <= dep_story.end_date:
                    dep_violations.append({
                        'story': story.id,
                        'story_start': story.start_date,
                        'dependency': dep_id,
                        'dep_end': dep_story.end_date,
                        'gap_days': (dep_story.end_date - story.start_date).days
                    })

    if dep_violations:
        print(f"\n[ERRO] {len(dep_violations)} violações de dependência encontradas:")
        for v in dep_violations:
            print(f"  - {v['story']} inicia em {v['story_start']} mas {v['dependency']} termina em {v['dep_end']} (gap: {v['gap_days']} dias)")
    else:
        print("\n[OK] Nenhuma violação de dependência encontrada!")

    # 2. ANÁLISE DE CONFLITOS DE PERÍODO
    print("\n" + "=" * 80)
    print("2. ANÁLISE DE CONFLITOS DE PERÍODO (SOBREPOSIÇÃO)")
    print("=" * 80)

    conflicts = []
    dev_stories = defaultdict(list)

    for story in stories:
        if story.developer_id and story.start_date and story.end_date:
            dev_stories[story.developer_id].append(story)

    for dev_id, dev_story_list in dev_stories.items():
        # Ordenar por data de início
        sorted_stories = sorted(dev_story_list, key=lambda s: s.start_date)

        for i in range(len(sorted_stories) - 1):
            current = sorted_stories[i]
            next_s = sorted_stories[i + 1]

            # Verificar sobreposição
            if current.end_date >= next_s.start_date:
                conflicts.append({
                    'developer': dev_id,
                    'story1': current.id,
                    'story1_period': f"{current.start_date} a {current.end_date}",
                    'story2': next_s.id,
                    'story2_period': f"{next_s.start_date} a {next_s.end_date}",
                    'overlap_days': (current.end_date - next_s.start_date).days + 1
                })

    if conflicts:
        print(f"\n[ERRO] {len(conflicts)} conflitos de período encontrados:")
        for c in conflicts:
            print(f"  - Dev {c['developer']}: {c['story1']} ({c['story1_period']}) sobrepõe {c['story2']} ({c['story2_period']}) por {c['overlap_days']} dias")
    else:
        print("\n[OK] Nenhum conflito de período encontrado!")

    # 3. ANÁLISE DE VIOLAÇÕES DE MAX_IDLE_DAYS
    print("\n" + "=" * 80)
    print("3. ANÁLISE DE VIOLAÇÕES DE MAX_IDLE_DAYS")
    print("=" * 80)

    idle_violations = []
    max_idle_days = config.max_idle_days

    if max_idle_days:
        for dev_id, dev_story_list in dev_stories.items():
            sorted_stories = sorted(dev_story_list, key=lambda s: s.start_date)

            for i in range(len(sorted_stories) - 1):
                current = sorted_stories[i]
                next_s = sorted_stories[i + 1]

                # Verificar se estão na mesma onda
                if current.wave != next_s.wave:
                    continue  # Ociosidade entre ondas é permitida

                # Calcular dias ociosos
                idle_days = schedule_calculator.count_workdays_between(
                    current.end_date, next_s.start_date
                )

                if idle_days > max_idle_days:
                    idle_violations.append({
                        'developer': dev_id,
                        'wave': current.wave,
                        'story1': current.id,
                        'story1_end': current.end_date,
                        'story2': next_s.id,
                        'story2_start': next_s.start_date,
                        'idle_days': idle_days,
                        'max_allowed': max_idle_days
                    })

        if idle_violations:
            print(f"\n[AVISO] {len(idle_violations)} violações de max_idle_days encontradas:")
            for v in idle_violations:
                print(f"  - Dev {v['developer']} (Onda {v['wave']}): {v['idle_days']} dias ociosos entre {v['story1']} ({v['story1_end']}) e {v['story2']} ({v['story2_start']}) - máx permitido: {v['max_allowed']}")
        else:
            print(f"\n[OK] Nenhuma violação de max_idle_days ({max_idle_days} dias) encontrada!")
    else:
        print("\n[INFO] max_idle_days não configurado - verificação ignorada")

    # 4. ANÁLISE DE BALANCEAMENTO DE CARGA
    print("\n" + "=" * 80)
    print("4. ANÁLISE DE BALANCEAMENTO DE CARGA")
    print("=" * 80)

    dev_load = defaultdict(lambda: {'stories': 0, 'points': 0, 'days': 0})

    for story in stories:
        if story.developer_id:
            dev_load[story.developer_id]['stories'] += 1
            dev_load[story.developer_id]['points'] += story.story_point.value if story.story_point else 0
            dev_load[story.developer_id]['days'] += story.duration if story.duration else 0

    print("\nDistribuição de carga por desenvolvedor:")
    print("-" * 60)
    print(f"{'Desenvolvedor':<15} {'Histórias':>10} {'Story Points':>15} {'Dias':>10}")
    print("-" * 60)

    total_stories = 0
    total_points = 0
    total_days = 0

    for dev in developers:
        load = dev_load.get(dev.id, {'stories': 0, 'points': 0, 'days': 0})
        print(f"{dev.name:<15} {load['stories']:>10} {load['points']:>15} {load['days']:>10}")
        total_stories += load['stories']
        total_points += load['points']
        total_days += load['days']

    print("-" * 60)
    print(f"{'TOTAL':<15} {total_stories:>10} {total_points:>15} {total_days:>10}")

    # Calcular desvio padrão para avaliar balanceamento
    if len(developers) > 0:
        avg_points = total_points / len(developers)
        variance = sum((dev_load.get(d.id, {'points': 0})['points'] - avg_points) ** 2 for d in developers) / len(developers)
        std_dev = variance ** 0.5

        print(f"\n[INFO] Média de story points por dev: {avg_points:.1f}")
        print(f"[INFO] Desvio padrão: {std_dev:.1f}")

        if std_dev / avg_points < 0.2 if avg_points > 0 else True:
            print("[OK] Carga bem balanceada (desvio < 20% da média)")
        else:
            print("[AVISO] Carga desbalanceada (desvio >= 20% da média)")

    # 5. MÉTRICAS GERAIS
    print("\n" + "=" * 80)
    print("5. MÉTRICAS GERAIS")
    print("=" * 80)

    allocated = sum(1 for s in stories if s.developer_id)
    unallocated = sum(1 for s in stories if not s.developer_id)

    if len(stories) > 0:
        print(f"\nHistórias alocadas: {allocated} ({100*allocated/len(stories):.1f}%)")
        print(f"Histórias não alocadas: {unallocated} ({100*unallocated/len(stories):.1f}%)")
    else:
        print("\n[INFO] Nenhuma história encontrada no banco de dados")

    if unallocated > 0:
        print("\nHistórias não alocadas:")
        for s in stories:
            if not s.developer_id:
                print(f"  - {s.id} (Onda {s.wave}, {s.story_point.value if s.story_point else '?'} pts)")

    # Análise por onda
    print("\nDistribuição por onda:")
    wave_stats = defaultdict(lambda: {'total': 0, 'allocated': 0})
    for s in stories:
        if s.wave:
            wave_stats[s.wave]['total'] += 1
            if s.developer_id:
                wave_stats[s.wave]['allocated'] += 1

    for wave in sorted(wave_stats.keys()):
        stats = wave_stats[wave]
        print(f"  Onda {wave}: {stats['allocated']}/{stats['total']} alocadas")

    # Data de início e fim do roadmap
    dates = [s.start_date for s in stories if s.start_date]
    end_dates = [s.end_date for s in stories if s.end_date]

    if dates:
        print(f"\nPeríodo do roadmap:")
        print(f"  Início: {min(dates)}")
        print(f"  Fim: {max(end_dates)}")
        print(f"  Duração total: {(max(end_dates) - min(dates)).days + 1} dias")

    # 6. RESUMO FINAL
    print("\n" + "=" * 80)
    print("6. RESUMO FINAL")
    print("=" * 80)

    issues = []
    if dep_violations:
        issues.append(f"{len(dep_violations)} violações de dependência")
    if conflicts:
        issues.append(f"{len(conflicts)} conflitos de período")
    if idle_violations:
        issues.append(f"{len(idle_violations)} violações de max_idle_days")
    if unallocated > 0:
        issues.append(f"{unallocated} histórias não alocadas")

    if issues:
        print(f"\n[ATENÇÃO] Problemas encontrados:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n[SUCESSO] Nenhum problema encontrado na alocação!")

    print("\n" + "=" * 80)

    return {
        'dep_violations': len(dep_violations),
        'conflicts': len(conflicts),
        'idle_violations': len(idle_violations),
        'unallocated': unallocated,
        'total_stories': len(stories),
        'allocated': allocated
    }


if __name__ == "__main__":
    results = analyze_allocation()
