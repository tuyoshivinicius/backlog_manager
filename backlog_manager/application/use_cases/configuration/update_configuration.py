"""Caso de uso para atualizar configuração."""
from datetime import date
from typing import Optional, Tuple

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
        self,
        story_points_per_sprint: int,
        workdays_per_sprint: int,
        roadmap_start_date: Optional[date] = None,
    ) -> Tuple[ConfigurationDTO, bool]:
        """
        Atualiza configuração do sistema.

        Args:
            story_points_per_sprint: Nova velocidade (obrigatório)
            workdays_per_sprint: Novos dias úteis (obrigatório)
            roadmap_start_date: Nova data de início do roadmap (opcional, None para limpar)

        Returns:
            Tupla (ConfigurationDTO atualizado, requer_recalculo: bool)

        Raises:
            ValueError: Se valores inválidos (ex: data em fim de semana)
        """
        # 1. Buscar configuração atual
        current = self._configuration_repository.get()

        # 2. Verificar se houve mudança
        requires_recalculation = (
            story_points_per_sprint != current.story_points_per_sprint
            or workdays_per_sprint != current.workdays_per_sprint
            or roadmap_start_date != current.roadmap_start_date
        )

        # 3. Criar nova configuração (validação acontece no __post_init__)
        new_config = Configuration(
            story_points_per_sprint=story_points_per_sprint,
            workdays_per_sprint=workdays_per_sprint,
            roadmap_start_date=roadmap_start_date,
        )

        # 4. Persistir
        self._configuration_repository.save(new_config)

        # 5. Retornar (DTO, flag_recalculo)
        return configuration_to_dto(new_config), requires_recalculation
