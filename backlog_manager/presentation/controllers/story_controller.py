"""
Controlador de operações de histórias.

Orquestra a comunicação entre views e use cases relacionados a histórias.
"""
from typing import Optional, List
from PySide6.QtWidgets import QWidget

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
from backlog_manager.application.use_cases.schedule.calculate_schedule import (
    CalculateScheduleUseCase,
)
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.presentation.utils.message_box import MessageBox


class StoryController:
    """Controlador de histórias."""

    # Campos que requerem recálculo de cronograma
    FIELDS_REQUIRING_RECALC = ["story_point", "developer_id", "dependencies"]

    def __init__(
        self,
        create_story_use_case: CreateStoryUseCase,
        update_story_use_case: UpdateStoryUseCase,
        delete_story_use_case: DeleteStoryUseCase,
        get_story_use_case: GetStoryUseCase,
        list_stories_use_case: ListStoriesUseCase,
        duplicate_story_use_case: DuplicateStoryUseCase,
        change_priority_use_case: ChangePriorityUseCase,
        calculate_schedule_use_case: CalculateScheduleUseCase,
    ):
        """
        Inicializa o controlador.

        Args:
            create_story_use_case: Use case de criação
            update_story_use_case: Use case de atualização
            delete_story_use_case: Use case de deleção
            get_story_use_case: Use case de obtenção
            list_stories_use_case: Use case de listagem
            duplicate_story_use_case: Use case de duplicação
            change_priority_use_case: Use case de mudança de prioridade
            calculate_schedule_use_case: Use case de cálculo de cronograma
        """
        self._create_use_case = create_story_use_case
        self._update_use_case = update_story_use_case
        self._delete_use_case = delete_story_use_case
        self._get_use_case = get_story_use_case
        self._list_use_case = list_stories_use_case
        self._duplicate_use_case = duplicate_story_use_case
        self._change_priority_use_case = change_priority_use_case
        self._calculate_schedule_use_case = calculate_schedule_use_case

        self._parent_widget: Optional[QWidget] = None
        self._refresh_callback: Optional[callable] = None
        self._show_loading_callback: Optional[callable] = None
        self._hide_loading_callback: Optional[callable] = None

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

    def set_loading_callbacks(self, show: callable, hide: callable) -> None:
        """
        Define callbacks de indicador de loading.

        Args:
            show: Callback para mostrar loading
            hide: Callback para esconder loading
        """
        self._show_loading_callback = show
        self._hide_loading_callback = hide

    def create_story(self, form_data: dict) -> None:
        """
        Cria uma nova história.

        Args:
            form_data: Dados do formulário
        """
        try:
            story = self._create_use_case.execute(form_data)
            self._refresh_view()

            # Feedback visual via status bar (MessageBox causa crash com delegates)
            # TODO: Investigar causa raiz do crash do MessageBox no futuro
            print(f"✓ História '{story.name}' criada com sucesso!")

        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Criar História", str(e)
            )

    def update_story(self, story_id: str, form_data: dict) -> None:
        """
        Atualiza uma história existente.

        Args:
            story_id: ID da história
            form_data: Dados atualizados
        """
        try:
            self._update_use_case.execute(story_id, form_data)
            MessageBox.success(
                self._parent_widget, "Sucesso", "História atualizada com sucesso!"
            )
            self._refresh_view()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Atualizar História", str(e)
            )

    def delete_story(self, story_id: str) -> None:
        """
        Deleta uma história.

        Args:
            story_id: ID da história a deletar
        """
        try:
            # Obter história para confirmar
            story = self._get_use_case.execute(story_id)

            # Confirmar deleção
            if not MessageBox.confirm_delete(self._parent_widget, story.name):
                return

            # Deletar
            self._delete_use_case.execute(story_id)
            MessageBox.success(
                self._parent_widget, "Sucesso", "História deletada com sucesso!"
            )
            self._refresh_view()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Deletar História", str(e)
            )

    def duplicate_story(self, story_id: str) -> None:
        """
        Duplica uma história.

        Args:
            story_id: ID da história a duplicar
        """
        try:
            new_story = self._duplicate_use_case.execute(story_id)
            MessageBox.success(
                self._parent_widget,
                "Sucesso",
                f"História duplicada! Nova ID: {new_story.id}",
            )
            self._refresh_view()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Duplicar História", str(e)
            )

    def on_story_field_changed(
        self, story_id: str, field: str, value: object
    ) -> None:
        """
        Gerencia edição inline de campo.

        Args:
            story_id: ID da história
            field: Nome do campo alterado
            value: Novo valor
        """
        try:
            # Atualizar história
            self._update_use_case.execute(story_id, {field: value})

            # Verificar se requer recálculo
            if field in self.FIELDS_REQUIRING_RECALC:
                self._recalculate_schedule()

        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Atualizar Campo", str(e)
            )
            # Reverter mudança na view
            self._refresh_view()

    def move_priority_up(self, story_id: str) -> None:
        """
        Move história para cima na prioridade.

        Args:
            story_id: ID da história
        """
        try:
            self._change_priority_use_case.execute(story_id, direction="up")
            self._refresh_view()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Mover Prioridade", str(e)
            )

    def move_priority_down(self, story_id: str) -> None:
        """
        Move história para baixo na prioridade.

        Args:
            story_id: ID da história
        """
        try:
            self._change_priority_use_case.execute(story_id, direction="down")
            self._refresh_view()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Mover Prioridade", str(e)
            )

    def get_story(self, story_id: str) -> Optional[StoryDTO]:
        """
        Obtém uma história pelo ID.

        Args:
            story_id: ID da história

        Returns:
            História ou None se não encontrada
        """
        try:
            return self._get_use_case.execute(story_id)
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Obter História", str(e)
            )
            return None

    def list_stories(self) -> List[StoryDTO]:
        """
        Lista todas as histórias ordenadas.

        Returns:
            Lista de histórias
        """
        try:
            return self._list_use_case.execute()
        except Exception as e:
            MessageBox.error(
                self._parent_widget, "Erro ao Listar Histórias", str(e)
            )
            return []

    def _recalculate_schedule(self) -> None:
        """Recalcula o cronograma."""
        try:
            if self._show_loading_callback:
                self._show_loading_callback()

            self._calculate_schedule_use_case.execute()

            if self._hide_loading_callback:
                self._hide_loading_callback()

            self._refresh_view()
        except Exception as e:
            if self._hide_loading_callback:
                self._hide_loading_callback()
            MessageBox.error(
                self._parent_widget, "Erro ao Recalcular Cronograma", str(e)
            )

    def _refresh_view(self) -> None:
        """Atualiza a view."""
        if self._refresh_callback:
            self._refresh_callback()
