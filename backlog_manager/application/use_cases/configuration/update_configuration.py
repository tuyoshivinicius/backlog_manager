"""Caso de uso para atualizar configuração."""
from typing import Tuple

from backlog_manager.application.dto.configuration_dto import ConfigurationDTO
from backlog_manager.application.dto.converters import configuration_to_dto
from backlog_manager.application.interfaces.repositories.configuration_repository import ConfigurationRepository
from backlog_manager.domain.entities.configuration import Configuration


class UpdateConfigurationUseCase:
    """
    Caso de uso para atualizar configuração do sistema.

    Responsabilidades:
    - Validar novos valores
    - Atualizar configuração
    - Persistir
    - Indicar se requer recálculo de cronograma
    """

    def __init__(self, configuration_repository: ConfigurationRepository):
        """
        Inicializa caso de uso.

        Args:
            configuration_repository: Repositório de configuração
        """
        self._configuration_repository = configuration_repository

    def execute(
        self, story_points_per_sprint: int | None = None, workdays_per_sprint: int | None = None
    ) -> Tuple[ConfigurationDTO, bool]:
        """
        Atualiza configuração do sistema.

        Args:
            story_points_per_sprint: Nova velocidade (opcional)
            workdays_per_sprint: Novos dias úteis (opcional)

        Returns:
            Tupla (ConfigurationDTO atualizado, requer_recalculo: bool)

        Raises:
            ValueError: Se valores inválidos
        """
        # 1. Buscar configuração atual
        current = self._configuration_repository.get()

        # 2. Determinar novos valores
        new_sp = story_points_per_sprint if story_points_per_sprint is not None else current.story_points_per_sprint

        new_workdays = workdays_per_sprint if workdays_per_sprint is not None else current.workdays_per_sprint

        # 3. Verificar se houve mudança
        requires_recalculation = (
            new_sp != current.story_points_per_sprint or new_workdays != current.workdays_per_sprint
        )

        # 4. Criar nova configuração (validação acontece no __post_init__)
        new_config = Configuration(story_points_per_sprint=new_sp, workdays_per_sprint=new_workdays)

        # 5. Persistir
        self._configuration_repository.save(new_config)

        # 6. Retornar (DTO, flag_recalculo)
        return configuration_to_dto(new_config), requires_recalculation
