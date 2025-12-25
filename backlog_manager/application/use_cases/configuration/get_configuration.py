"""Caso de uso para buscar configuração."""
import logging

from backlog_manager.application.dto.configuration_dto import ConfigurationDTO
from backlog_manager.application.dto.converters import configuration_to_dto
from backlog_manager.application.interfaces.repositories.configuration_repository import ConfigurationRepository

logger = logging.getLogger(__name__)


class GetConfigurationUseCase:
    """
    Caso de uso para buscar configuração do sistema.

    Responsabilidades:
    - Buscar configuração (retorna defaults se não existe)
    - Converter para DTO
    """

    def __init__(self, configuration_repository: ConfigurationRepository):
        """
        Inicializa caso de uso.

        Args:
            configuration_repository: Repositório de configuração
        """
        self._configuration_repository = configuration_repository

    def execute(self) -> ConfigurationDTO:
        """
        Retorna configuração do sistema.

        Returns:
            ConfigurationDTO com configuração atual
        """
        logger.debug("Buscando configuração do sistema")

        config = self._configuration_repository.get()

        logger.debug(
            f"Configuração: story_points_per_sprint={config.story_points_per_sprint}, "
            f"workdays_per_sprint={config.workdays_per_sprint}, "
            f"roadmap_start_date={config.roadmap_start_date}"
        )

        return configuration_to_dto(config)
