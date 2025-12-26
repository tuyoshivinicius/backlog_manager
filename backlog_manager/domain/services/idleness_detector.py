"""Serviço para detectar ociosidade de desenvolvedores."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING, Dict, List, Union

from backlog_manager.domain.entities.story import Story

if TYPE_CHECKING:
    from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator


@dataclass
class IdlenessWarning:
    """Representa um aviso de ociosidade dentro de uma onda (feature)."""
    developer_id: str
    gap_days: int
    story_before_id: str
    story_after_id: str
    idle_start: date
    idle_end: date
    wave: int  # Onda onde a ociosidade ocorreu

    def __str__(self) -> str:
        return (
            f"[Onda {self.wave}] Desenvolvedor {self.developer_id}: "
            f"{self.gap_days} dia(s) ocioso(s) entre {self.story_before_id} e {self.story_after_id} "
            f"({self.idle_start.strftime('%d/%m/%Y')} - {self.idle_end.strftime('%d/%m/%Y')})"
        )


@dataclass
class BetweenWavesIdlenessInfo:
    """Informação sobre ociosidade entre ondas (features) diferentes - é esperado e permitido."""
    developer_id: str
    gap_days: int
    story_before_id: str
    story_after_id: str
    idle_start: date
    idle_end: date
    wave_before: int
    wave_after: int

    def __str__(self) -> str:
        return (
            f"[Entre ondas {self.wave_before}→{self.wave_after}] Desenvolvedor {self.developer_id}: "
            f"{self.gap_days} dia(s) entre {self.story_before_id} e {self.story_after_id} "
            f"({self.idle_start.strftime('%d/%m/%Y')} - {self.idle_end.strftime('%d/%m/%Y')})"
        )


@dataclass
class DeadlockWarning:
    """Warning emitido quando o algoritmo detecta situação sem progresso."""
    wave: int
    unallocated_story_ids: List[str]
    message: str

    def __str__(self) -> str:
        return f"Deadlock na onda {self.wave}: {self.message}"


# Tipo união para warnings de alocação
AllocationWarning = Union[IdlenessWarning, BetweenWavesIdlenessInfo, DeadlockWarning]


class IdlenessDetector:
    """
    Serviço de domínio para detectar ociosidade de desenvolvedores.

    Identifica gaps de 1+ dias úteis entre histórias consecutivas
    do mesmo desenvolvedor DENTRO DA MESMA ONDA.

    Ociosidade entre ondas diferentes é esperada e não gera warnings,
    pois as ondas são processadas sequencialmente.

    Usa ScheduleCalculator para cálculos de dias úteis, garantindo
    consistência com feriados brasileiros em todo o sistema.
    """

    def __init__(self, schedule_calculator: ScheduleCalculator) -> None:
        """
        Inicializa detector de ociosidade.

        Args:
            schedule_calculator: Serviço para cálculo de dias úteis
        """
        self._schedule_calculator = schedule_calculator

    def detect_idleness(
        self,
        all_stories: List[Story],
        min_gap_days: int = 1
    ) -> List[IdlenessWarning]:
        """
        Detecta ociosidade de desenvolvedores DENTRO de cada onda.

        Gaps entre histórias de ondas diferentes NÃO são reportados,
        pois a ociosidade entre ondas é esperada e permitida.

        Args:
            all_stories: Lista de todas as histórias
            min_gap_days: Mínimo de dias para considerar gap (padrão: 1)

        Returns:
            Lista de warnings de ociosidade (apenas dentro de cada onda)
        """
        warnings: List[IdlenessWarning] = []

        # Agrupar histórias por desenvolvedor E onda
        stories_by_dev_wave = self._group_stories_by_developer_and_wave(all_stories)

        # Analisar cada desenvolvedor em cada onda separadamente
        for (dev_id, wave), dev_wave_stories in stories_by_dev_wave.items():
            # Ordenar por data de início (filtrar histórias sem datas)
            sorted_stories = sorted(
                [s for s in dev_wave_stories if s.start_date and s.end_date],
                key=lambda s: s.start_date  # type: ignore[return-value, arg-type]
            )

            # Detectar gaps entre histórias consecutivas DA MESMA ONDA
            for i in range(len(sorted_stories) - 1):
                story_before = sorted_stories[i]
                story_after = sorted_stories[i + 1]

                # Calcular gap em dias úteis usando ScheduleCalculator
                # (considera feriados brasileiros)
                gap = self._schedule_calculator.count_workdays_between(
                    story_before.end_date,  # type: ignore[arg-type]
                    story_after.start_date  # type: ignore[arg-type]
                )

                if gap >= min_gap_days:
                    warning = IdlenessWarning(
                        developer_id=dev_id,
                        gap_days=gap,
                        story_before_id=story_before.id,
                        story_after_id=story_after.id,
                        idle_start=story_before.end_date + timedelta(days=1),  # type: ignore[operator]
                        idle_end=story_after.start_date - timedelta(days=1),  # type: ignore[operator]
                        wave=wave,
                    )
                    warnings.append(warning)

        return warnings

    def detect_between_waves_idleness(
        self,
        all_stories: List[Story],
        min_gap_days: int = 1
    ) -> List[BetweenWavesIdlenessInfo]:
        """
        Detecta ociosidade de desenvolvedores ENTRE ondas diferentes.

        Esta ociosidade é esperada e permitida, mas é reportada como informação.

        Args:
            all_stories: Lista de todas as histórias
            min_gap_days: Mínimo de dias para considerar gap (padrão: 1)

        Returns:
            Lista de informações de ociosidade entre ondas
        """
        infos: List[BetweenWavesIdlenessInfo] = []

        # Agrupar histórias por desenvolvedor
        stories_by_dev = self._group_stories_by_developer(all_stories)

        # Analisar cada desenvolvedor
        for dev_id, dev_stories in stories_by_dev.items():
            # Ordenar por data de início (filtrar histórias sem datas)
            sorted_stories = sorted(
                [s for s in dev_stories if s.start_date and s.end_date],
                key=lambda s: s.start_date  # type: ignore[return-value, arg-type]
            )

            # Detectar gaps entre histórias de ONDAS DIFERENTES
            for i in range(len(sorted_stories) - 1):
                story_before = sorted_stories[i]
                story_after = sorted_stories[i + 1]

                # Só reportar se são de ondas diferentes
                if story_before.wave == story_after.wave:
                    continue  # Dentro da mesma onda - já coberto por detect_idleness

                # Calcular gap em dias úteis
                gap = self._schedule_calculator.count_workdays_between(
                    story_before.end_date,  # type: ignore[arg-type]
                    story_after.start_date  # type: ignore[arg-type]
                )

                if gap >= min_gap_days:
                    info = BetweenWavesIdlenessInfo(
                        developer_id=dev_id,
                        gap_days=gap,
                        story_before_id=story_before.id,
                        story_after_id=story_after.id,
                        idle_start=story_before.end_date + timedelta(days=1),  # type: ignore[operator]
                        idle_end=story_after.start_date - timedelta(days=1),  # type: ignore[operator]
                        wave_before=story_before.wave,
                        wave_after=story_after.wave,
                    )
                    infos.append(info)

        return infos

    def _group_stories_by_developer_and_wave(
        self,
        stories: List[Story]
    ) -> Dict[tuple, List[Story]]:
        """
        Agrupa histórias por desenvolvedor E onda.

        Args:
            stories: Lista de histórias

        Returns:
            Dicionário {(developer_id, wave): [histórias]}
        """
        grouped: Dict[tuple, List[Story]] = {}
        for story in stories:
            if story.developer_id:
                key = (story.developer_id, story.wave)
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(story)
        return grouped

    def _group_stories_by_developer(
        self,
        stories: List[Story]
    ) -> Dict[str, List[Story]]:
        """
        Agrupa histórias por desenvolvedor.

        Args:
            stories: Lista de histórias

        Returns:
            Dicionário {developer_id: [histórias]}
        """
        grouped: Dict[str, List[Story]] = {}
        for story in stories:
            if story.developer_id:
                if story.developer_id not in grouped:
                    grouped[story.developer_id] = []
                grouped[story.developer_id].append(story)
        return grouped
