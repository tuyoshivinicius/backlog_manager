# PLANO DE IMPLEMENTAÇÃO - Data de Início do Roadmap

**Projeto:** Backlog Manager
**Data:** 2025-12-20
**Objetivo:** Adicionar configuração de data de início do roadmap com persistência e restauração automática

---

## CONTEXTO

### Situação Atual
- O sistema já calcula cronograma com velocidade do time (story_points_per_sprint e workdays_per_sprint)
- `ScheduleCalculator.calculate()` aceita `start_date` opcional, mas usa `date.today()` como padrão
- Configuração já é persistida no banco de dados (tabela `configuration` singleton com ID=1)
- Cálculo de duração e cronograma já respeita dias úteis (segunda a sexta)

### Problema
- Não há forma de o usuário configurar uma data de início customizada para o roadmap
- Data de início não é persistida, sempre recalcula a partir da data atual
- Interface não oferece controle sobre quando o roadmap deve começar

### Solução Proposta
Adicionar campo `roadmap_start_date` à configuração global, permitindo ao usuário:
1. Selecionar uma data de início através de um datepicker na interface
2. Persistir essa data no banco junto com as outras configurações
3. Restaurar automaticamente ao abrir a aplicação
4. Usar essa data como referência para o cálculo de cronograma

---

## REQUISITOS FUNCIONAIS

### RF-NEW-001 - Configurar Data de Início do Roadmap
**Descrição:** O sistema deve permitir ao usuário configurar a data de início do roadmap através de um datepicker.

**Critérios de Aceitação:**
- Dialog de Configurações deve incluir campo de seleção de data
- Usar componente `QDateEdit` com calendário dropdown
- Validar que data seja >= data atual (não permitir datas passadas)
- Validar que data seja um dia útil (segunda a sexta)
- Sugerir próximo dia útil automaticamente se usuário selecionar fim de semana
- Data deve ser salva junto com story_points_per_sprint e workdays_per_sprint
- Data deve ser opcional (pode ser NULL = usar date.today())

### RF-NEW-002 - Persistir Data de Início do Roadmap
**Descrição:** O sistema deve persistir a data de início do roadmap no banco de dados SQLite.

**Critérios de Aceitação:**
- Adicionar coluna `roadmap_start_date` (TEXT, nullable) na tabela `configuration`
- Formato ISO 8601: "YYYY-MM-DD" (ex: "2025-01-15")
- Migration automática: ALTER TABLE para adicionar coluna em banco existente
- Atualizar `SQLiteConfigurationRepository` para ler/escrever a data

### RF-NEW-003 - Restaurar Data de Início na Inicialização
**Descrição:** O sistema deve restaurar a data de início configurada ao abrir a aplicação.

**Critérios de Aceitação:**
- `ConfigurationRepository.get()` deve retornar a data salva
- Se não houver data salva (NULL), usar `date.today()` como fallback
- Dialog de Configurações deve exibir a data atual ao abrir

### RF-NEW-004 - Usar Data Configurada no Cálculo de Cronograma
**Descrição:** O sistema deve usar a data configurada como início do roadmap ao calcular cronograma.

**Critérios de Aceitação:**
- `CalculateScheduleUseCase.execute()` deve buscar a data da configuração
- Passar a data para `ScheduleCalculator.calculate(stories, config, start_date)`
- Se data configurada for NULL, usar `date.today()` (comportamento atual)
- Histórias devem começar a partir da data configurada (ou posterior, se houver dependências/alocações)
- Garantir que a data de início respeite dias úteis (já implementado no `ScheduleCalculator`)

---

## ARQUITETURA DE MUDANÇAS

### Camada 1: Domain (Entidades e Value Objects)

#### Modificar: `backlog_manager/domain/entities/configuration.py`
```python
from datetime import date
from typing import Optional

@dataclass
class Configuration:
    story_points_per_sprint: int = 21
    workdays_per_sprint: int = 15
    roadmap_start_date: Optional[date] = None  # ✅ NOVO CAMPO

    @property
    def velocity_per_day(self) -> float:
        """Calcula velocidade em story points por dia útil."""
        return self.story_points_per_sprint / self.workdays_per_sprint

    def __post_init__(self) -> None:
        """Valida configuração após inicialização."""
        self._validate()

    def _validate(self) -> None:
        """Valida invariantes da configuração."""
        if self.story_points_per_sprint <= 0:
            raise ValueError("Story points por sprint deve ser maior que zero")
        if self.workdays_per_sprint <= 0:
            raise ValueError("Dias úteis por sprint deve ser maior que zero")
        # ✅ NOVA VALIDAÇÃO
        if self.roadmap_start_date and self.roadmap_start_date.weekday() >= 5:
            raise ValueError("Data de início do roadmap deve ser um dia útil (seg-sex)")
```

**Justificativa:**
- Adiciona o campo opcional `roadmap_start_date` à entidade de domínio
- Validação garante que a data, se fornecida, seja um dia útil
- Mantém compatibilidade com código existente (valor padrão `None`)

---

### Camada 2: Infrastructure (Banco de Dados)

#### Modificar: `backlog_manager/infrastructure/database/schema.sql`
```sql
-- ✅ MODIFICAR TABELA CONFIGURATION
CREATE TABLE IF NOT EXISTS configuration (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    story_points_per_sprint INTEGER NOT NULL DEFAULT 21,
    workdays_per_sprint INTEGER NOT NULL DEFAULT 15,
    roadmap_start_date TEXT,  -- ✅ NOVO CAMPO (formato ISO: YYYY-MM-DD)
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Garantir linha singleton
INSERT OR IGNORE INTO configuration (id, story_points_per_sprint, workdays_per_sprint)
VALUES (1, 21, 15);

-- ✅ MIGRATION: Adicionar coluna em bancos existentes
-- Executado automaticamente pela aplicação se coluna não existir
```

#### Criar Script de Migration: `backlog_manager/infrastructure/database/migrations/001_add_roadmap_start_date.py`
```python
"""Migration: Adiciona coluna roadmap_start_date à tabela configuration."""

def upgrade(connection):
    """Aplica migration."""
    cursor = connection.cursor()
    try:
        cursor.execute("""
            ALTER TABLE configuration
            ADD COLUMN roadmap_start_date TEXT
        """)
        connection.commit()
        return True
    except Exception as e:
        # Coluna já existe (migration já aplicada)
        if "duplicate column" in str(e).lower():
            return False
        raise

def downgrade(connection):
    """Reverte migration (SQLite não suporta DROP COLUMN nativamente)."""
    # Não implementado - SQLite não suporta DROP COLUMN facilmente
    pass
```

#### Modificar: `backlog_manager/infrastructure/database/repositories/sqlite_configuration_repository.py`
```python
from datetime import date
from typing import Optional

class SQLiteConfigurationRepository(ConfigurationRepository):
    """Repositório SQLite para configuração."""

    def get(self) -> Configuration:
        """
        Busca configuração global (singleton).

        Returns:
            Configuração do sistema
        """
        cursor = self._connection.cursor()
        cursor.execute("""
            SELECT
                story_points_per_sprint,
                workdays_per_sprint,
                roadmap_start_date  -- ✅ NOVO CAMPO
            FROM configuration
            WHERE id = 1
        """)
        row = cursor.fetchone()

        if not row:
            # Configuração padrão se não existir no banco
            return Configuration()

        return Configuration(
            story_points_per_sprint=row[0],
            workdays_per_sprint=row[1],
            roadmap_start_date=date.fromisoformat(row[2]) if row[2] else None  # ✅ CONVERTER DE ISO
        )

    def save(self, configuration: Configuration) -> None:
        """
        Salva configuração global.

        Args:
            configuration: Configuração a ser salva
        """
        cursor = self._connection.cursor()
        cursor.execute("""
            UPDATE configuration
            SET
                story_points_per_sprint = ?,
                workdays_per_sprint = ?,
                roadmap_start_date = ?,  -- ✅ NOVO CAMPO
                updated_at = datetime('now')
            WHERE id = 1
        """, (
            configuration.story_points_per_sprint,
            configuration.workdays_per_sprint,
            configuration.roadmap_start_date.isoformat() if configuration.roadmap_start_date else None  # ✅ CONVERTER PARA ISO
        ))
        self._connection.commit()
```

**Justificativa:**
- Adiciona coluna `roadmap_start_date` ao schema
- Migration script para atualizar bancos existentes sem perda de dados
- Repository serializa/deserializa data em formato ISO 8601

---

### Camada 3: Application (Use Cases)

#### Modificar: `backlog_manager/application/use_cases/configuration/update_configuration.py`
```python
from datetime import date
from typing import Optional

class UpdateConfigurationUseCase:
    """Caso de uso para atualizar configuração global."""

    def __init__(self, configuration_repository: ConfigurationRepository):
        self._config_repo = configuration_repository

    def execute(
        self,
        story_points_per_sprint: int,
        workdays_per_sprint: int,
        roadmap_start_date: Optional[date] = None  # ✅ NOVO PARÂMETRO
    ) -> Configuration:
        """
        Atualiza configuração global do sistema.

        Args:
            story_points_per_sprint: Velocidade do time em SP/sprint
            workdays_per_sprint: Dias úteis por sprint
            roadmap_start_date: Data de início do roadmap (opcional)

        Returns:
            Configuração atualizada

        Raises:
            ValueError: Se valores forem inválidos
        """
        config = Configuration(
            story_points_per_sprint=story_points_per_sprint,
            workdays_per_sprint=workdays_per_sprint,
            roadmap_start_date=roadmap_start_date  # ✅ NOVO CAMPO
        )

        self._config_repo.save(config)
        return config
```

#### Modificar: `backlog_manager/application/use_cases/schedule/calculate_schedule.py`
```python
from datetime import date
from typing import Optional

class CalculateScheduleUseCase:
    """Caso de uso para calcular cronograma completo."""

    def execute(self, start_date: Optional[date] = None) -> BacklogDTO:
        """
        Calcula cronograma completo do backlog.

        Args:
            start_date: Data de início customizada (opcional)
                       Se None, usa a data configurada no sistema
                       Se configurada também for None, usa date.today()

        Returns:
            BacklogDTO com cronograma calculado
        """
        # Buscar configuração
        config = self._configuration_repository.get()

        # ✅ DETERMINAR DATA DE INÍCIO
        # Prioridade: 1) start_date passado por parâmetro
        #             2) roadmap_start_date da configuração
        #             3) date.today() (fallback)
        effective_start_date = start_date or config.roadmap_start_date or date.today()

        # Buscar todas as histórias
        stories = self._story_repository.find_all()

        # Limpar alocações anteriores
        for story in stories:
            if story.developer_id:
                story.deallocate_developer()
                self._story_repository.save(story)

        # Ordenar por dependências + prioridade
        sorted_stories = self._backlog_sorter.sort(stories)

        # ✅ CALCULAR CRONOGRAMA COM DATA CONFIGURADA
        scheduled_stories = self._schedule_calculator.calculate(
            sorted_stories,
            config,
            effective_start_date  # ✅ USAR DATA DETERMINADA
        )

        # Atualizar prioridades e salvar
        for index, story in enumerate(scheduled_stories):
            story.priority = index
            self._story_repository.save(story)

        # Calcular metadados
        total_sp = sum(s.story_point.value for s in scheduled_stories)
        if scheduled_stories:
            first_start = min(s.start_date for s in scheduled_stories if s.start_date)
            last_end = max(s.end_date for s in scheduled_stories if s.end_date)
            duration_days = (last_end - first_start).days + 1 if first_start and last_end else 0
        else:
            duration_days = 0

        return BacklogDTO(
            stories=[story_to_dto(s) for s in scheduled_stories],
            total_count=len(scheduled_stories),
            total_story_points=total_sp,
            estimated_duration_days=duration_days
        )
```

**Justificativa:**
- `UpdateConfigurationUseCase` aceita a nova data como parâmetro
- `CalculateScheduleUseCase` usa hierarquia de precedência para determinar data de início
- Mantém compatibilidade com código existente (parâmetro opcional)

---

### Camada 4: Presentation (Interface Gráfica)

#### Modificar: `backlog_manager/presentation/views/configuration_dialog.py`

**Criar se não existir, ou modificar dialog existente:**

```python
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QSpinBox, QDateEdit, QPushButton, QHBoxLayout,
    QMessageBox
)
from PySide6.QtCore import QDate, Qt
from datetime import date, timedelta

class ConfigurationDialog(QDialog):
    """Dialog para configurar parâmetros globais do sistema."""

    def __init__(self, current_config, parent=None):
        super().__init__(parent)
        self._current_config = current_config
        self._setup_ui()
        self._load_current_config()

    def _setup_ui(self):
        """Configura interface do dialog."""
        self.setWindowTitle("Configurações do Sistema")
        self.setMinimumWidth(450)

        layout = QVBoxLayout()

        # Formulário
        form_layout = QFormLayout()

        # Story Points por Sprint
        self.sp_spinbox = QSpinBox()
        self.sp_spinbox.setMinimum(1)
        self.sp_spinbox.setMaximum(999)
        self.sp_spinbox.setValue(21)
        self.sp_spinbox.valueChanged.connect(self._update_velocity_label)
        form_layout.addRow("Story Points por Sprint:", self.sp_spinbox)

        # Dias Úteis por Sprint
        self.workdays_spinbox = QSpinBox()
        self.workdays_spinbox.setMinimum(1)
        self.workdays_spinbox.setMaximum(30)
        self.workdays_spinbox.setValue(15)
        self.workdays_spinbox.valueChanged.connect(self._update_velocity_label)
        form_layout.addRow("Dias Úteis por Sprint:", self.workdays_spinbox)

        # ✅ NOVO: Data de Início do Roadmap
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)  # Dropdown com calendário
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setMinimumDate(QDate.currentDate())  # Não permitir datas passadas
        self.date_edit.dateChanged.connect(self._validate_workday)

        # Layout para data + checkbox "Usar data atual"
        date_layout = QHBoxLayout()
        date_layout.addWidget(self.date_edit)

        self.use_current_date_btn = QPushButton("Usar Data Atual")
        self.use_current_date_btn.clicked.connect(self._set_current_date)
        date_layout.addWidget(self.use_current_date_btn)

        form_layout.addRow("Data de Início do Roadmap:", date_layout)

        # Label de velocidade calculada
        self.velocity_label = QLabel()
        self.velocity_label.setStyleSheet("color: #666; font-style: italic;")
        form_layout.addRow("Velocidade Calculada:", self.velocity_label)

        layout.addLayout(form_layout)

        # Aviso sobre dias úteis
        warning_label = QLabel(
            "⚠️ A data de início deve ser um dia útil (segunda a sexta). "
            "Se selecionar fim de semana, será ajustada automaticamente."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #FF8C00; padding: 10px; background-color: #FFF8DC; border-radius: 5px;")
        layout.addWidget(warning_label)

        # Botões
        button_layout = QHBoxLayout()

        restore_btn = QPushButton("Restaurar Padrões")
        restore_btn.clicked.connect(self._restore_defaults)
        button_layout.addWidget(restore_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Salvar")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self._update_velocity_label()

    def _load_current_config(self):
        """Carrega configuração atual nos campos."""
        self.sp_spinbox.setValue(self._current_config.story_points_per_sprint)
        self.workdays_spinbox.setValue(self._current_config.workdays_per_sprint)

        # ✅ CARREGAR DATA CONFIGURADA
        if self._current_config.roadmap_start_date:
            qdate = QDate(
                self._current_config.roadmap_start_date.year,
                self._current_config.roadmap_start_date.month,
                self._current_config.roadmap_start_date.day
            )
            self.date_edit.setDate(qdate)
        else:
            # Se não houver data configurada, usar data atual
            self.date_edit.setDate(QDate.currentDate())

    def _update_velocity_label(self):
        """Atualiza label de velocidade calculada."""
        sp = self.sp_spinbox.value()
        workdays = self.workdays_spinbox.value()
        velocity = sp / workdays
        self.velocity_label.setText(f"{velocity:.2f} SP/dia")

    def _validate_workday(self, qdate: QDate):
        """
        Valida se a data selecionada é um dia útil.
        Se for fim de semana, ajusta para próxima segunda-feira.
        """
        python_date = date(qdate.year(), qdate.month(), qdate.day())

        # Se for fim de semana (sábado=5, domingo=6), ajustar
        if python_date.weekday() >= 5:
            # Calcular próxima segunda-feira
            days_until_monday = 7 - python_date.weekday()
            next_monday = python_date + timedelta(days=days_until_monday)

            # Atualizar QDateEdit
            self.date_edit.setDate(QDate(next_monday.year, next_monday.month, next_monday.day))

            QMessageBox.information(
                self,
                "Dia Útil Requerido",
                f"Fim de semana não é permitido. Data ajustada para {next_monday.strftime('%d/%m/%Y')} (segunda-feira)."
            )

    def _set_current_date(self):
        """Define data de início como data atual."""
        current_date = date.today()
        # Se hoje for fim de semana, ajustar para próxima segunda
        if current_date.weekday() >= 5:
            days_until_monday = 7 - current_date.weekday()
            current_date = current_date + timedelta(days=days_until_monday)

        self.date_edit.setDate(QDate(current_date.year, current_date.month, current_date.day))

    def _restore_defaults(self):
        """Restaura valores padrão."""
        self.sp_spinbox.setValue(21)
        self.workdays_spinbox.setValue(15)
        self._set_current_date()

    def _save(self):
        """Valida e salva configuração."""
        # Converter QDate para date
        qdate = self.date_edit.date()
        python_date = date(qdate.year(), qdate.month(), qdate.day())

        # Última validação de dia útil
        if python_date.weekday() >= 5:
            QMessageBox.warning(
                self,
                "Data Inválida",
                "A data de início deve ser um dia útil (segunda a sexta)."
            )
            return

        self.accept()

    def get_configuration_data(self):
        """
        Retorna dados da configuração.

        Returns:
            Tupla (story_points_per_sprint, workdays_per_sprint, roadmap_start_date)
        """
        qdate = self.date_edit.date()
        python_date = date(qdate.year(), qdate.month(), qdate.day())

        return (
            self.sp_spinbox.value(),
            self.workdays_spinbox.value(),
            python_date  # ✅ RETORNAR DATA
        )
```

#### Modificar: Controller que abre o dialog de configurações

```python
class MainController:
    """Controller principal da aplicação."""

    def _on_configure_settings(self):
        """Abre dialog de configurações."""
        # Buscar configuração atual
        current_config = self._get_configuration_use_case.execute()

        # Abrir dialog
        dialog = ConfigurationDialog(current_config, parent=self._view)

        if dialog.exec() == QDialog.Accepted:
            # Obter dados do dialog
            sp_per_sprint, workdays, start_date = dialog.get_configuration_data()  # ✅ INCLUIR DATA

            try:
                # Salvar nova configuração
                updated_config = self._update_configuration_use_case.execute(
                    story_points_per_sprint=sp_per_sprint,
                    workdays_per_sprint=workdays,
                    roadmap_start_date=start_date  # ✅ PASSAR DATA
                )

                QMessageBox.information(
                    self._view,
                    "Configuração Salva",
                    "Configurações atualizadas com sucesso!\n\n"
                    "Execute o cálculo de cronograma para aplicar as mudanças."
                )

            except ValueError as e:
                QMessageBox.warning(
                    self._view,
                    "Erro de Validação",
                    str(e)
                )
```

**Justificativa:**
- Adiciona `QDateEdit` com calendário dropdown para seleção de data
- Validação automática de dias úteis (ajusta fins de semana para segunda-feira)
- Botão "Usar Data Atual" para conveniência
- Warning visual sobre requisito de dia útil

---

### Camada 5: Dependency Injection (DI Container)

#### Modificar: `backlog_manager/presentation/di_container.py`

Nenhuma mudança necessária - os use cases já estão registrados e aceitam os novos parâmetros como opcionais.

---

## SEQUÊNCIA DE IMPLEMENTAÇÃO

### Fase 1: Domain Layer (30 min)
1. ✅ Adicionar campo `roadmap_start_date` em `Configuration`
2. ✅ Adicionar validação de dia útil em `Configuration._validate()`
3. ✅ Executar testes unitários de `Configuration`

### Fase 2: Infrastructure Layer (45 min)
4. ✅ Modificar `schema.sql` para adicionar coluna `roadmap_start_date`
5. ✅ Criar script de migration `001_add_roadmap_start_date.py`
6. ✅ Atualizar `SQLiteConfigurationRepository.get()` para ler a data
7. ✅ Atualizar `SQLiteConfigurationRepository.save()` para salvar a data
8. ✅ Executar migration em banco de teste
9. ✅ Executar testes de integração do repository

### Fase 3: Application Layer (30 min)
10. ✅ Modificar `UpdateConfigurationUseCase.execute()` para aceitar `roadmap_start_date`
11. ✅ Modificar `CalculateScheduleUseCase.execute()` para usar data configurada
12. ✅ Atualizar testes unitários dos use cases

### Fase 4: Presentation Layer (60 min)
13. ✅ Criar/modificar `ConfigurationDialog` para incluir `QDateEdit`
14. ✅ Implementar validação de dia útil no dialog
15. ✅ Adicionar botão "Usar Data Atual"
16. ✅ Modificar controller para passar a data ao use case
17. ✅ Testar fluxo completo na interface

### Fase 5: Testes de Integração (30 min)
18. ✅ Testar configuração + persistência + restauração
19. ✅ Testar cálculo de cronograma com data configurada
20. ✅ Testar comportamento com data NULL (fallback para today)
21. ✅ Testar validação de fins de semana

### Fase 6: Documentação (15 min)
22. ✅ Atualizar `CLAUDE.md` com nova funcionalidade
23. ✅ Atualizar `requisitos_novo.md` marcando requisito como implementado

---

## TESTES

### Testes Unitários - Domain

**Arquivo:** `tests/unit/domain/entities/test_configuration.py`

```python
def test_configuration_with_roadmap_start_date():
    """Testa criação de configuração com data de início."""
    start_date = date(2025, 1, 6)  # Segunda-feira
    config = Configuration(
        story_points_per_sprint=21,
        workdays_per_sprint=15,
        roadmap_start_date=start_date
    )
    assert config.roadmap_start_date == start_date

def test_configuration_rejects_weekend_start_date():
    """Testa que configuração rejeita data de fim de semana."""
    saturday = date(2025, 1, 4)  # Sábado
    with pytest.raises(ValueError, match="dia útil"):
        Configuration(
            story_points_per_sprint=21,
            workdays_per_sprint=15,
            roadmap_start_date=saturday
        )

def test_configuration_accepts_none_start_date():
    """Testa que data None é aceita (comportamento padrão)."""
    config = Configuration(
        story_points_per_sprint=21,
        workdays_per_sprint=15,
        roadmap_start_date=None
    )
    assert config.roadmap_start_date is None
```

### Testes de Integração - Infrastructure

**Arquivo:** `tests/integration/infrastructure/database/repositories/test_sqlite_configuration_repository.py`

```python
def test_save_and_get_configuration_with_roadmap_start_date(repository):
    """Testa persistência de configuração com data de início."""
    start_date = date(2025, 2, 10)  # Segunda-feira
    config = Configuration(
        story_points_per_sprint=30,
        workdays_per_sprint=20,
        roadmap_start_date=start_date
    )

    repository.save(config)
    retrieved = repository.get()

    assert retrieved.story_points_per_sprint == 30
    assert retrieved.workdays_per_sprint == 20
    assert retrieved.roadmap_start_date == start_date

def test_save_configuration_with_none_start_date(repository):
    """Testa persistência de configuração sem data (NULL)."""
    config = Configuration(
        story_points_per_sprint=21,
        workdays_per_sprint=15,
        roadmap_start_date=None
    )

    repository.save(config)
    retrieved = repository.get()

    assert retrieved.roadmap_start_date is None
```

### Testes de Integração - Use Cases

**Arquivo:** `tests/integration/application/use_cases/test_calculate_schedule_with_start_date.py`

```python
def test_calculate_schedule_uses_configured_start_date(
    calculate_schedule_use_case,
    story_repository,
    configuration_repository
):
    """Testa que cronograma usa data configurada."""
    # Configurar data de início
    start_date = date(2025, 3, 17)  # Segunda-feira
    config = Configuration(
        story_points_per_sprint=21,
        workdays_per_sprint=15,
        roadmap_start_date=start_date
    )
    configuration_repository.save(config)

    # Criar histórias
    story1 = Story(id="S1", feature="A", name="Task 1", story_point=StoryPoint(5), ...)
    story_repository.save(story1)

    # Calcular cronograma
    result = calculate_schedule_use_case.execute()

    # Verificar que história começa na data configurada
    scheduled = [s for s in result.stories if s.id == "S1"][0]
    assert scheduled.start_date >= start_date
    assert scheduled.start_date.weekday() < 5  # Dia útil

def test_calculate_schedule_with_none_config_uses_today(
    calculate_schedule_use_case,
    story_repository,
    configuration_repository
):
    """Testa que cronograma usa date.today() quando config é None."""
    # Configurar sem data de início
    config = Configuration(
        story_points_per_sprint=21,
        workdays_per_sprint=15,
        roadmap_start_date=None
    )
    configuration_repository.save(config)

    # Criar histórias
    story1 = Story(id="S1", feature="A", name="Task 1", story_point=StoryPoint(5), ...)
    story_repository.save(story1)

    # Calcular cronograma
    result = calculate_schedule_use_case.execute()

    # Verificar que história começa em data >= hoje
    scheduled = [s for s in result.stories if s.id == "S1"][0]
    assert scheduled.start_date >= date.today()
```

---

## VALIDAÇÕES E REGRAS DE NEGÓCIO

### Validação 1: Data deve ser dia útil (segunda a sexta)
- **Onde:** `Configuration._validate()`
- **Comportamento:** Lança `ValueError` se `roadmap_start_date.weekday() >= 5`
- **Interface:** Dialog ajusta automaticamente para próxima segunda

### Validação 2: Data não pode ser anterior a hoje
- **Onde:** `QDateEdit.setMinimumDate(QDate.currentDate())`
- **Comportamento:** Datepicker não permite selecionar datas passadas
- **Exceção:** Pode permitir datas passadas se for requisito de planejamento retroativo

### Validação 3: Data é opcional (pode ser None/NULL)
- **Onde:** `Configuration`, `CalculateScheduleUseCase`
- **Comportamento:** Se `None`, usar `date.today()` como fallback
- **Persistência:** Coluna `roadmap_start_date` é `nullable` no banco

---

## IMPACTO EM FUNCIONALIDADES EXISTENTES

### ✅ NÃO IMPACTA (Compatibilidade Mantida)

1. **Cálculo de Cronograma**
   - `ScheduleCalculator.calculate()` já aceita `start_date` opcional
   - Comportamento padrão (`date.today()`) preservado
   - Algoritmo de dias úteis não muda

2. **Alocação de Desenvolvedores**
   - Usa datas calculadas pelo `ScheduleCalculator`
   - Não depende da origem da data de início
   - Algoritmo de load balancing intacto

3. **Persistência de Histórias**
   - Campos `start_date` e `end_date` já existem
   - Formato ISO já implementado
   - Sem mudanças no schema de `stories`

4. **Ordenação de Backlog**
   - Usa dependências + prioridade
   - Não depende de datas
   - `BacklogSorter` intacto

---

## PONTOS DE ATENÇÃO

### ⚠️ Migration de Banco de Dados
- Bancos existentes precisarão da migration para adicionar coluna
- Script deve ser idempotente (não falhar se coluna já existir)
- Testar com banco real antes de distribuir

### ⚠️ Validação de Dia Útil
- Fins de semana devem ser automaticamente ajustados
- Interface deve avisar o usuário claramente
- Domain deve rejeitar valores inválidos

### ⚠️ Compatibilidade com Código Existente
- Parâmetro `roadmap_start_date` deve ser opcional em todas as camadas
- Fallback para `date.today()` garantido
- Testes existentes não devem quebrar

### ⚠️ UX do Datepicker
- QDateEdit deve ter calendário dropdown (QCalendarPopup)
- Formato brasileiro: dd/MM/yyyy
- Botão "Usar Data Atual" para conveniência

---

## CHECKLIST DE IMPLEMENTAÇÃO

- [ ] **Domain:** Adicionar `roadmap_start_date` em `Configuration`
- [ ] **Domain:** Validar dia útil em `Configuration._validate()`
- [ ] **Domain:** Testes unitários de `Configuration`
- [ ] **Infrastructure:** Modificar `schema.sql` (adicionar coluna)
- [ ] **Infrastructure:** Criar script de migration
- [ ] **Infrastructure:** Atualizar `SQLiteConfigurationRepository.get()`
- [ ] **Infrastructure:** Atualizar `SQLiteConfigurationRepository.save()`
- [ ] **Infrastructure:** Testes de integração do repository
- [ ] **Application:** Modificar `UpdateConfigurationUseCase`
- [ ] **Application:** Modificar `CalculateScheduleUseCase`
- [ ] **Application:** Testes de integração dos use cases
- [ ] **Presentation:** Criar/modificar `ConfigurationDialog`
- [ ] **Presentation:** Adicionar `QDateEdit` com calendário
- [ ] **Presentation:** Implementar validação de dia útil
- [ ] **Presentation:** Adicionar botão "Usar Data Atual"
- [ ] **Presentation:** Modificar controller para passar data
- [ ] **E2E:** Testar fluxo completo (configurar → persistir → restaurar → calcular)
- [ ] **E2E:** Testar validação de fins de semana
- [ ] **E2E:** Testar fallback para `date.today()` quando NULL
- [ ] **Docs:** Atualizar `CLAUDE.md`
- [ ] **Docs:** Atualizar `requisitos_novo.md`

---

## ESTIMATIVA DE ESFORÇO

| Fase | Story Points | Tempo Estimado |
|------|--------------|----------------|
| Domain Layer | 2 SP | 30 min |
| Infrastructure Layer | 5 SP | 45 min |
| Application Layer | 3 SP | 30 min |
| Presentation Layer | 5 SP | 60 min |
| Testes de Integração | 3 SP | 30 min |
| Documentação | 1 SP | 15 min |
| **TOTAL** | **19 SP** | **3h 30min** |

---

## REFERÊNCIAS

- **Requisitos:** `requisitos_novo.md` (RF-019 - Configurar Velocidade do Time)
- **Arquitetura:** `CLAUDE.md` (Clean Architecture guidelines)
- **Domain:** `backlog_manager/domain/entities/configuration.py`
- **Infrastructure:** `backlog_manager/infrastructure/database/schema.sql`
- **Use Cases:** `backlog_manager/application/use_cases/schedule/calculate_schedule.py`
- **Qt Documentation:** [QDateEdit Class](https://doc.qt.io/qt-6/qdateedit.html)

---

**Fim do Plano de Implementação**
