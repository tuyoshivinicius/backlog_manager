"""Caso de uso para listar desenvolvedores."""
import logging
from typing import List

from backlog_manager.application.dto.converters import developer_to_dto
from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository

logger = logging.getLogger(__name__)


class ListDevelopersUseCase:
    """
    Caso de uso para listar todos os desenvolvedores.

    Responsabilidades:
    - Buscar todos desenvolvedores
    - Ordenar por nome
    - Converter para DTOs
    """

    def __init__(self, developer_repository: DeveloperRepository):
        """
        Inicializa caso de uso.

        Args:
            developer_repository: Repositório de desenvolvedores
        """
        self._developer_repository = developer_repository

    def execute(self) -> List[DeveloperDTO]:
        """
        Retorna todos os desenvolvedores ordenados por nome.

        Returns:
            Lista de DeveloperDTO ordenada alfabeticamente
        """
        logger.debug("Listando todos os desenvolvedores")

        # 1. Buscar todos
        developers = self._developer_repository.find_all()
        logger.debug(f"Encontrados {len(developers)} desenvolvedores")

        # 2. Ordenar por nome
        developers.sort(key=lambda d: d.name.lower())

        # 3. Converter para DTOs
        return [developer_to_dto(dev) for dev in developers]
