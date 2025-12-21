"""Utilitário para destacar células temporariamente."""
from typing import List, Dict
from PySide6.QtWidgets import QTableWidget
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QBrush


class CellHighlighter:
    """
    Utilitário para destacar células da tabela temporariamente.

    Permite criar efeitos visuais como flash vermelho para indicar
    conflitos ou erros, sem bloquear a interface.

    Example:
        >>> table = QTableWidget()
        >>> CellHighlighter.highlight_cells(
        ...     table=table,
        ...     rows=[0, 1, 2],
        ...     column=5,
        ...     color=QColor(255, 0, 0, 128),
        ...     duration_ms=2000
        ... )
    """

    @staticmethod
    def highlight_cells(
        table: QTableWidget,
        rows: List[int],
        column: int,
        color: QColor = None,
        duration_ms: int = 2000
    ) -> None:
        """
        Destaca células temporariamente.

        Args:
            table: Tabela contendo as células
            rows: Lista de índices de linhas a destacar
            column: Índice da coluna
            color: Cor do highlight (padrão: vermelho 50% transparente)
            duration_ms: Duração em milissegundos (padrão: 2000ms)

        Example:
            >>> # Destacar células das linhas 0, 1 e 5 na coluna 3
            >>> CellHighlighter.highlight_cells(table, [0, 1, 5], 3)
        """
        if color is None:
            color = QColor(255, 0, 0, 128)  # Vermelho 50% transparente

        # Armazenar cores originais
        original_colors: Dict[int, QBrush] = {}
        for row in rows:
            item = table.item(row, column)
            if item:
                original_colors[row] = item.background()
                item.setBackground(color)

        # Restaurar cores após duração
        QTimer.singleShot(
            duration_ms,
            lambda: CellHighlighter._restore_colors(
                table, original_colors, column
            )
        )

    @staticmethod
    def _restore_colors(
        table: QTableWidget,
        original_colors: Dict[int, QBrush],
        column: int
    ) -> None:
        """
        Restaura cores originais das células.

        Args:
            table: Tabela
            original_colors: Dict {row: QBrush}
            column: Coluna
        """
        for row, brush in original_colors.items():
            item = table.item(row, column)
            if item:
                item.setBackground(brush)

    @staticmethod
    def flash_cell(
        table: QTableWidget,
        row: int,
        column: int,
        error: bool = True,
        duration_ms: int = 2000
    ) -> None:
        """
        Flash rápido em uma célula única.

        Args:
            table: Tabela
            row: Linha
            column: Coluna
            error: Se True usa vermelho, se False usa amarelo
            duration_ms: Duração

        Example:
            >>> # Flash vermelho de erro na célula (2, 5)
            >>> CellHighlighter.flash_cell(table, 2, 5, error=True)
            >>> # Flash amarelo de aviso na célula (3, 1)
            >>> CellHighlighter.flash_cell(table, 3, 1, error=False)
        """
        color = QColor(255, 0, 0, 128) if error else QColor(255, 255, 0, 128)
        CellHighlighter.highlight_cells(table, [row], column, color, duration_ms)

    @staticmethod
    def flash_error(
        table: QTableWidget,
        rows: List[int],
        column: int,
        duration_ms: int = 2000
    ) -> None:
        """
        Flash vermelho de erro em múltiplas células.

        Atalho para highlight_cells com cor vermelha.

        Args:
            table: Tabela
            rows: Linhas a destacar
            column: Coluna
            duration_ms: Duração
        """
        CellHighlighter.highlight_cells(
            table, rows, column,
            QColor(255, 0, 0, 128),
            duration_ms
        )

    @staticmethod
    def flash_warning(
        table: QTableWidget,
        rows: List[int],
        column: int,
        duration_ms: int = 2000
    ) -> None:
        """
        Flash amarelo de aviso em múltiplas células.

        Args:
            table: Tabela
            rows: Linhas a destacar
            column: Coluna
            duration_ms: Duração
        """
        CellHighlighter.highlight_cells(
            table, rows, column,
            QColor(255, 255, 0, 128),
            duration_ms
        )

    @staticmethod
    def flash_success(
        table: QTableWidget,
        rows: List[int],
        column: int,
        duration_ms: int = 1000
    ) -> None:
        """
        Flash verde de sucesso em múltiplas células.

        Args:
            table: Tabela
            rows: Linhas a destacar
            column: Coluna
            duration_ms: Duração (padrão mais curto: 1s)
        """
        CellHighlighter.highlight_cells(
            table, rows, column,
            QColor(0, 255, 0, 128),
            duration_ms
        )
