"""
Container de Injeção de Dependências.

Centraliza a criação e configuração de todos os componentes da aplicação.
"""
from backlog_manager.domain.services.cycle_detector import CycleDetector
from backlog_manager.domain.services.backlog_sorter import BacklogSorter
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator
from backlog_manager.domain.services.allocation_validator import AllocationValidator
from backlog_manager.domain.services.developer_load_balancer import DeveloperLoadBalancer
from backlog_manager.domain.services.idleness_detector import IdlenessDetector
from backlog_manager.domain.services.wave_dependency_validator import WaveDependencyValidator

from backlog_manager.infrastructure.database.sqlite_connection import SQLiteConnection
from backlog_manager.infrastructure.database.repositories.sqlite_story_repository import (
    SQLiteStoryRepository,
)
from backlog_manager.infrastructure.database.repositories.sqlite_developer_repository import (
    SQLiteDeveloperRepository,
)
from backlog_manager.infrastructure.database.repositories.sqlite_configuration_repository import (
    SQLiteConfigurationRepository,
)
from backlog_manager.infrastructure.database.repositories.sqlite_feature_repository import (
    SQLiteFeatureRepository,
)
from backlog_manager.infrastructure.excel.openpyxl_excel_service import (
    OpenpyxlExcelService,
)

from backlog_manager.application.use_cases.story.create_story import CreateStoryUseCase
from backlog_manager.application.use_cases.story.update_story import UpdateStoryUseCase
from backlog_manager.application.use_cases.story.delete_story import DeleteStoryUseCase
from backlog_manager.application.use_cases.story.get_story import GetStoryUseCase
from backlog_manager.application.use_cases.story.list_stories import ListStoriesUseCase
from backlog_manager.application.use_cases.story.duplicate_story import (
    DuplicateStoryUseCase,
)
from backlog_manager.application.use_cases.story.change_priority import (
    ChangePriorityUseCase,
)
from backlog_manager.application.use_cases.story.validate_developer_allocation import (
    ValidateDeveloperAllocationUseCase,
)

from backlog_manager.application.use_cases.developer.create_developer import (
    CreateDeveloperUseCase,
)
from backlog_manager.application.use_cases.developer.update_developer import (
    UpdateDeveloperUseCase,
)
from backlog_manager.application.use_cases.developer.delete_developer import (
    DeleteDeveloperUseCase,
)
from backlog_manager.application.use_cases.developer.get_developer import (
    GetDeveloperUseCase,
)
from backlog_manager.application.use_cases.developer.list_developers import (
    ListDevelopersUseCase,
)

from backlog_manager.application.use_cases.feature.create_feature import (
    CreateFeatureUseCase,
)
from backlog_manager.application.use_cases.feature.update_feature import (
    UpdateFeatureUseCase,
)
from backlog_manager.application.use_cases.feature.delete_feature import (
    DeleteFeatureUseCase,
)
from backlog_manager.application.use_cases.feature.get_feature import (
    GetFeatureUseCase,
)
from backlog_manager.application.use_cases.feature.list_features import (
    ListFeaturesUseCase,
)

from backlog_manager.application.use_cases.dependency.add_dependency import (
    AddDependencyUseCase,
)
from backlog_manager.application.use_cases.dependency.remove_dependency import (
    RemoveDependencyUseCase,
)

from backlog_manager.application.use_cases.schedule.calculate_schedule import (
    CalculateScheduleUseCase,
)
from backlog_manager.application.use_cases.schedule.allocate_developers import (
    AllocateDevelopersUseCase,
)

from backlog_manager.application.use_cases.configuration.get_configuration import (
    GetConfigurationUseCase,
)
from backlog_manager.application.use_cases.configuration.update_configuration import (
    UpdateConfigurationUseCase,
)

from backlog_manager.application.use_cases.excel.import_from_excel import (
    ImportFromExcelUseCase,
)
from backlog_manager.application.use_cases.excel.export_to_excel import (
    ExportToExcelUseCase,
)

from backlog_manager.presentation.controllers.story_controller import StoryController
from backlog_manager.presentation.controllers.developer_controller import (
    DeveloperController,
)
from backlog_manager.presentation.controllers.feature_controller import (
    FeatureController,
)
from backlog_manager.presentation.controllers.schedule_controller import (
    ScheduleController,
)
from backlog_manager.presentation.controllers.main_controller import MainController


class DIContainer:
    """Container de injeção de dependências."""

    def __init__(self, database_path: str = "backlog.db"):
        """
        Inicializa o container.

        Args:
            database_path: Caminho do banco de dados SQLite
        """
        self._database_path = database_path
        self._initialize_database()
        self._create_domain_services()
        self._create_repositories()
        self._create_excel_service()
        self._create_use_cases()
        self._create_controllers()

    def _initialize_database(self) -> None:
        """Inicializa conexão com banco de dados."""
        # SQLiteConnection é singleton, criar e guardar referência
        self.db_connection = SQLiteConnection(self._database_path)

    def _create_domain_services(self) -> None:
        """Cria serviços de domínio."""
        self.cycle_detector = CycleDetector()
        self.backlog_sorter = BacklogSorter()
        self.schedule_calculator = ScheduleCalculator()
        self.allocation_validator = AllocationValidator()
        self.developer_load_balancer = DeveloperLoadBalancer()
        # IdlenessDetector usa ScheduleCalculator para cálculo de dias úteis
        self.idleness_detector = IdlenessDetector(self.schedule_calculator)
        self.wave_dependency_validator = WaveDependencyValidator()

    def _create_repositories(self) -> None:
        """Cria repositories."""
        self.story_repository = SQLiteStoryRepository(self.db_connection)
        self.developer_repository = SQLiteDeveloperRepository(self.db_connection)
        self.feature_repository = SQLiteFeatureRepository(self.db_connection)
        self.configuration_repository = SQLiteConfigurationRepository(self.db_connection)

    def _create_excel_service(self) -> None:
        """Cria serviço de Excel."""
        self.excel_service = OpenpyxlExcelService()

    def _create_use_cases(self) -> None:
        """Cria use cases."""
        # Story Use Cases
        self.create_story_use_case = CreateStoryUseCase(
            self.story_repository, self.feature_repository
        )
        self.update_story_use_case = UpdateStoryUseCase(
            self.story_repository, self.feature_repository, self.wave_dependency_validator
        )
        self.delete_story_use_case = DeleteStoryUseCase(self.story_repository)
        self.get_story_use_case = GetStoryUseCase(self.story_repository)
        self.list_stories_use_case = ListStoriesUseCase(self.story_repository)
        self.duplicate_story_use_case = DuplicateStoryUseCase(
            self.story_repository
        )
        self.change_priority_use_case = ChangePriorityUseCase(
            self.story_repository
        )
        self.validate_allocation_use_case = ValidateDeveloperAllocationUseCase(
            self.story_repository, self.allocation_validator
        )

        # Developer Use Cases
        self.create_developer_use_case = CreateDeveloperUseCase(
            self.developer_repository
        )
        self.update_developer_use_case = UpdateDeveloperUseCase(
            self.developer_repository
        )
        self.delete_developer_use_case = DeleteDeveloperUseCase(
            self.developer_repository, self.story_repository
        )
        self.get_developer_use_case = GetDeveloperUseCase(
            self.developer_repository
        )
        self.list_developers_use_case = ListDevelopersUseCase(
            self.developer_repository
        )

        # Feature Use Cases
        self.create_feature_use_case = CreateFeatureUseCase(
            self.feature_repository
        )
        self.update_feature_use_case = UpdateFeatureUseCase(
            self.feature_repository, self.story_repository, self.wave_dependency_validator
        )
        self.delete_feature_use_case = DeleteFeatureUseCase(
            self.feature_repository
        )
        self.get_feature_use_case = GetFeatureUseCase(
            self.feature_repository
        )
        self.list_features_use_case = ListFeaturesUseCase(
            self.feature_repository
        )

        # Dependency Use Cases
        self.add_dependency_use_case = AddDependencyUseCase(
            self.story_repository, self.cycle_detector, self.wave_dependency_validator
        )
        self.remove_dependency_use_case = RemoveDependencyUseCase(
            self.story_repository
        )

        # Schedule Use Cases
        self.calculate_schedule_use_case = CalculateScheduleUseCase(
            self.story_repository,
            self.configuration_repository,
            self.backlog_sorter,
            self.schedule_calculator,
        )
        self.allocate_developers_use_case = AllocateDevelopersUseCase(
            self.story_repository,
            self.developer_repository,
            self.configuration_repository,
            self.developer_load_balancer,
            self.idleness_detector,
            self.schedule_calculator,
            self.backlog_sorter
        )

        # Configuration Use Cases
        self.get_configuration_use_case = GetConfigurationUseCase(
            self.configuration_repository
        )
        self.update_configuration_use_case = UpdateConfigurationUseCase(
            self.configuration_repository
        )

        # Excel Use Cases
        self.import_from_excel_use_case = ImportFromExcelUseCase(
            self.story_repository,
            self.excel_service,
            self.cycle_detector,
            self.feature_repository,  # NOVO: para upsert de features
            self.developer_repository,  # NOVO: para upsert de developers
        )
        self.export_to_excel_use_case = ExportToExcelUseCase(
            self.excel_service, self.story_repository
        )

    def _create_controllers(self) -> None:
        """Cria controllers."""
        # Story Controller
        self.story_controller = StoryController(
            self.create_story_use_case,
            self.update_story_use_case,
            self.delete_story_use_case,
            self.get_story_use_case,
            self.list_stories_use_case,
            self.duplicate_story_use_case,
            self.change_priority_use_case,
            self.calculate_schedule_use_case,
            self.validate_allocation_use_case,
        )

        # Developer Controller
        self.developer_controller = DeveloperController(
            self.create_developer_use_case,
            self.update_developer_use_case,
            self.delete_developer_use_case,
            self.get_developer_use_case,
            self.list_developers_use_case,
        )

        # Feature Controller
        self.feature_controller = FeatureController(
            self.create_feature_use_case,
            self.update_feature_use_case,
            self.delete_feature_use_case,
            self.get_feature_use_case,
            self.list_features_use_case,
        )

        # Schedule Controller
        self.schedule_controller = ScheduleController(
            self.calculate_schedule_use_case,
            self.allocate_developers_use_case,
        )

        # Main Controller
        self.main_controller = MainController(
            self.story_controller,
            self.developer_controller,
            self.feature_controller,
            self.schedule_controller,
            self.import_from_excel_use_case,
            self.export_to_excel_use_case,
            self.get_configuration_use_case,
            self.update_configuration_use_case,
            self.validate_allocation_use_case,
            self.story_repository,
        )

    def get_main_controller(self) -> MainController:
        """
        Retorna o controlador principal.

        Returns:
            Controlador principal da aplicação
        """
        return self.main_controller
