"""
Controlador de operações de features.

Orquestra a comunicação entre views e use cases relacionados a features.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

from backlog_manager.application.dto.feature_dto import FeatureDTO
from backlog_manager.application.use_cases.feature.create_feature import CreateFeatureUseCase
from backlog_manager.application.use_cases.feature.delete_feature import DeleteFeatureUseCase
from backlog_manager.application.use_cases.feature.get_feature import GetFeatureUseCase
from backlog_manager.application.use_cases.feature.list_features import ListFeaturesUseCase
from backlog_manager.application.use_cases.feature.update_feature import UpdateFeatureUseCase
from backlog_manager.domain.exceptions.domain_exceptions import (
    DuplicateWaveException,
    FeatureHasStoriesException,
    FeatureNotFoundException,
    InvalidWaveDependencyException,
)
from backlog_manager.presentation.utils.message_box import MessageBox


class FeatureController:
    """Controlador de features."""

    def __init__(
        self,
        create_feature_use_case: CreateFeatureUseCase,
        update_feature_use_case: UpdateFeatureUseCase,
        delete_feature_use_case: DeleteFeatureUseCase,
        get_feature_use_case: GetFeatureUseCase,
        list_features_use_case: ListFeaturesUseCase,
    ):
        """
        Inicializa o controlador.

        Args:
            create_feature_use_case: Use case de criação
            update_feature_use_case: Use case de atualização
            delete_feature_use_case: Use case de deleção
            get_feature_use_case: Use case de obtenção
            list_features_use_case: Use case de listagem
        """
        self._create_use_case = create_feature_use_case
        self._update_use_case = update_feature_use_case
        self._delete_use_case = delete_feature_use_case
        self._get_use_case = get_feature_use_case
        self._list_use_case = list_features_use_case

        self._parent_widget: Optional[QWidget] = None
        self._refresh_callback: Optional[callable] = None

    def set_parent_widget(self, widget: QWidget) -> None:
        """
        Define o widget pai para dialogs.

        Args:
            widget: Widget pai
        """
        self._parent_widget = widget

    def set_refresh_callback(self, callback: callable) -> None:
        """
        Define callback para atualizar a view.

        Args:
            callback: Função a chamar para atualizar
        """
        self._refresh_callback = callback

    def create_feature(self, name: str, wave: int) -> None:
        """
        Cria uma nova feature.

        Args:
            name: Nome da feature
            wave: Número da onda
        """
        try:
            feature = self._create_use_case.execute(name, wave)
            MessageBox.success(
                self._parent_widget,
                "Sucesso",
                f"Feature '{feature.name}' criada com ID: {feature.id} na onda {feature.wave}",
            )
            self._refresh_view()
        except DuplicateWaveException as e:
            MessageBox.error(
                self._parent_widget,
                "Erro: Onda Duplicada",
                f"Já existe uma feature na onda {e.wave}: '{e.existing_feature_name}'.\n"
                f"Cada onda deve ter apenas uma feature.",
            )
        except ValueError as e:
            MessageBox.error(self._parent_widget, "Erro de Validação", str(e))
        except Exception as e:
            MessageBox.error(self._parent_widget, "Erro ao Criar Feature", str(e))

    def update_feature(self, feature_id: str, name: str, wave: int) -> None:
        """
        Atualiza uma feature existente.

        Args:
            feature_id: ID da feature
            name: Novo nome
            wave: Nova onda
        """
        try:
            feature = self._update_use_case.execute(feature_id, name, wave)
            MessageBox.success(
                self._parent_widget,
                "Sucesso",
                f"Feature '{feature.name}' atualizada (Onda {feature.wave})",
            )
            self._refresh_view()
        except FeatureNotFoundException as e:
            MessageBox.error(
                self._parent_widget, "Erro", f"Feature não encontrada: {e.feature_id}"
            )
        except DuplicateWaveException as e:
            MessageBox.error(
                self._parent_widget,
                "Erro: Onda Duplicada",
                f"Já existe uma feature na onda {e.wave}: '{e.existing_feature_name}'.\n"
                f"Escolha outra onda.",
            )
        except InvalidWaveDependencyException as e:
            MessageBox.error(
                self._parent_widget,
                "Erro: Dependências Inválidas",
                f"Não é possível mudar para onda {e.dependency_wave} porque:\n"
                f"História '{e.story_id}' (onda {e.story_wave}) depende de "
                f"história '{e.dependency_id}' (onda {e.dependency_wave}).\n\n"
                f"Histórias não podem depender de histórias em ondas posteriores.",
            )
        except ValueError as e:
            MessageBox.error(self._parent_widget, "Erro de Validação", str(e))
        except Exception as e:
            MessageBox.error(self._parent_widget, "Erro ao Atualizar Feature", str(e))

    def delete_feature(self, feature_id: str) -> bool:
        """
        Deleta uma feature.

        Args:
            feature_id: ID da feature

        Returns:
            True se deletado com sucesso
        """
        try:
            self._delete_use_case.execute(feature_id)
            MessageBox.success(
                self._parent_widget, "Sucesso", f"Feature '{feature_id}' deletada"
            )
            self._refresh_view()
            return True
        except FeatureNotFoundException as e:
            MessageBox.error(
                self._parent_widget, "Erro", f"Feature não encontrada: {e.feature_id}"
            )
            return False
        except FeatureHasStoriesException as e:
            MessageBox.error(
                self._parent_widget,
                "Erro: Feature Possui Histórias",
                f"Não é possível deletar a feature '{e.feature_name}' porque ela possui "
                f"{e.story_count} história(s) associada(s).\n\n"
                f"Delete ou reatribua as histórias antes de deletar a feature.",
            )
            return False
        except Exception as e:
            MessageBox.error(self._parent_widget, "Erro ao Deletar Feature", str(e))
            return False

    def get_feature(self, feature_id: str) -> Optional[FeatureDTO]:
        """
        Obtém uma feature por ID.

        Args:
            feature_id: ID da feature

        Returns:
            FeatureDTO ou None se não encontrada
        """
        try:
            return self._get_use_case.execute(feature_id)
        except FeatureNotFoundException:
            return None
        except Exception as e:
            MessageBox.error(self._parent_widget, "Erro ao Buscar Feature", str(e))
            return None

    def list_features(self) -> list[FeatureDTO]:
        """
        Lista todas as features ordenadas por onda.

        Returns:
            Lista de FeatureDTOs
        """
        try:
            return self._list_use_case.execute()
        except Exception as e:
            MessageBox.error(self._parent_widget, "Erro ao Listar Features", str(e))
            return []

    def _refresh_view(self) -> None:
        """Atualiza a view se callback definido."""
        if self._refresh_callback:
            self._refresh_callback()
