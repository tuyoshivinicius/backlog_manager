# Backlog Manager - Contexto Técnico

## 1. Visão Geral do Projeto

**Backlog Manager** é um sistema desktop para planejamento inteligente de tarefas e gestão de backlog de desenvolvimento.

- **Propósito**: Gestão de backlog com alocação automática de desenvolvedores e cálculo de cronogramas
- **Domínio**: Planejamento de desenvolvimento de software
- **Público-alvo**: Times de desenvolvimento (contexto brasileiro)
- **Estado**: Aplicação funcional completa com todas as camadas implementadas
- **Idioma**: Interface em Português (Brasil)

### Funcionalidades Principais

1. **Gestão de User Stories**: CRUD completo, priorização, duplicação, IDs auto-gerados
2. **Gestão de Dependências**: Dependências entre histórias com detecção de ciclos
3. **Cálculo de Cronograma**: Datas calculadas automaticamente baseadas em story points e velocidade do time
4. **Alocação Automática de Desenvolvedores**: Algoritmo sofisticado de balanceamento de carga
5. **Integração Excel**: Import/export com mapeamento flexível de colunas
6. **Validações**: Conflitos de alocação, ciclos de dependência, períodos ociosos

## 2. Arquitetura

### 2.1 Clean Architecture

O projeto segue rigorosamente os princípios de **Clean Architecture** com separação clara de responsabilidades:

```
┌─────────────────────────────────────────────────────┐
│              Presentation Layer                      │
│  (PySide6 Views, Controllers, UI Utils)             │
│                                                      │
│  Arquivos: presentation/                            │
└──────────────────┬──────────────────────────────────┘
                   │ depende de
┌──────────────────▼──────────────────────────────────┐
│           Infrastructure Layer                       │
│  (SQLite, Excel, Repositories)                      │
│                                                      │
│  Arquivos: infrastructure/                          │
└──────────────────┬──────────────────────────────────┘
                   │ depende de
┌──────────────────▼──────────────────────────────────┐
│            Application Layer                         │
│  (Use Cases, DTOs, Interfaces)                      │
│                                                      │
│  Arquivos: application/                             │
└──────────────────┬──────────────────────────────────┘
                   │ depende de
┌──────────────────▼──────────────────────────────────┐
│              Domain Layer                            │
│  (Entities, Value Objects, Domain Services)         │
│  SEM DEPENDÊNCIAS EXTERNAS                          │
│                                                      │
│  Arquivos: domain/                                  │
└─────────────────────────────────────────────────────┘
```

**Regra fundamental**: A camada de domínio NUNCA importa de outras camadas. O fluxo de dependências é sempre de fora para dentro.

### 2.2 Padrões de Design Utilizados

- **Clean Architecture**: Separação em camadas com inversão de dependências
- **Domain-Driven Design (DDD)**: Entidades ricas, Value Objects, Domain Services
- **Repository Pattern**: Abstração de acesso a dados
- **Unit of Work Pattern**: Gerenciamento de transações
- **Dependency Injection**: DIContainer centralizado
- **DTO Pattern**: Transferência de dados entre camadas
- **MVC/MVP**: Controllers mediam entre Views e Use Cases

## 3. Estrutura de Diretórios

```
backlog_manager/
├── domain/
│   ├── entities/              # Story, Developer, Configuration
│   ├── value_objects/         # StoryPoint, StoryStatus
│   ├── services/              # BacklogSorter, ScheduleCalculator, etc.
│   ├── interfaces/            # Repository interfaces
│   └── exceptions/            # Domain exceptions
│
├── application/
│   ├── use_cases/
│   │   ├── story/            # CreateStory, UpdateStory, etc.
│   │   ├── developer/        # CRUD de desenvolvedores
│   │   ├── dependency/       # Gestão de dependências
│   │   ├── schedule/         # CalculateSchedule, AllocateDevelopers
│   │   ├── configuration/    # Configurações do sistema
│   │   └── excel/            # Import/Export
│   ├── dto/                  # StoryDTO, DeveloperDTO, etc.
│   └── interfaces/           # Interfaces de serviços (ExcelService)
│
├── infrastructure/
│   ├── database/
│   │   ├── repositories/     # Implementações SQLite
│   │   ├── migrations/       # Schema migrations
│   │   ├── schema.sql        # Schema do banco
│   │   ├── connection.py     # Singleton de conexão
│   │   └── unit_of_work.py   # Transações
│   └── excel/
│       └── openpyxl_excel_service.py
│
└── presentation/
    ├── views/                # Janelas e dialogs PySide6
    ├── controllers/          # MainController, StoryController, etc.
    └── utils/                # DIContainer, StatusBarManager, etc.
```

## 4. Camada de Domínio (Domain Layer)

### 4.1 Entidades

#### Story
Representa uma história de usuário (user story) no backlog.

**Atributos**:
- `id: str` - ID composto (ex: "CORE-001", "UI-042")
- `component: str` - Componente do sistema (ex: "CORE", "UI", "API")
- `name: str` - Nome descritivo da história
- `story_points: StoryPoint` - Pontos de complexidade (3, 5, 8, 13)
- `status: StoryStatus` - BACKLOG, EXECUÇÃO, TESTES, CONCLUÍDO, IMPEDIDO
- `priority: int` - Prioridade (1 = maior, valores crescentes = menor)
- `dependencies: list[str]` - IDs das histórias que são pré-requisitos
- `developer_id: int | None` - Desenvolvedor alocado (FK)
- `start_date: datetime.date | None` - Data de início calculada
- `end_date: datetime.date | None` - Data de conclusão calculada
- `duration_in_days: int | None` - Duração em dias úteis

**Arquivo**: `backlog_manager/domain/entities/story.py`

#### Developer
Representa um desenvolvedor que pode ser alocado a histórias.

**Atributos**:
- `id: int` - ID auto-incrementado
- `name: str` - Nome do desenvolvedor

**Arquivo**: `backlog_manager/domain/entities/developer.py`

#### Configuration
Configuração global do sistema (singleton).

**Atributos**:
- `id: int` - Sempre 1 (singleton)
- `story_points_per_sprint: int` - Velocidade do time em pontos por sprint
- `workdays_per_sprint: int` - Dias úteis por sprint
- `roadmap_start_date: datetime.date` - Data de início do roadmap

**Propriedade calculada**:
- `velocity_per_day: float` - story_points_per_sprint / workdays_per_sprint

**Arquivo**: `backlog_manager/domain/entities/configuration.py`

### 4.2 Value Objects

#### StoryPoint
Escala Fibonacci de complexidade.

**Valores válidos**: 3 (P), 5 (M), 8 (G), 13 (GG)

**Arquivo**: `backlog_manager/domain/value_objects/story_point.py`

#### StoryStatus
Estados do ciclo de vida de uma história.

**Valores**: BACKLOG, EXECUÇÃO, TESTES, CONCLUÍDO, IMPEDIDO

**Arquivo**: `backlog_manager/domain/value_objects/story_status.py`

### 4.3 Serviços de Domínio

#### BacklogSorter
Ordena histórias respeitando dependências e prioridades.

**Algoritmo**: Ordenação topológica usando Kahn's algorithm
**Complexidade**: O(V+E) onde V=histórias, E=dependências
**Regra**: Histórias sem dependências são ordenadas por prioridade (menor = primeiro)

**Arquivo**: `backlog_manager/domain/services/backlog_sorter.py`

#### ScheduleCalculator
Calcula datas de início/fim baseado em story points e velocidade.

**Funcionalidades**:
- Calcula apenas dias úteis (segunda a sexta)
- Considera feriados brasileiros nacionais (2025-2026)
- Ajusta datas de início para próximo dia útil
- Respeita dependências (história só inicia após dependências concluírem)

**Feriados incluídos**: Ano Novo, Carnaval, Sexta-feira Santa, Tiradentes, Dia do Trabalho, Corpus Christi, Independência, Nossa Senhora Aparecida, Finados, Proclamação da República, Consciência Negra, Natal

**Arquivo**: `backlog_manager/domain/services/schedule_calculator.py`

#### DeveloperLoadBalancer
Balanceia carga de trabalho entre desenvolvedores.

**Estratégia**:
1. Calcula carga atual de cada desenvolvedor (soma de story points)
2. Aloca nova história ao desenvolvedor com menor carga
3. Desempate aleatório quando cargas são iguais (para fairness)

**Complexidade**: O(n*d) onde n=histórias, d=desenvolvedores

**Arquivo**: `backlog_manager/domain/services/developer_load_balancer.py`

#### CycleDetector
Detecta dependências circulares usando busca em profundidade (DFS).

**Complexidade**: O(V+E)

**Arquivo**: `backlog_manager/domain/services/cycle_detector.py`

#### AllocationValidator
Valida se alocações de desenvolvedores causam conflitos (períodos sobrepostos).

**Arquivo**: `backlog_manager/domain/services/allocation_validator.py`

#### IdlenessDetector
Detecta períodos ociosos (gaps) nos cronogramas de desenvolvedores.

**Arquivo**: `backlog_manager/domain/services/idleness_detector.py`

### 4.4 Regras de Negócio Críticas

1. **Story Points**: Apenas valores Fibonacci (3, 5, 8, 13)
2. **Cronograma**: Apenas dias úteis (segunda-sexta), exclui feriados brasileiros
3. **Dependências**: Devem ser acíclicas (grafo direcionado acíclico - DAG)
4. **Alocação**: Um desenvolvedor por história, sem sobreposição de períodos
5. **Prioridade**: Menor número = maior prioridade
6. **IDs de Stories**: Formato "COMPONENTE-NÚMERO" (ex: "CORE-001")
7. **Configuration**: Singleton (apenas uma instância)

## 5. Camada de Aplicação (Application Layer)

### 5.1 Casos de Uso (Use Cases)

#### Gestão de Stories

**CreateStoryUseCase**
- Auto-gera ID baseado no componente (busca próximo número disponível)
- Define prioridade inicial como max(priority) + 1
- Valida story points
- **Arquivo**: `application/use_cases/story/create_story.py`

**UpdateStoryUseCase**
- Permite alterar todos os campos exceto ID
- Valida story points e dependências
- **Arquivo**: `application/use_cases/story/update_story.py`

**DuplicateStoryUseCase**
- Clona história existente com novo ID
- Mantém todos os atributos exceto ID e datas
- **Arquivo**: `application/use_cases/story/duplicate_story.py`

**DeleteStoryUseCase**, **GetStoryUseCase**, **ListStoriesUseCase**
- Operações CRUD padrão
- **Arquivos**: `application/use_cases/story/`

**ChangePriorityUseCase**
- Reordena prioridades do backlog
- **Arquivo**: `application/use_cases/story/change_priority.py`

#### Gestão de Desenvolvedores

**CreateDeveloperUseCase**, **UpdateDeveloperUseCase**, **DeleteDeveloperUseCase**, **GetDeveloperUseCase**, **ListDevelopersUseCase**
- CRUD completo de desenvolvedores
- **Arquivos**: `application/use_cases/developer/`

#### Gestão de Dependências

**AddDependencyUseCase**
- Adiciona dependência entre histórias
- Valida ciclos usando CycleDetector
- Lança `CyclicDependencyException` se criar ciclo
- **Arquivo**: `application/use_cases/dependency/add_dependency.py`

**RemoveDependencyUseCase**
- Remove dependência
- **Arquivo**: `application/use_cases/dependency/remove_dependency.py`

#### Agendamento (Scheduling)

**CalculateScheduleUseCase**
- Calcula cronograma completo do backlog
- **Fluxo**:
  1. Busca todas as histórias e configuração
  2. Ordena histórias (BacklogSorter)
  3. Calcula datas (ScheduleCalculator)
  4. Persiste datas calculadas
- Usa UnitOfWork para transação
- **Arquivo**: `application/use_cases/schedule/calculate_schedule.py`

**AllocateDevelopersUseCase**
- Algoritmo complexo de alocação automática (RF-ALOC-001)
- **Fluxo**:
  1. Ordena histórias por prioridade
  2. Para cada história não alocada:
     - Tenta alocar usando DeveloperLoadBalancer
     - Valida conflitos usando AllocationValidator
     - Se houver conflito, ajusta data de início e recalcula cronograma
  3. Detecta ociosidade e emite warnings
- Usa UnitOfWork para transação
- **Arquivo**: `application/use_cases/schedule/allocate_developers.py`

**ValidateDeveloperAllocationUseCase**
- Valida se alocação causaria conflito
- **Arquivo**: `application/use_cases/schedule/validate_developer_allocation.py`

#### Configuração

**GetConfigurationUseCase**, **UpdateConfigurationUseCase**
- Gerencia configuração global (singleton)
- **Arquivos**: `application/use_cases/configuration/`

#### Import/Export Excel

**ImportFromExcelUseCase**
- Importa histórias de arquivo Excel
- Mapeamento flexível de colunas (case-insensitive)
- Suporta modo update (atualiza histórias existentes)
- **Colunas esperadas**: ID, Component, Name, Story Points, Status, Priority, Dependencies, Developer
- **Arquivo**: `application/use_cases/excel/import_from_excel.py`

**ExportToExcelUseCase**
- Exporta backlog para Excel com formatação
- **Arquivo**: `application/use_cases/excel/export_to_excel.py`

### 5.2 DTOs (Data Transfer Objects)

**StoryDTO**, **DeveloperDTO**, **ConfigurationDTO**, **BacklogDTO**
- Transferem dados entre camadas
- Conversores em `application/dto/converters.py`

**Arquivos**: `application/dto/`

### 5.3 Interfaces

**Repositories**:
- `StoryRepository`
- `DeveloperRepository`
- `ConfigurationRepository`

**Services**:
- `ExcelService`

**Arquivos**: `application/interfaces/`

## 6. Camada de Infraestrutura (Infrastructure Layer)

### 6.1 Database (SQLite)

#### SQLiteConnection
Singleton para gerenciar conexão com banco SQLite.

**Arquivo**: `infrastructure/database/connection.py`

#### UnitOfWork
Implementa padrão Unit of Work para gerenciamento de transações.

**Uso**:
```python
with uow:
    uow.stories.add(story)
    uow.commit()
```

**Arquivo**: `infrastructure/database/unit_of_work.py`

#### Repositories
Implementações SQLite dos repositórios definidos no Application.

- **SQLiteStoryRepository**: `infrastructure/database/repositories/sqlite_story_repository.py`
- **SQLiteDeveloperRepository**: `infrastructure/database/repositories/sqlite_developer_repository.py`
- **SQLiteConfigurationRepository**: `infrastructure/database/repositories/sqlite_configuration_repository.py`

#### Schema

**Tabelas**:

**stories**:
```sql
CREATE TABLE stories (
    id TEXT PRIMARY KEY,
    component TEXT NOT NULL,
    name TEXT NOT NULL,
    story_points INTEGER NOT NULL,
    status TEXT NOT NULL,
    priority INTEGER NOT NULL,
    start_date TEXT,
    end_date TEXT,
    duration_in_days INTEGER,
    developer_id INTEGER,
    dependencies TEXT,  -- JSON array
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (developer_id) REFERENCES developers(id)
);
```

**developers**:
```sql
CREATE TABLE developers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
```

**configuration**:
```sql
CREATE TABLE configuration (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Singleton
    story_points_per_sprint INTEGER NOT NULL,
    workdays_per_sprint INTEGER NOT NULL,
    roadmap_start_date TEXT NOT NULL
);
```

**Indexes**:
- `idx_stories_priority` ON stories(priority)
- `idx_stories_status` ON stories(status)
- `idx_stories_developer` ON stories(developer_id)
- `idx_stories_component` ON stories(component)

**Triggers**:
- Auto-atualiza `updated_at` em stories

**Arquivo**: `infrastructure/database/schema.sql`

#### Migrations
Sistema de migrations para evolução do schema.

**Arquivo**: `infrastructure/database/migrations/`

### 6.2 Excel

#### OpenpyxlExcelService
Implementa `ExcelService` usando biblioteca openpyxl.

**Funcionalidades**:
- Import com mapeamento flexível de colunas (case-insensitive)
- Export com formatação (cabeçalhos em negrito, auto-size de colunas)
- Suporte para modo update

**Arquivo**: `infrastructure/excel/openpyxl_excel_service.py`

## 7. Camada de Apresentação (Presentation Layer)

### 7.1 Views (PySide6/Qt)

#### MainWindow
Janela principal da aplicação.

**Componentes**:
- Barra de menu (Arquivo, Editar, Ferramentas, Ajuda)
- Toolbar com ações rápidas
- Tabela principal (EditableTable) com histórias
- Status bar

**Arquivo**: `presentation/views/main_window.py`

#### Dialogs

**StoryForm**: Dialog para criar/editar história
**DeveloperForm**: Dialog para criar/editar desenvolvedor
**DeveloperManagerDialog**: Gestão completa de desenvolvedores
**ConfigurationDialog**: Configurações do sistema
**DependenciesDialog**: Gerenciar dependências de histórias

**Arquivos**: `presentation/views/`

#### Widgets Customizados

**EditableTable**: Tabela editável com delegates customizados
**Delegates**: StatusDelegate, StoryPointDelegate, DependenciesDelegate, DeveloperDelegate

**Arquivos**: `presentation/views/widgets/`

### 7.2 Controllers

**MainController**: Orquestrador principal da aplicação
**StoryController**: Operações de histórias
**DeveloperController**: Operações de desenvolvedores
**ScheduleController**: Cálculos de cronograma

**Arquivos**: `presentation/controllers/`

### 7.3 Utils

**DIContainer**: Container de injeção de dependências (gerencia instâncias de Use Cases)
**StatusBarManager**: Gerencia mensagens na status bar
**ProgressDialog**: Dialog de progresso para operações longas
**MessageBox**: Dialogs de mensagens padronizados
**AllocationWorker**: QThread para executar alocação em background
**CellHighlighter**: Feedback visual para células da tabela

**Arquivos**: `presentation/utils/`

## 8. Stack Tecnológico

### Core
- **Python 3.11+**: Type hints em todo o código
- **PySide6 6.6.1**: Framework Qt para interface gráfica
- **SQLite**: Banco de dados embarcado
- **openpyxl 3.1.2**: Manipulação de arquivos Excel

### Testing
- **pytest 7.4.3**: Framework de testes
- **pytest-cov 4.1.0**: Cobertura de código
- **Meta**: 90%+ de cobertura
- **16 arquivos de teste** (unit + integration)

### Qualidade de Código
- **black 23.12.0**: Formatação automática (100 chars por linha)
- **isort 5.13.2**: Organização de imports
- **flake8 6.1.0**: Linting
- **mypy 1.7.1**: Type checking (strict mode)
- **pylint 3.0.3**: Linting adicional
- **radon 6.0.1**: Análise de complexidade

### Development
- **ipython 8.18.1**: Shell interativo
- **PyInstaller 6.3.0**: Empacotamento para distribuição

## 9. Estratégia de Testes

### Organização
```
tests/
├── unit/                    # Testes rápidos e isolados
│   ├── domain/             # Entities, Value Objects, Services
│   │   ├── test_story.py
│   │   ├── test_backlog_sorter.py
│   │   ├── test_schedule_calculator.py
│   │   ├── test_developer_load_balancer.py
│   │   └── ...
│   └── application/        # Use Cases (com mocks)
│
└── integration/            # Testes de integração
    └── infrastructure/
        ├── database/       # Repositories, UnitOfWork
        └── excel/          # ExcelService
```

### Configuração
- **Source**: `backlog_manager/`
- **Exclude**: tests, venv, `__init__.py`
- **Target**: 90%+ coverage
- **Reports**: Terminal + HTML (htmlcov/)

### Markers
- `unit`: Testes unitários rápidos
- `integration`: Testes de integração
- `slow`: Testes que demoram > 1 segundo

### Comandos
```bash
# Todos os testes com cobertura
pytest

# Apenas unit tests
pytest tests/unit -v

# Relatório HTML
pytest --cov-report=html
```

## 10. Algoritmos e Complexidade

### BacklogSorter
**Algoritmo**: Kahn's algorithm para ordenação topológica
**Complexidade**: O(V+E) onde V=histórias, E=dependências
**Comportamento**: Histórias sem dependências não satisfeitas são ordenadas por prioridade

### CycleDetector
**Algoritmo**: DFS (Depth-First Search) com marcação de estados
**Complexidade**: O(V+E)
**Detecta**: Dependências circulares (back edges)

### ScheduleCalculator
**Complexidade**: O(n) onde n=número de histórias
**Considera**: Dias úteis, feriados brasileiros, dependências

### DeveloperLoadBalancer
**Complexidade**: O(n*d) onde n=histórias, d=desenvolvedores
**Estratégia**: Greedy com desempate aleatório

## 11. Schema do Banco de Dados

### stories
**Colunas**:
- `id` (PK): TEXT - ID composto como "CORE-001"
- `component`: TEXT - Componente do sistema
- `name`: TEXT - Nome da história
- `story_points`: INTEGER - 3, 5, 8, ou 13
- `status`: TEXT - BACKLOG, EXECUÇÃO, TESTES, CONCLUÍDO, IMPEDIDO
- `priority`: INTEGER - Menor = maior prioridade
- `start_date`: TEXT (ISO format) - Data de início
- `end_date`: TEXT (ISO format) - Data de conclusão
- `duration_in_days`: INTEGER - Duração em dias úteis
- `developer_id`: INTEGER (FK) - Desenvolvedor alocado
- `dependencies`: TEXT (JSON array) - Lista de IDs de dependências
- `created_at`: TEXT - Auto-gerenciado
- `updated_at`: TEXT - Auto-gerenciado por trigger

**Indexes**: priority, status, developer_id, component

### developers
**Colunas**:
- `id` (PK): INTEGER AUTO_INCREMENT
- `name`: TEXT - Nome do desenvolvedor

### configuration
**Colunas**:
- `id` (PK): INTEGER - Sempre 1 (singleton enforced por CHECK)
- `story_points_per_sprint`: INTEGER - Velocidade do time
- `workdays_per_sprint`: INTEGER - Dias úteis por sprint
- `roadmap_start_date`: TEXT (ISO format) - Início do roadmap

## 12. Localização (i18n/l10n)

### Idioma
- **UI**: Português (Brasil)
- **Documentação**: Português
- **Código**: Inglês (nomes de classes, métodos, variáveis)

### Feriados Brasileiros
Lista completa de feriados nacionais (2025-2026) em `ScheduleCalculator`:
- Ano Novo (01/01)
- Carnaval (data móvel)
- Sexta-feira Santa (data móvel)
- Tiradentes (21/04)
- Dia do Trabalho (01/05)
- Corpus Christi (data móvel)
- Independência (07/09)
- Nossa Senhora Aparecida (12/10)
- Finados (02/11)
- Proclamação da República (15/11)
- Consciência Negra (20/11)
- Natal (25/12)

### Formatos
- **Data**: ISO format (YYYY-MM-DD) internamente, formatação brasileira na UI

## 13. Pontos de Atenção para Desenvolvimento

### Regras Arquiteturais
1. **Domain nunca importa de outras camadas**: Mantém o núcleo puro
2. **Use Cases coordenam**: Não colocam lógica de negócio, apenas orquestram
3. **Repositories retornam entidades**: Não DTOs
4. **Controllers não acessam repositórios diretamente**: Sempre via Use Cases

### Padrões de Código
1. **Type hints obrigatórios**: mypy em strict mode
2. **Docstrings em classes e métodos públicos**: Descrever propósito e comportamento
3. **Testes para novos Use Cases**: Unit + integration
4. **Formatação com black**: 100 caracteres por linha
5. **Imports organizados com isort**: Ordem: stdlib, third-party, local

### Transações
- **Use UnitOfWork** para operações que modificam múltiplas entidades
- **Exemplo**: CalculateScheduleUseCase usa UnitOfWork para garantir atomicidade

### Validações
- **Domain entities validam no construtor**: Falham rápido com exceções específicas
- **Use Cases validam regras de orquestração**: Ex: AddDependencyUseCase valida ciclos

### IDs
- **Stories**: IDs compostos (componente + número), gerados em CreateStoryUseCase
- **Developers**: IDs numéricos auto-increment

### Datas
- **Sempre use ScheduleCalculator** para cálculos de cronograma
- **Não calcule datas manualmente**: ScheduleCalculator considera feriados e fins de semana

### Dependências
- **Sempre valide com CycleDetector** antes de adicionar dependência
- **AddDependencyUseCase já faz isso**: Não bypasse o Use Case

## 14. Arquivos Críticos

### Domain
- `domain/entities/story.py` - Entidade Story
- `domain/services/backlog_sorter.py` - Ordenação topológica
- `domain/services/schedule_calculator.py` - Cálculo de cronograma
- `domain/services/developer_load_balancer.py` - Balanceamento de carga

### Application
- `application/use_cases/schedule/calculate_schedule.py` - Cálculo completo de cronograma
- `application/use_cases/schedule/allocate_developers.py` - Alocação automática
- `application/use_cases/excel/import_from_excel.py` - Import de Excel

### Infrastructure
- `infrastructure/database/schema.sql` - Schema do banco
- `infrastructure/database/repositories/sqlite_story_repository.py` - Repository principal
- `infrastructure/database/unit_of_work.py` - Gerenciamento de transações

### Presentation
- `presentation/views/main_window.py` - Janela principal
- `presentation/controllers/main_controller.py` - Orquestrador da aplicação
- `presentation/utils/di_container.py` - Container de injeção de dependências

## 15. Fluxos Importantes

### Fluxo de Cálculo de Cronograma
1. Usuário clica em "Calcular Cronograma"
2. `MainController` chama `ScheduleController.calculate_schedule()`
3. `ScheduleController` executa `CalculateScheduleUseCase`
4. `CalculateScheduleUseCase`:
   - Busca todas as stories e configuration
   - Ordena stories com `BacklogSorter`
   - Calcula datas com `ScheduleCalculator`
   - Persiste via `UnitOfWork`
5. UI é atualizada

### Fluxo de Alocação Automática
1. Usuário clica em "Alocar Desenvolvedores"
2. `MainController` inicia `AllocationWorker` (thread em background)
3. `AllocationWorker` executa `AllocateDevelopersUseCase`
4. `AllocateDevelopersUseCase`:
   - Ordena stories por prioridade
   - Para cada story não alocada:
     - Tenta alocar com `DeveloperLoadBalancer`
     - Valida com `AllocationValidator`
     - Se conflito, ajusta data de início
     - Recalcula cronograma
   - Detecta ociosidade com `IdlenessDetector`
   - Persiste via `UnitOfWork`
5. UI mostra progresso e resultado

### Fluxo de Import Excel
1. Usuário seleciona arquivo Excel
2. `MainController` chama `ExcelController.import_from_excel()`
3. `ExcelController` executa `ImportFromExcelUseCase`
4. `ImportFromExcelUseCase`:
   - Lê arquivo com `ExcelService`
   - Mapeia colunas (case-insensitive)
   - Para cada linha:
     - Verifica se story existe (modo update) ou cria nova
     - Valida dados
     - Persiste via repository
5. UI mostra resumo da importação

## 16. Decisões de Design

### Por que Clean Architecture?
- **Testabilidade**: Domain isolado, fácil de testar
- **Flexibilidade**: Trocar UI ou database sem afetar lógica de negócio
- **Manutenibilidade**: Separação clara de responsabilidades

### Por que SQLite?
- **Simplicidade**: Sem necessidade de servidor
- **Portabilidade**: Arquivo único
- **Suficiente**: Para escala esperada (centenas de stories)

### Por que PySide6?
- **Nativo**: Performance melhor que web-based
- **Maturidade**: Qt é estável e bem documentado
- **Offline**: Não requer servidor

### Por que Fibonacci para Story Points?
- **Padrão da indústria**: Planning poker usa Fibonacci
- **Incerteza crescente**: Diferenças maiores para valores maiores refletem incerteza

### Por que ordenação topológica + prioridade?
- **Dependências first**: Garante que pré-requisitos vêm antes
- **Prioridade como desempate**: Para histórias sem dependências, usa prioridade

## 17. Estado Atual do Projeto

### Implementado
- ✅ Todas as camadas (Domain, Application, Infrastructure, Presentation)
- ✅ CRUD completo de Stories e Developers
- ✅ Gestão de dependências com detecção de ciclos
- ✅ Cálculo de cronograma com dias úteis e feriados brasileiros
- ✅ Alocação automática de desenvolvedores com balanceamento
- ✅ Import/Export Excel
- ✅ Interface gráfica completa em PySide6
- ✅ Testes unitários e de integração
- ✅ Banco de dados SQLite com migrations

### Em Desenvolvimento
- 🚧 Melhorias na UI (drag-and-drop, visualizações)
- 🚧 Relatórios e dashboards
- 🚧 Integração com ferramentas externas (Jira, etc.)

### Backlog
- 📋 Suporte a múltiplos times
- 📋 Histórico de mudanças (audit log)
- 📋 Notificações e alertas
- 📋 API REST para integrações

## 18. Como Executar

### Setup
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements-dev.txt
```

### Executar aplicação
```bash
python -m backlog_manager.main
```

### Testes
```bash
# Todos os testes
pytest

# Apenas unit
pytest tests/unit -v

# Com coverage HTML
pytest --cov-report=html
```

### Qualidade de código
```bash
# Formatação
black backlog_manager/

# Imports
isort backlog_manager/

# Linting
flake8 backlog_manager/

# Type checking
mypy backlog_manager/
```

## 19. Referências

- **Clean Architecture**: Robert C. Martin ("Uncle Bob")
- **Domain-Driven Design**: Eric Evans
- **Repository Pattern**: Martin Fowler
- **Unit of Work**: Martin Fowler
- **PySide6 Documentation**: https://doc.qt.io/qtforpython/
- **pytest Documentation**: https://docs.pytest.org/

---

**Última atualização**: 2024-12-24
**Versão**: 1.0
**Contato**: [Informações do projeto]
