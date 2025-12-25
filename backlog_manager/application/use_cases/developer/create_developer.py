"""Caso de uso para criar desenvolvedor."""
import logging

from backlog_manager.application.dto.converters import developer_to_dto
from backlog_manager.application.dto.developer_dto import DeveloperDTO
from backlog_manager.application.interfaces.repositories.developer_repository import DeveloperRepository
from backlog_manager.domain.entities.developer import Developer

logger = logging.getLogger(__name__)


class CreateDeveloperUseCase:
    """
    Caso de uso para criar novo desenvolvedor.

    Responsabilidades:
    - Validar nome
    - Gerar ID automático (2 primeiras letras maiúsculas)
    - Resolver conflitos de ID (JO → JO2 → JO3)
    - Criar e persistir desenvolvedor
    """

    def __init__(self, developer_repository: DeveloperRepository):
        """
        Inicializa caso de uso.

        Args:
            developer_repository: Repositório de desenvolvedores
        """
        self._developer_repository = developer_repository

    def execute(self, name: str) -> DeveloperDTO:
        """
        Cria novo desenvolvedor.

        Args:
            name: Nome do desenvolvedor (min 2 caracteres)

        Returns:
            DeveloperDTO criado

        Raises:
            ValueError: Se nome inválido
        """
        logger.info(f"Iniciando criação de desenvolvedor: name='{name}'")

        # 1. Validar nome
        if not name or len(name.strip()) < 2:
            logger.error(f"Nome inválido: '{name}' (mínimo 2 caracteres)")
            raise ValueError("Nome deve ter pelo menos 2 caracteres")

        name = name.strip()
        logger.debug(f"Nome validado: '{name}'")

        # 2. Gerar ID base (2 primeiras letras maiúsculas)
        base_id = name[:2].upper()
        logger.debug(f"ID base gerado: '{base_id}'")

        # 3. Resolver conflitos
        developer_id = base_id
        counter = 2

        while not self._developer_repository.id_is_available(developer_id):
            developer_id = f"{base_id}{counter}"
            counter += 1

        logger.debug(f"ID final: '{developer_id}'")

        # 4. Criar entidade
        developer = Developer(id=developer_id, name=name)

        # 5. Persistir
        self._developer_repository.save(developer)
        logger.info(f"Desenvolvedor criado: id='{developer_id}', name='{name}'")

        return developer_to_dto(developer)
