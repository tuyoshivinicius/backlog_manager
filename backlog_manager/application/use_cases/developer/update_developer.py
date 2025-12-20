"""Caso de uso para atualizar desenvolvedor."""
from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.application.dto.converters import developer_to_dto
from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.domain.exceptions.domain_exceptions import DeveloperNotFoundException


class UpdateDeveloperUseCase:
    """
    Caso de uso para atualizar dados de um desenvolvedor.

    Responsabilidades:
    - Verificar que desenvolvedor existe
    - Atualizar campos permitidos (ex: nome)
    - Persistir
    """

    def __init__(self, developer_repository: DeveloperRepository):
        """
        Inicializa caso de uso.

        Args:
            developer_repository: Repositório de desenvolvedores
        """
        self._developer_repository = developer_repository

    def execute(self, developer_id: str, name: str | None = None) -> DeveloperDTO:
        """
        Atualiza dados do desenvolvedor.

        Args:
            developer_id: ID do desenvolvedor
            name: Novo nome (opcional)

        Returns:
            DeveloperDTO atualizado

        Raises:
            DeveloperNotFoundException: Se desenvolvedor não existe
            ValueError: Se nome inválido
        """
        # 1. Buscar desenvolvedor
        developer = self._developer_repository.find_by_id(developer_id)

        if developer is None:
            raise DeveloperNotFoundException(developer_id)

        # 2. Atualizar campos
        if name is not None:
            developer.update_name(name)

        # 3. Persistir
        self._developer_repository.save(developer)

        # 4. Retornar DTO
        return developer_to_dto(developer)
