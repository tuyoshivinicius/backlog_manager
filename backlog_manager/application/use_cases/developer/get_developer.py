"""Caso de uso para buscar desenvolvedor."""
from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.application.dto.converters import developer_to_dto
from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.domain.exceptions.domain_exceptions import DeveloperNotFoundException


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
        # 1. Buscar desenvolvedor
        developer = self._developer_repository.find_by_id(developer_id)

        if developer is None:
            raise DeveloperNotFoundException(developer_id)

        # 2. Retornar DTO
        return developer_to_dto(developer)
