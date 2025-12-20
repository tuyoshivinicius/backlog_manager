"""
Constantes de cores e temas visuais da aplicação.

Define a paleta de cores e estilos usados em toda a interface.
"""
from typing import Dict


class AppColors:
    """Cores principais da aplicação."""

    # Cores primárias
    PRIMARY = "#2196F3"  # Azul
    PRIMARY_LIGHT = "#64B5F6"
    PRIMARY_DARK = "#1976D2"

    # Cores secundárias
    SECONDARY = "#4CAF50"  # Verde
    SECONDARY_LIGHT = "#81C784"
    SECONDARY_DARK = "#388E3C"

    # Cores de status
    SUCCESS = "#4CAF50"  # Verde
    ERROR = "#F44336"  # Vermelho
    WARNING = "#FF9800"  # Laranja
    INFO = "#2196F3"  # Azul

    # Cores de background
    BACKGROUND = "#FAFAFA"  # Cinza muito claro
    BACKGROUND_DARK = "#F5F5F5"
    SURFACE = "#FFFFFF"  # Branco

    # Cores de texto
    TEXT_PRIMARY = "#212121"  # Preto quase
    TEXT_SECONDARY = "#757575"  # Cinza
    TEXT_DISABLED = "#BDBDBD"  # Cinza claro

    # Cores de borda
    BORDER = "#E0E0E0"
    BORDER_FOCUS = "#2196F3"

    # Cores de status de história
    STATUS_BACKLOG = "#2196F3"  # Azul
    STATUS_EXECUCAO = "#FF9800"  # Laranja
    STATUS_TESTES = "#9C27B0"  # Roxo
    STATUS_CONCLUIDO = "#4CAF50"  # Verde
    STATUS_IMPEDIDO = "#F44336"  # Vermelho


class StatusColors:
    """Mapeamento de cores por status de história."""

    COLORS: Dict[str, str] = {
        "BACKLOG": AppColors.STATUS_BACKLOG,
        "EXECUCAO": AppColors.STATUS_EXECUCAO,
        "TESTES": AppColors.STATUS_TESTES,
        "CONCLUIDO": AppColors.STATUS_CONCLUIDO,
        "IMPEDIDO": AppColors.STATUS_IMPEDIDO,
    }

    @classmethod
    def get_color(cls, status: str) -> str:
        """
        Retorna a cor associada a um status.

        Args:
            status: Status da história

        Returns:
            Código hexadecimal da cor
        """
        return cls.COLORS.get(status, AppColors.TEXT_SECONDARY)
