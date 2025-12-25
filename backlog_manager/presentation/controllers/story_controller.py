"""
Controlador de operações de histórias.

Orquestra a comunicação entre views e use cases relacionados a histórias.
"""
import logging
from typing import Optional, List
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

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
from backlog_manager.application.use_cases.story.change_priority import Direction
from backlog_manager.application.use_cases.story.validate_developer_allocation import (
    ValidateDeveloperAllocationUseCase,
)
from backlog_manager.application.dto.story_dto import StoryDTO
from backlog_manager.domain.services.allocation_validator import AllocationConflict
from backlog_manager.presentation.utils.message_box import MessageBox
from backlog_manager.presentation.utils.cell_highlighter import CellHighlighter


class StoryController:
    """Controlador de histórias."""

    # Campos que requerem recálculo de cronograma
    # Nota: developer_id NÃO está aqui porque mudar o desenvolvedor de uma história
    # não deve recalcular todo o cronograma (que limpa todos os desenvolvedores)
    FIELDS_REQUIRING_RECALC = ["story_point", "dependencies"]

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
        validate_allocation_use_case: ValidateDeveloperAllocationUseCase,
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
            validate_allocation_use_case: Use case de validação de alocação
        """
        self._create_use_case = create_story_use_case
        self._update_use_case = update_story_use_case
        self._delete_use_case = delete_story_use_case
        self._get_use_case = get_story_use_case
        self._list_use_case = list_stories_use_case
        self._duplicate_use_case = duplicate_story_use_case
        self._change_priority_use_case = change_priority_use_case
        self._calculate_schedule_use_case = calculate_schedule_use_case
        self._validate_allocation_use_case = validate_allocation_use_case

        self._parent_widget: Optional[QWidget] = None
        self._table_widget = None
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

    def set_table_widget(self, table_widget) -> None:
        """
        Define referência à tabela para feedback visual.

        Args:
            table_widget: Widget da tabela
        """
        self._table_widget = table_widget

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
        logger.info(f"Criando história: component='{form_data.get('component')}', name='{form_data.get('name')}'")
        logger.debug(f"Dados completos do formulário: {form_data}")

        try:
            story = self._create_use_case.execute(form_data)
            logger.info(f"História criada com sucesso: id='{story.id}', priority={story.priority}")

            self._refresh_view()

            # Feedback visual via status bar (MessageBox causa crash com delegates)
            # TODO: Investigar causa raiz do crash do MessageBox no futuro
            logger.info(f"✓ História '{story.name}' criada com sucesso!")

        except Exception as e:
            logger.error(f"Erro ao criar história: {e}", exc_info=True)
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
        logger.info(f"Atualizando história: id='{story_id}'")
        logger.debug(f"Dados de atualização: {form_data}")

        try:
            self._update_use_case.execute(story_id, form_data)
            logger.info(f"História '{story_id}' atualizada com sucesso")

            MessageBox.success(
                self._parent_widget, "Sucesso", "História atualizada com sucesso!"
            )
            self._refresh_view()
        except Exception as e:
            logger.error(f"Erro ao atualizar história '{story_id}': {e}", exc_info=True)
            MessageBox.error(
                self._parent_widget, "Erro ao Atualizar História", str(e)
            )

    def delete_story(self, story_id: str) -> None:
        """
        Deleta uma história.

        Args:
            story_id: ID da história a deletar
        """
        logger.info(f"Solicitação de deleção de história: id='{story_id}'")

        try:
            # Obter história para confirmar
            story = self._get_use_case.execute(story_id)

            # Confirmar deleção
            if not MessageBox.confirm_delete(self._parent_widget, story.name):
                logger.debug(f"Deleção de '{story_id}' cancelada pelo usuário")
                return

            # Deletar
            logger.info(f"Deletando história: id='{story_id}'")
            self._delete_use_case.execute(story_id)
            logger.info(f"História '{story_id}' deletada com sucesso")

            MessageBox.success(
                self._parent_widget, "Sucesso", "História deletada com sucesso!"
            )
            self._refresh_view()
        except Exception as e:
            logger.error(f"Erro ao deletar história '{story_id}': {e}", exc_info=True)
            MessageBox.error(
                self._parent_widget, "Erro ao Deletar História", str(e)
            )

    def duplicate_story(self, story_id: str) -> None:
        """
        Duplica uma história.

        Args:
            story_id: ID da história a duplicar
        """
        logger.info(f"Duplicando história: id='{story_id}'")

        try:
            new_story = self._duplicate_use_case.execute(story_id)
            logger.info(f"História duplicada: original='{story_id}', nova='{new_story.id}'")

            MessageBox.success(
                self._parent_widget,
                "Sucesso",
                f"História duplicada! Nova ID: {new_story.id}",
            )
            self._refresh_view()
        except Exception as e:
            logger.error(f"Erro ao duplicar história '{story_id}': {e}", exc_info=True)
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
            # Converter dependências de string para lista
            if field == "dependencies":
                if isinstance(value, str):
                    # Converter "S1, S2, S3" para ["S1", "S2", "S3"]
                    value = [dep.strip() for dep in value.split(",") if dep.strip()]
                elif value is None:
                    value = []

            # TRATAMENTO ESPECIAL: developer_id
            if field == "developer_id":
                # Converter "(Nenhum)" para None (banco espera NULL)
                if value == "(Nenhum)" or not value:
                    value = None

                # Validar conflito de alocação apenas se estiver alocando um desenvolvedor
                if value is not None:
                    is_valid, conflicts = self._validate_allocation_use_case.execute(
                        story_id, value
                    )

                    if not is_valid:
                        # Conflito detectado! Cancelar operação e mostrar feedback
                        self._handle_allocation_conflict(story_id, conflicts)
                        return  # NÃO salva

            # Atualizar história
            self._update_use_case.execute(story_id, {field: value})

            # Verificar se requer recálculo
            if field in self.FIELDS_REQUIRING_RECALC:
                self._recalculate_schedule()
            else:
                # Se não requer recálculo, apenas atualizar view
                self._refresh_view()

        except Exception as e:
            logger.error(f"Erro ao atualizar campo '{field}' da história '{story_id}': {e}", exc_info=True)
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
            self._change_priority_use_case.execute(story_id, direction=Direction.UP)
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
            self._change_priority_use_case.execute(story_id, direction=Direction.DOWN)
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

    def _handle_allocation_conflict(
        self,
        story_id: str,
        conflicts: List[AllocationConflict]
    ) -> None:
        """
        Trata conflito de alocação com feedback visual.

        Args:
            story_id: ID da história sendo editada
            conflicts: Lista de conflitos detectados
        """
        if not self._table_widget:
            MessageBox.warning(
                self._parent_widget,
                "Conflito de Alocação",
                "Desenvolvedor já está alocado em histórias com períodos sobrepostos."
            )
            self._refresh_view()
            return

        # Encontrar linhas conflitantes
        from backlog_manager.presentation.views.widgets.editable_table import EditableTableWidget
        table = self._table_widget
        conflicting_rows = []
        current_row = None

        for row in range(table.rowCount()):
            id_item = table.item(row, EditableTableWidget.COL_ID)
            if not id_item:
                continue

            row_story_id = id_item.text()

            if row_story_id == story_id:
                current_row = row

            for conflict in conflicts:
                if row_story_id == conflict.story_id:
                    conflicting_rows.append(row)

        # Reverter célula para valor correto ANTES de mostrar feedback
        # (evita loops de eventos)
        if current_row is not None:
            # Buscar valor correto do banco de dados
            story = self._get_use_case.execute(story_id)
            if story:
                # Atualizar apenas a célula específica
                developer_item = table.item(current_row, EditableTableWidget.COL_DEVELOPER)
                if developer_item:
                    # Se tinha desenvolvedor, mostra o ID, senão mostra "(Nenhum)"
                    correct_value = story.developer_id if story.developer_id else "(Nenhum)"
                    developer_item.setText(correct_value)

        # Destacar células em vermelho
        all_rows = ([current_row] + conflicting_rows) if current_row is not None else conflicting_rows

        if all_rows:
            CellHighlighter.flash_error(
                table=table,
                rows=all_rows,
                column=EditableTableWidget.COL_DEVELOPER,
                duration_ms=2000
            )

        # Mostrar mensagem de erro
        conflict_ids = [c.story_id for c in conflicts]
        MessageBox.warning(
            self._parent_widget,
            "Conflito de Alocação",
            f"Desenvolvedor já está alocado em: {', '.join(conflict_ids)}\n"
            f"Períodos de execução se sobrepõem."
        )
