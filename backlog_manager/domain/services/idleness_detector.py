"""Serviço para detectar ociosidade de desenvolvedores."""
from typing import List, Dict
from datetime import date, timedelta
from dataclasses import dataclass
from backlog_manager.domain.entities.story import Story


@dataclass
class IdlenessWarning:
    """Representa um aviso de ociosidade."""
    developer_id: str
    gap_days: int
    story_before_id: str
    story_after_id: str
    idle_start: date
    idle_end: date

    def __str__(self) -> str:
        return (
            f"Desenvolvedor {self.developer_id}: {self.gap_days} dia(s) ocioso(s) "
            f"entre {self.story_before_id} e {self.story_after_id} "
            f"({self.idle_start.strftime('%d/%m/%Y')} - {self.idle_end.strftime('%d/%m/%Y')})"
        )


class IdlenessDetector:
    """
    Serviço de domínio para detectar ociosidade de desenvolvedores.

    Identifica gaps de 1+ dias úteis entre histórias consecutivas
    do mesmo desenvolvedor.
    """

    @staticmethod
    def detect_idleness(
        all_stories: List[Story],
        min_gap_days: int = 1
    ) -> List[IdlenessWarning]:
        """
        Detecta ociosidade de desenvolvedores.

        Args:
            all_stories: Lista de todas as histórias
            min_gap_days: Mínimo de dias para considerar gap (padrão: 1)

        Returns:
            Lista de warnings de ociosidade
        """
        warnings = []

        # Agrupar histórias por desenvolvedor
        stories_by_dev = IdlenessDetector._group_stories_by_developer(all_stories)

        # Analisar cada desenvolvedor
        for dev_id, dev_stories in stories_by_dev.items():
            # Ordenar por data de início
            sorted_stories = sorted(
                [s for s in dev_stories if s.start_date and s.end_date],
                key=lambda s: s.start_date
            )

            # Detectar gaps entre histórias consecutivas
            for i in range(len(sorted_stories) - 1):
                story_before = sorted_stories[i]
                story_after = sorted_stories[i + 1]

                # Calcular gap em dias úteis
                gap = IdlenessDetector._calculate_workday_gap(
                    story_before.end_date,
                    story_after.start_date
                )

                if gap >= min_gap_days:
                    warning = IdlenessWarning(
                        developer_id=dev_id,
                        gap_days=gap,
                        story_before_id=story_before.id,
                        story_after_id=story_after.id,
                        idle_start=story_before.end_date + timedelta(days=1),
                        idle_end=story_after.start_date - timedelta(days=1)
                    )
                    warnings.append(warning)

        return warnings

    @staticmethod
    def _group_stories_by_developer(
        stories: List[Story]
    ) -> Dict[str, List[Story]]:
        """
        Agrupa histórias por desenvolvedor.

        Args:
            stories: Lista de histórias

        Returns:
            Dicionário {developer_id: [histórias]}
        """
        grouped = {}
        for story in stories:
            if story.developer_id:
                if story.developer_id not in grouped:
                    grouped[story.developer_id] = []
                grouped[story.developer_id].append(story)
        return grouped

    @staticmethod
    def _calculate_workday_gap(end_date: date, start_date: date) -> int:
        """
        Calcula gap em dias úteis entre duas datas.

        Args:
            end_date: Data fim da primeira história
            start_date: Data início da segunda história

        Returns:
            Número de dias úteis entre as datas (exclusivo)
        """
        if start_date <= end_date:
            return 0

        # Contar dias úteis entre end_date+1 e start_date-1
        current = end_date + timedelta(days=1)
        end = start_date
        workdays = 0

        while current < end:
            if current.weekday() < 5:  # 0-4 = seg-sex
                workdays += 1
            current += timedelta(days=1)

        return workdays
