"""Caso de uso para buscar desenvolvedor."""
import logging

from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.application.dto.converters import developer_to_dto
from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.domain.exceptions.domain_exceptions import DeveloperNotFoundException

logger = logging.getLogger(__name__)


class GetDeveloperUseCase:
    """
    Caso de uso para buscar desenvolvedor por ID.

    Responsabilidades:
    - Buscar desenvolvedor
    - Converter para DTO
    """

    def __init__(self, developer_repository: DeveloperRepository):
        """
        Inicializa caso de uso.

        Args:
            developer_repository: Repositório de desenvolvedores
        """
        self._developer_repository = developer_repository

    def execute(self, developer_id: str) -> DeveloperDTO:
        """
        Busca desenvolvedor por ID.

        Args:
            developer_id: ID do desenvolvedor

        Returns:
            DeveloperDTO encontrado

        Raises:
            DeveloperNotFoundException: Se desenvolvedor não existe
        """
        logger.debug(f"Buscando desenvolvedor: id='{developer_id}'")

        # 1. Buscar desenvolvedor
        developer = self._developer_repository.find_by_id(developer_id)

        if developer is None:
            logger.error(f"Desenvolvedor não encontrado: id='{developer_id}'")
            raise DeveloperNotFoundException(developer_id)

        logger.debug(f"Desenvolvedor encontrado: id='{developer_id}', name='{developer.name}'")

        # 2. Retornar DTO
        return developer_to_dto(developer)
