# PLANO DE REVISÃO: Calcular Cronograma e Alocar Desenvolvedores

**Projeto:** Backlog Manager
**Versão:** 1.0
**Data:** 20/12/2025
**Objetivo:** Revisar e corrigir comportamento de Calcular Cronograma e Alocar Desenvolvedores

---

## 📋 ÍNDICE
1. [Análise do Estado Atual](#análise-do-estado-atual)
2. [Requisitos e Mudanças Necessárias](#requisitos-e-mudanças-necessárias)
3. [Arquitetura da Solução](#arquitetura-da-solução)
4. [Plano de Implementação](#plano-de-implementação)
5. [Critérios de Aceitação](#critérios-de-aceitação)
6. [Casos de Teste](#casos-de-teste)

---

## 🔍 ANÁLISE DO ESTADO ATUAL

### Comportamento Atual: Calcular Cronograma

**Arquivo:** `application/use_cases/schedule/calculate_schedule.py`

**Fluxo Atual:**
1. ✅ Busca todas as histórias do repositório
2. ✅ Ordena por dependências (ordenação topológica)
3. ✅ Ordena por prioridade
4. ✅ Calcula início, fim e duração
5. ❌ **NÃO limpa desenvolvedores das histórias**
6. ✅ Usa configuração de velocidade (`velocity_per_day`)

**Problemas Identificados:**
- ❌ Não remove desenvolvedores antes de calcular
- ❌ Histórias mantêm alocações antigas que podem não fazer sentido após reordenação

---

### Comportamento Atual: Alocar Desenvolvedores

**Arquivo:** `application/use_cases/schedule/allocate_developers.py`

**Fluxo Atual:**
1. ✅ Filtra histórias sem desenvolvedor (`developer_id = None`)
2. ✅ Busca todos os desenvolvedores
3. ❌ **Usa distribuição round-robin simples** (não considera carga)
4. ❌ **NÃO recalcula datas** após alocar
5. ❌ **NÃO detecta gaps/ociosidade**
6. ❌ **NÃO mostra warnings ao usuário**

**Problemas Identificados:**
- ❌ Distribuição não considera balanceamento de carga (quem tem menos histórias)
- ❌ Datas de início/fim não são ajustadas após alocação
- ❌ Não há detecção de ociosidade por gaps de dependência
- ❌ Sem feedback ao usuário sobre problemas

---

### Estado Atual: Interface

**Arquivo:** `presentation/views/main_window.py`

**Toolbar Atual:**
1. Nova História
2. Editar
3. Deletar
4. Importar Excel
5. Exportar Excel
6. **Calcular Cronograma**
7. ❌ **FALTANDO: Alocar Desenvolvedores** (só existe no menu)

**Problema:**
- ❌ Botão "Alocar Desenvolvedores" não está na toolbar

---

## 📊 REQUISITOS E MUDANÇAS NECESSÁRIAS

### RF-REV-001: Revisão do Calcular Cronograma

**Descrição:** Ajustar comportamento para limpar desenvolvedores antes de calcular.

**Comportamento Esperado:**
1. ✨ **Limpar todos os desenvolvedores** (`developer_id = None` em todas as histórias)
2. ✅ Reordenar por dependências (já existe)
3. ✅ Reordenar por prioridade (já existe)
4. ✅ Calcular início, fim e duração (já existe)
5. ✅ Considerar velocidade do time (já existe)

**Mudanças Necessárias:**
```python
# ADICIONAR no início do execute():
for story in stories:
    story.deallocate_developer()  # Remove desenvolvedor
    self._story_repo.save(story)
```

**Justificativa:**
- Garante que alocações antigas não interfiram no novo cronograma
- Histórias começam "limpas" para posterior alocação inteligente

**Prioridade:** Alta
**Estimativa:** 2 SP

---

### RF-REV-002: Revisão do Alocar Desenvolvedores

**Descrição:** Implementar alocação inteligente com balanceamento de carga.

**Comportamento Esperado:**
1. ✅ Filtrar histórias sem desenvolvedor (já existe)
2. ✨ **Alocar priorizando desenvolvedor com MENOS histórias no backlog**
3. ✨ **Recalcular datas de início/fim** após cada alocação
4. ✨ **Detectar gaps de ociosidade** (1-2 dias entre histórias do mesmo dev)
5. ✨ **Mostrar warning ao usuário** sobre ociosidade detectada

**Algoritmo de Alocação (Novo):**
```python
# Para cada história sem desenvolvedor (em ordem):
1. Contar histórias já alocadas para cada desenvolvedor
2. Selecionar desenvolvedor com MENOR contagem
3. Alocar desenvolvedor à história
4. Recalcular start_date e end_date baseado em:
   - Dependências da história
   - Última história do desenvolvedor
5. Detectar gap entre histórias do desenvolvedor:
   - Se gap >= 1 dia útil: registrar warning
6. Salvar história
```

**Detecção de Ociosidade:**
```python
# Para cada desenvolvedor:
historias_dev = [h for h in todas_historias if h.developer_id == dev_id]
historias_dev.sort(key=lambda h: h.start_date)

for i in range(len(historias_dev) - 1):
    h_atual = historias_dev[i]
    h_proxima = historias_dev[i + 1]

    gap_dias = calcular_dias_uteis(h_atual.end_date + 1, h_proxima.start_date - 1)

    if gap_dias >= 1:
        warnings.append(f"Dev {dev_id}: {gap_dias} dia(s) ocioso(s) entre {h_atual.id} e {h_proxima.id}")
```

**Prioridade:** Alta
**Estimativa:** 8 SP

---

### RF-REV-003: Adicionar Botão na Toolbar

**Descrição:** Adicionar botão "Alocar Desenvolvedores" na toolbar.

**Posição:** Ao lado direito de "Calcular Cronograma"

**Toolbar Final:**
1. Nova História
2. Editar
3. Deletar
4. Importar Excel
5. Exportar Excel
6. Calcular Cronograma
7. ✨ **Alocar Desenvolvedores** (NOVO)

**Mudanças Necessárias:**
```python
# main_window.py - Método _create_toolbar()

# Adicionar botão após "Calcular Cronograma"
self._allocate_developers_action = QAction(
    QIcon.fromTheme("system-users"),
    "Alocar Desenvolvedores",
    self
)
self._allocate_developers_action.setShortcut("Shift+F5")
self._allocate_developers_action.setStatusTip("Distribuir desenvolvedores automaticamente")
self._allocate_developers_action.triggered.connect(
    self._on_allocate_developers_requested
)
toolbar.addAction(self._allocate_developers_action)
```

**Prioridade:** Média
**Estimativa:** 1 SP

---

## 🏗️ ARQUITETURA DA SOLUÇÃO

### Componentes a Modificar

```
application/use_cases/schedule/
├── calculate_schedule.py          # ⚠️ MODIFICAR - Adicionar limpeza de devs
└── allocate_developers.py         # ⚠️ MODIFICAR - Implementar alocação inteligente

domain/services/
└── developer_load_balancer.py     # ✨ CRIAR - Serviço para balancear carga

presentation/views/
└── main_window.py                  # ⚠️ MODIFICAR - Adicionar botão na toolbar

presentation/utils/
└── allocation_report_dialog.py    # ✨ CRIAR - Dialog para mostrar warnings
```

---

## 📋 PLANO DE IMPLEMENTAÇÃO

### FASE 1: Adicionar Limpeza no Calcular Cronograma (2 SP) 🧹

**Objetivo:** Limpar desenvolvedores antes de calcular cronograma.

#### 1.1 Modificar CalculateScheduleUseCase

**Arquivo:** `application/use_cases/schedule/calculate_schedule.py`

```python
def execute(self) -> BacklogDTO:
    """
    Calcula cronograma completo do backlog.

    **NOVO COMPORTAMENTO:**
    1. Limpa todos os desenvolvedores das histórias
    2. Ordena por dependências e prioridade
    3. Calcula datas

    Returns:
        BacklogDTO com histórias ordenadas e calculadas
    """
    # Buscar histórias e configuração
    stories = self._story_repo.find_all()
    if not stories:
        return BacklogDTO(stories=[], total_stories=0, total_story_points=0, estimated_duration=0)

    # **NOVO: Limpar desenvolvedores de todas as histórias**
    for story in stories:
        if story.developer_id:
            story.deallocate_developer()
            self._story_repo.save(story)

    # Configuração
    config = self._config_repo.get()

    # Ordenar backlog (dependências + prioridade)
    sorted_stories = self._sorter.sort(stories)

    # Calcular cronograma
    calculated_stories = self._calculator.calculate(sorted_stories, config)

    # Atualizar prioridades baseado na ordem final
    for index, story in enumerate(calculated_stories, start=1):
        story.priority = index
        self._story_repo.save(story)

    # Calcular métricas
    total_points = sum(s.story_point.value for s in calculated_stories)
    estimated_duration = self._calculate_total_duration(calculated_stories)

    # Converter para DTOs
    story_dtos = [StoryDTO.from_entity(s) for s in calculated_stories]

    return BacklogDTO(
        stories=story_dtos,
        total_stories=len(story_dtos),
        total_story_points=total_points,
        estimated_duration=estimated_duration
    )
```

**Testes:**
- [ ] Histórias com desenvolvedores têm `developer_id` limpo após calcular
- [ ] Ordenação e cálculo de datas funcionam normalmente
- [ ] Todas as histórias salvas corretamente

**Estimativa:** 2 SP

---

### FASE 2: Criar Serviço de Balanceamento de Carga (3 SP) ⚖️

**Objetivo:** Criar serviço de domínio para balancear alocação.

#### 2.1 Criar DeveloperLoadBalancer

**Arquivo:** `domain/services/developer_load_balancer.py`

```python
"""Serviço para balancear carga de desenvolvedores."""
from typing import List, Dict
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.entities.developer import Developer


class DeveloperLoadBalancer:
    """
    Serviço de domínio para balancear carga entre desenvolvedores.

    Garante distribuição equitativa de histórias considerando
    a carga atual de cada desenvolvedor.
    """

    @staticmethod
    def select_least_loaded_developer(
        developers: List[Developer],
        all_stories: List[Story]
    ) -> Developer:
        """
        Seleciona desenvolvedor com MENOR número de histórias alocadas.

        Args:
            developers: Lista de desenvolvedores disponíveis
            all_stories: Lista de todas as histórias (para contar carga)

        Returns:
            Desenvolvedor com menor carga

        Raises:
            ValueError: Se lista de desenvolvedores estiver vazia
        """
        if not developers:
            raise ValueError("Lista de desenvolvedores não pode estar vazia")

        # Contar histórias por desenvolvedor
        load_count = DeveloperLoadBalancer._count_stories_per_developer(
            developers, all_stories
        )

        # Selecionar desenvolvedor com menor carga
        # Em caso de empate, retorna o primeiro da lista
        least_loaded_dev = min(
            developers,
            key=lambda dev: load_count.get(dev.id, 0)
        )

        return least_loaded_dev

    @staticmethod
    def _count_stories_per_developer(
        developers: List[Developer],
        all_stories: List[Story]
    ) -> Dict[str, int]:
        """
        Conta número de histórias alocadas para cada desenvolvedor.

        Args:
            developers: Lista de desenvolvedores
            all_stories: Lista de todas as histórias

        Returns:
            Dicionário {developer_id: contagem}
        """
        load_count = {dev.id: 0 for dev in developers}

        for story in all_stories:
            if story.developer_id and story.developer_id in load_count:
                load_count[story.developer_id] += 1

        return load_count

    @staticmethod
    def get_load_report(
        developers: List[Developer],
        all_stories: List[Story]
    ) -> Dict[str, int]:
        """
        Gera relatório de carga por desenvolvedor.

        Args:
            developers: Lista de desenvolvedores
            all_stories: Lista de histórias

        Returns:
            Dicionário {developer_id: contagem}
        """
        return DeveloperLoadBalancer._count_stories_per_developer(
            developers, all_stories
        )
```

**Testes:**
- [ ] Seleciona desenvolvedor com menos histórias
- [ ] Em caso de empate, retorna primeiro da lista
- [ ] Lança erro se lista de desenvolvedores vazia
- [ ] Conta corretamente histórias por desenvolvedor
- [ ] Ignora histórias sem desenvolvedor

**Estimativa:** 3 SP

---

### FASE 3: Criar Detector de Ociosidade (3 SP) 🔍

**Objetivo:** Detectar gaps de ociosidade entre histórias.

#### 3.1 Criar IdlenessDetector

**Arquivo:** `domain/services/idleness_detector.py`

```python
"""Serviço para detectar ociosidade de desenvolvedores."""
from typing import List, Dict
from datetime import date, timedelta
from dataclasses import dataclass
from backlog_manager.domain.entities.story import Story


@dataclass
class IdlenessWarning:
    """Representa um aviso de ociosidade."""
    developer_id: str
    gap_days: int
    story_before_id: str
    story_after_id: str
    idle_start: date
    idle_end: date

    def __str__(self) -> str:
        return (
            f"Desenvolvedor {self.developer_id}: {self.gap_days} dia(s) ocioso(s) "
            f"entre {self.story_before_id} e {self.story_after_id} "
            f"({self.idle_start} - {self.idle_end})"
        )


class IdlenessDetector:
    """
    Serviço de domínio para detectar ociosidade de desenvolvedores.

    Identifica gaps de 1+ dias úteis entre histórias consecutivas
    do mesmo desenvolvedor.
    """

    @staticmethod
    def detect_idleness(
        all_stories: List[Story],
        min_gap_days: int = 1
    ) -> List[IdlenessWarning]:
        """
        Detecta ociosidade de desenvolvedores.

        Args:
            all_stories: Lista de todas as histórias
            min_gap_days: Mínimo de dias para considerar gap (padrão: 1)

        Returns:
            Lista de warnings de ociosidade
        """
        warnings = []

        # Agrupar histórias por desenvolvedor
        stories_by_dev = IdlenessDetector._group_stories_by_developer(all_stories)

        # Analisar cada desenvolvedor
        for dev_id, dev_stories in stories_by_dev.items():
            # Ordenar por data de início
            sorted_stories = sorted(
                [s for s in dev_stories if s.start_date and s.end_date],
                key=lambda s: s.start_date
            )

            # Detectar gaps entre histórias consecutivas
            for i in range(len(sorted_stories) - 1):
                story_before = sorted_stories[i]
                story_after = sorted_stories[i + 1]

                # Calcular gap em dias úteis
                gap = IdlenessDetector._calculate_workday_gap(
                    story_before.end_date,
                    story_after.start_date
                )

                if gap >= min_gap_days:
                    warning = IdlenessWarning(
                        developer_id=dev_id,
                        gap_days=gap,
                        story_before_id=story_before.id,
                        story_after_id=story_after.id,
                        idle_start=story_before.end_date + timedelta(days=1),
                        idle_end=story_after.start_date - timedelta(days=1)
                    )
                    warnings.append(warning)

        return warnings

    @staticmethod
    def _group_stories_by_developer(
        stories: List[Story]
    ) -> Dict[str, List[Story]]:
        """
        Agrupa histórias por desenvolvedor.

        Args:
            stories: Lista de histórias

        Returns:
            Dicionário {developer_id: [histórias]}
        """
        grouped = {}
        for story in stories:
            if story.developer_id:
                if story.developer_id not in grouped:
                    grouped[story.developer_id] = []
                grouped[story.developer_id].append(story)
        return grouped

    @staticmethod
    def _calculate_workday_gap(end_date: date, start_date: date) -> int:
        """
        Calcula gap em dias úteis entre duas datas.

        Args:
            end_date: Data fim da primeira história
            start_date: Data início da segunda história

        Returns:
            Número de dias úteis entre as datas (exclusivo)
        """
        if start_date <= end_date:
            return 0

        # Contar dias úteis entre end_date+1 e start_date-1
        current = end_date + timedelta(days=1)
        end = start_date
        workdays = 0

        while current < end:
            if current.weekday() < 5:  # 0-4 = seg-sex
                workdays += 1
            current += timedelta(days=1)

        return workdays
```

**Testes:**
- [ ] Detecta gap de 1 dia entre histórias
- [ ] Detecta gap de 2+ dias
- [ ] Ignora gaps de fim de semana
- [ ] Ignora histórias sem datas
- [ ] Agrupa corretamente por desenvolvedor
- [ ] Retorna lista vazia se não houver gaps

**Estimativa:** 3 SP

---

### FASE 4: Reimplementar AllocateDevelopersUseCase (5 SP) 🔄

**Objetivo:** Implementar alocação inteligente com balanceamento.

#### 4.1 Modificar AllocateDevelopersUseCase

**Arquivo:** `application/use_cases/schedule/allocate_developers.py`

```python
"""Caso de uso para alocar desenvolvedores automaticamente."""
from typing import List, Tuple
from backlog_manager.application.interfaces.repositories.story_repository import (
    StoryRepository
)
from backlog_manager.application.interfaces.repositories.developer_repository import (
    DeveloperRepository
)
from backlog_manager.application.interfaces.repositories.configuration_repository import (
    ConfigurationRepository
)
from backlog_manager.domain.services.developer_load_balancer import DeveloperLoadBalancer
from backlog_manager.domain.services.idleness_detector import IdlenessDetector, IdlenessWarning
from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator
from backlog_manager.domain.exceptions import NoDevelopersAvailableException


class AllocateDevelopersUseCase:
    """
    Aloca desenvolvedores automaticamente em histórias sem alocação.

    **COMPORTAMENTO REVISADO:**
    - Usa balanceamento de carga (dev com menos histórias)
    - Recalcula datas após cada alocação
    - Detecta e reporta ociosidade
    """

    def __init__(
        self,
        story_repository: StoryRepository,
        developer_repository: DeveloperRepository,
        configuration_repository: ConfigurationRepository,
        load_balancer: DeveloperLoadBalancer,
        idleness_detector: IdlenessDetector,
        schedule_calculator: ScheduleCalculator
    ):
        self._story_repo = story_repository
        self._developer_repo = developer_repository
        self._config_repo = configuration_repository
        self._load_balancer = load_balancer
        self._idleness_detector = idleness_detector
        self._calculator = schedule_calculator

    def execute(self) -> Tuple[int, List[IdlenessWarning]]:
        """
        Aloca desenvolvedores e detecta ociosidade.

        Returns:
            Tupla (total_alocado, lista_de_warnings)

        Raises:
            NoDevelopersAvailableException: Se não houver desenvolvedores
        """
        # Buscar dados
        all_stories = self._story_repo.find_all()
        unallocated_stories = [s for s in all_stories if not s.developer_id]

        if not unallocated_stories:
            return 0, []  # Nada a alocar

        developers = self._developer_repo.find_all()
        if not developers:
            raise NoDevelopersAvailableException(
                "Não há desenvolvedores cadastrados para alocar"
            )

        config = self._config_repo.get()
        allocated_count = 0

        # Alocar cada história sem desenvolvedor
        for story in unallocated_stories:
            # Selecionar desenvolvedor com MENOR carga
            selected_dev = self._load_balancer.select_least_loaded_developer(
                developers, all_stories
            )

            # Alocar
            story.allocate_developer(selected_dev.id)

            # Recalcular datas desta história
            self._recalculate_story_dates(story, all_stories, config)

            # Salvar
            self._story_repo.save(story)
            allocated_count += 1

        # Detectar ociosidade após todas as alocações
        warnings = self._idleness_detector.detect_idleness(all_stories)

        return allocated_count, warnings

    def _recalculate_story_dates(
        self,
        story,
        all_stories,
        config
    ) -> None:
        """
        Recalcula datas de início e fim da história.

        Considera:
        - Dependências da história
        - Última história do desenvolvedor alocado

        Args:
            story: História a recalcular
            all_stories: Lista de todas as histórias
            config: Configuração do sistema
        """
        # Usar ScheduleCalculator para recalcular apenas esta história
        # (mantém lógica existente de cálculo)
        calculated = self._calculator.calculate([story], config)

        if calculated:
            story.start_date = calculated[0].start_date
            story.end_date = calculated[0].end_date
            story.duration = calculated[0].duration
```

**Estimativa:** 5 SP

---

### FASE 5: Criar Dialog de Relatório (2 SP) 📊

**Objetivo:** Mostrar warnings de ociosidade ao usuário.

#### 5.1 Criar AllocationReportDialog

**Arquivo:** `presentation/utils/allocation_report_dialog.py`

```python
"""Dialog para mostrar relatório de alocação."""
from typing import List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QWidget
)
from PySide6.QtCore import Qt
from backlog_manager.domain.services.idleness_detector import IdlenessWarning


class AllocationReportDialog(QDialog):
    """
    Dialog para exibir relatório de alocação de desenvolvedores.

    Mostra warnings de ociosidade detectados.
    """

    def __init__(self, parent: QWidget, allocated_count: int, warnings: List[IdlenessWarning]):
        super().__init__(parent)
        self.setWindowTitle("Relatório de Alocação")
        self.setModal(True)
        self.setMinimumSize(600, 400)

        self._warnings = warnings
        self._allocated_count = allocated_count

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura interface."""
        layout = QVBoxLayout(self)

        # Título
        title = QLabel(f"✓ {self._allocated_count} história(s) alocada(s) com sucesso!")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: green;")
        layout.addWidget(title)

        # Warnings (se houver)
        if self._warnings:
            warning_label = QLabel(
                f"⚠️ {len(self._warnings)} aviso(s) de ociosidade detectado(s):"
            )
            warning_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: orange;")
            layout.addWidget(warning_label)

            # Text edit com warnings
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)

            warning_text = "\n\n".join([
                f"• {warning}" for warning in self._warnings
            ])
            text_edit.setPlainText(warning_text)

            layout.addWidget(text_edit)
        else:
            success_label = QLabel("✓ Nenhum gap de ociosidade detectado!")
            success_label.setStyleSheet("font-size: 11pt; color: green;")
            layout.addWidget(success_label)

        # Botão OK
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignRight)
```

**Estimativa:** 2 SP

---

### FASE 6: Adicionar Botão na Toolbar (1 SP) 🔘

**Objetivo:** Adicionar botão "Alocar Desenvolvedores" na toolbar.

#### 6.1 Modificar MainWindow

**Arquivo:** `presentation/views/main_window.py`

```python
def _create_toolbar(self) -> QToolBar:
    """Cria barra de ferramentas."""
    toolbar = QToolBar("Toolbar Principal")
    toolbar.setMovable(False)
    toolbar.setIconSize(QSize(24, 24))

    # ... botões existentes ...

    # Separador antes de cronograma
    toolbar.addSeparator()

    # Calcular Cronograma (já existe)
    self._calculate_schedule_action = QAction(...)
    toolbar.addAction(self._calculate_schedule_action)

    # **NOVO: Alocar Desenvolvedores**
    self._allocate_developers_action = QAction(
        QIcon.fromTheme("system-users"),
        "Alocar Desenvolvedores",
        self
    )
    self._allocate_developers_action.setShortcut("Shift+F5")
    self._allocate_developers_action.setStatusTip(
        "Distribuir desenvolvedores automaticamente (Shift+F5)"
    )
    self._allocate_developers_action.triggered.connect(
        lambda: self.allocate_developers_requested.emit()
    )
    toolbar.addAction(self._allocate_developers_action)

    return toolbar
```

**Estimativa:** 1 SP

---

### FASE 7: Atualizar ScheduleController (2 SP) 🎮

**Objetivo:** Atualizar controller para mostrar relatório.

#### 7.1 Modificar ScheduleController

**Arquivo:** `presentation/controllers/schedule_controller.py`

```python
def allocate_developers(self) -> None:
    """Aloca desenvolvedores e mostra relatório."""
    try:
        if self._show_loading_callback:
            self._show_loading_callback()

        # Executar alocação
        allocated_count, warnings = self._allocate_use_case.execute()

        if self._hide_loading_callback:
            self._hide_loading_callback()

        # Mostrar relatório
        from backlog_manager.presentation.utils.allocation_report_dialog import (
            AllocationReportDialog
        )

        dialog = AllocationReportDialog(
            self._parent_widget,
            allocated_count,
            warnings
        )
        dialog.exec()

        # Atualizar view
        self._refresh_view()

    except Exception as e:
        if self._hide_loading_callback:
            self._hide_loading_callback()
        MessageBox.error(
            self._parent_widget,
            "Erro ao Alocar Desenvolvedores",
            str(e)
        )
```

**Estimativa:** 2 SP

---

### FASE 8: Atualizar DI Container (1 SP) 🔧

**Objetivo:** Injetar novos serviços nos use cases.

#### 8.1 Modificar DIContainer

**Arquivo:** `presentation/di_container.py`

```python
def _create_domain_services(self) -> None:
    """Cria serviços de domínio."""
    self.cycle_detector = CycleDetector()
    self.backlog_sorter = BacklogSorter()
    self.schedule_calculator = ScheduleCalculator()
    self.allocation_validator = AllocationValidator()
    self.developer_load_balancer = DeveloperLoadBalancer()  # NOVO
    self.idleness_detector = IdlenessDetector()  # NOVO

def _create_use_cases(self) -> None:
    """Cria use cases."""
    # ...

    # Allocate Developers - REVISADO
    self.allocate_developers_use_case = AllocateDevelopersUseCase(
        self.story_repository,
        self.developer_repository,
        self.configuration_repository,  # NOVO
        self.developer_load_balancer,  # NOVO
        self.idleness_detector,  # NOVO
        self.schedule_calculator  # NOVO
    )
```

**Estimativa:** 1 SP

---

## ✅ CRITÉRIOS DE ACEITAÇÃO GLOBAIS

### Funcionais

#### Calcular Cronograma
- [ ] Remove todos os desenvolvedores antes de calcular
- [ ] Ordena corretamente por dependências
- [ ] Ordena corretamente por prioridade
- [ ] Calcula datas considerando velocidade do time
- [ ] Histórias ficam sem desenvolvedor após calcular

#### Alocar Desenvolvedores
- [ ] Seleciona desenvolvedor com menos histórias
- [ ] Recalcula datas após cada alocação
- [ ] Detecta gaps de 1+ dias
- [ ] Mostra relatório com warnings ao usuário
- [ ] Relatório é claro e informativo

#### Interface
- [ ] Botão "Alocar Desenvolvedores" aparece na toolbar
- [ ] Botão está ao lado direito de "Calcular Cronograma"
- [ ] Atalho Shift+F5 funciona
- [ ] Tooltip é exibido corretamente

### Técnicos
- [ ] Novos serviços testados (cobertura ≥ 90%)
- [ ] Código segue Clean Architecture
- [ ] Sem acoplamento entre camadas
- [ ] Performance aceitável (< 5s para 100 histórias)

### UX
- [ ] Feedback claro durante operações longas (loading)
- [ ] Relatório de alocação é fácil de entender
- [ ] Warnings destacam desenvolvedores e histórias
- [ ] Usuário entende onde há ociosidade

---

## 🧪 CASOS DE TESTE

### CT-001: Calcular Cronograma Limpa Desenvolvedores

**Pré-condições:**
- 3 histórias cadastradas (H1, H2, H3)
- Todas com desenvolvedores alocados (D1, D2, D1)

**Passos:**
1. Clicar em "Calcular Cronograma"
2. Aguardar conclusão

**Resultado Esperado:**
- ✅ Todas as histórias têm `developer_id = None`
- ✅ Histórias ordenadas corretamente
- ✅ Datas calculadas

---

### CT-002: Alocar com Balanceamento de Carga

**Pré-condições:**
- 2 desenvolvedores (D1, D2)
- 5 histórias sem desenvolvedor (H1-H5)
- H1 e H2 já têm D1 (antes de limpar)

**Passos:**
1. Calcular Cronograma (limpa devs)
2. Alocar Desenvolvedores

**Resultado Esperado:**
- ✅ D1 e D2 recebem ~2-3 histórias cada
- ✅ Distribuição balanceada (diferença ≤ 1)

---

### CT-003: Detectar Ociosidade

**Pré-condições:**
- Desenvolvedor D1
- H1: 01/01 - 05/01, D1, depende de nada
- H2: 10/01 - 15/01, D1, depende de H3
- H3: 06/01 - 08/01, D2

**Passos:**
1. Alocar Desenvolvedores
2. Verificar relatório

**Resultado Esperado:**
- ✅ Warning: "D1: 1 dia(s) ocioso(s) entre H1 e H2"
- ✅ Gap causado por dependência de H3

---

### CT-004: Botão na Toolbar

**Passos:**
1. Abrir aplicação
2. Verificar toolbar

**Resultado Esperado:**
- ✅ Botão "Alocar Desenvolvedores" visível
- ✅ Está à direita de "Calcular Cronograma"
- ✅ Ícone de "system-users"
- ✅ Tooltip correto

---

### CT-005: Fluxo Completo

**Pré-condições:**
- Sistema limpo

**Passos:**
1. Importar 10 histórias do Excel
2. Cadastrar 3 desenvolvedores
3. Calcular Cronograma
4. Verificar que nenhuma história tem desenvolvedor
5. Alocar Desenvolvedores
6. Verificar relatório

**Resultado Esperado:**
- ✅ Histórias distribuídas em ~3-4 cada
- ✅ Relatório mostra alocações
- ✅ Se houver gaps, warnings são exibidos
- ✅ Cronograma completo e válido

---

## 📊 RESUMO DE ESTIMATIVAS

| Fase | Descrição | Story Points |
|------|-----------|--------------|
| 1 | Limpeza no Calcular Cronograma | 2 SP |
| 2 | Serviço de Balanceamento | 3 SP |
| 3 | Detector de Ociosidade | 3 SP |
| 4 | Reimplementar AllocateDevelopers | 5 SP |
| 5 | Dialog de Relatório | 2 SP |
| 6 | Botão na Toolbar | 1 SP |
| 7 | Atualizar Controller | 2 SP |
| 8 | Atualizar DI Container | 1 SP |
| **TOTAL** | | **19 SP** |

**Duração Estimada:** 2-3 semanas
**Complexidade:** Média-Alta

---

## 🎯 ORDEM DE IMPLEMENTAÇÃO RECOMENDADA

### Sprint 1 (10 SP)
1. ✅ FASE 1: Limpeza no Calcular Cronograma
2. ✅ FASE 2: Serviço de Balanceamento
3. ✅ FASE 3: Detector de Ociosidade
4. ✅ FASE 6: Botão na Toolbar

### Sprint 2 (9 SP)
5. ✅ FASE 4: Reimplementar AllocateDevelopers
6. ✅ FASE 5: Dialog de Relatório
7. ✅ FASE 7: Atualizar Controller
8. ✅ FASE 8: Atualizar DI Container
9. ✅ Testes E2E completos

---

## 📝 NOTAS DE IMPLEMENTAÇÃO

### Dependências Externas
- Nenhuma biblioteca externa necessária
- Usa apenas PySide6 (já presente)

### Considerações de Performance
- Alocação O(n*m) onde n = histórias, m = desenvolvedores
- Aceitável para < 1000 histórias e < 50 desenvolvedores
- Detecção de ociosidade O(n log n) por desenvolvedor

### Tratamento de Edge Cases
1. **Sem histórias:** Calcular e Alocar retornam imediatamente
2. **Sem desenvolvedores:** AllocateDevelopers lança exceção clara
3. **Todas alocadas:** AllocateDevelopers retorna 0, sem warnings
4. **Gaps de fim de semana:** Não contam como ociosidade

### Melhorias Futuras
- [ ] Permitir usuário escolher estratégia de alocação (manual, round-robin, balanceada)
- [ ] Visualização gráfica de timeline com gaps destacados
- [ ] Sugerir reordenação para minimizar ociosidade
- [ ] Exportar relatório de alocação para PDF

---

## ✅ CONCLUSÃO

Este plano revisa comportamentos críticos de **Calcular Cronograma** e **Alocar Desenvolvedores**:

**Benefícios:**
- ✅ Cronograma começa limpo (sem alocações antigas)
- ✅ Alocação inteligente balanceia carga
- ✅ Detecção de ociosidade previne desperdício
- ✅ Feedback claro ao usuário via relatório
- ✅ UX melhorada com botão na toolbar

**Pronto para implementação!** 🚀
