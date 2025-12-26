"""Caso de uso para atualizar configuração."""
import logging
from datetime import date
from typing import Optional, Tuple

from backlog_manager.application.dto.configuration_dto import ConfigurationDTO
from backlog_manager.application.dto.converters import configuration_to_dto
from backlog_manager.application.interfaces.repositories.configuration_repository import ConfigurationRepository
from backlog_manager.domain.entities.configuration import Configuration
from backlog_manager.domain.value_objects.allocation_criteria import AllocationCriteria

logger = logging.getLogger(__name__)


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
        allocation_criteria: Optional[str] = None,
        max_idle_days: Optional[int] = None,
    ) -> Tuple[ConfigurationDTO, bool]:
        """
        Atualiza configuração do sistema.

        Args:
            story_points_per_sprint: Nova velocidade (obrigatório)
            workdays_per_sprint: Novos dias úteis (obrigatório)
            roadmap_start_date: Nova data de início do roadmap (opcional, None para limpar)
            allocation_criteria: Critério de alocação (opcional, None mantém o atual)
            max_idle_days: Máximo de dias úteis ociosos (opcional, None mantém o atual)

        Returns:
            Tupla (ConfigurationDTO atualizado, requer_recalculo: bool)

        Raises:
            ValueError: Se valores inválidos (ex: data em fim de semana)
        """
        logger.info(
            f"Atualizando configuração: story_points_per_sprint={story_points_per_sprint}, "
            f"workdays_per_sprint={workdays_per_sprint}, roadmap_start_date={roadmap_start_date}, "
            f"allocation_criteria={allocation_criteria}, max_idle_days={max_idle_days}"
        )

        # 1. Buscar configuração atual
        current = self._configuration_repository.get()
        logger.debug(
            f"Configuração atual: story_points_per_sprint={current.story_points_per_sprint}, "
            f"workdays_per_sprint={current.workdays_per_sprint}, "
            f"roadmap_start_date={current.roadmap_start_date}, "
            f"allocation_criteria={current.allocation_criteria.value}, "
            f"max_idle_days={current.max_idle_days}"
        )

        # Converter allocation_criteria de string para enum (se fornecido)
        if allocation_criteria is not None:
            try:
                new_allocation_criteria = AllocationCriteria.from_string(allocation_criteria)
            except ValueError:
                logger.warning(
                    f"Critério de alocação inválido: {allocation_criteria}. "
                    "Mantendo o valor atual."
                )
                new_allocation_criteria = current.allocation_criteria
        else:
            new_allocation_criteria = current.allocation_criteria

        # Usar max_idle_days atual se não fornecido
        new_max_idle_days = max_idle_days if max_idle_days is not None else current.max_idle_days

        # 2. Verificar se houve mudança (que afeta cronograma)
        requires_recalculation = (
            story_points_per_sprint != current.story_points_per_sprint
            or workdays_per_sprint != current.workdays_per_sprint
            or roadmap_start_date != current.roadmap_start_date
        )

        if requires_recalculation:
            logger.info("Mudanças detectadas - recálculo de cronograma será necessário")
        else:
            logger.debug("Nenhuma mudança detectada - recálculo não necessário")

        # 3. Criar nova configuração (validação acontece no __post_init__)
        new_config = Configuration(
            story_points_per_sprint=story_points_per_sprint,
            workdays_per_sprint=workdays_per_sprint,
            roadmap_start_date=roadmap_start_date,
            allocation_criteria=new_allocation_criteria,
            max_idle_days=new_max_idle_days,
        )
        logger.debug("Nova configuração validada")

        # 4. Persistir
        self._configuration_repository.save(new_config)
        logger.info(
            f"Configuração atualizada: velocity={new_config.velocity_per_day:.2f} pts/dia, "
            f"allocation_criteria={new_config.allocation_criteria.value}, "
            f"max_idle_days={new_config.max_idle_days}, "
            f"requer_recalculo={requires_recalculation}"
        )

        # 5. Retornar (DTO, flag_recalculo)
        return configuration_to_dto(new_config), requires_recalculation
