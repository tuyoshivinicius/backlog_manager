"""Caso de uso para atualizar desenvolvedor."""
import logging

from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.application.dto.converters import developer_to_dto
from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.domain.exceptions.domain_exceptions import DeveloperNotFoundException

logger = logging.getLogger(__name__)


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
        logger.info(f"Atualizando desenvolvedor: id='{developer_id}'")
        logger.debug(f"Novo nome: '{name}'")

        # 1. Buscar desenvolvedor
        developer = self._developer_repository.find_by_id(developer_id)

        if developer is None:
            logger.error(f"Desenvolvedor não encontrado: id='{developer_id}'")
            raise DeveloperNotFoundException(developer_id)

        # 2. Atualizar campos
        if name is not None:
            old_name = developer.name
            developer.update_name(name)
            logger.debug(f"Nome atualizado: '{old_name}' -> '{name}'")

        # 3. Persistir
        self._developer_repository.save(developer)
        logger.info(f"Desenvolvedor atualizado: id='{developer_id}', name='{developer.name}'")

        # 4. Retornar DTO
        return developer_to_dto(developer)
