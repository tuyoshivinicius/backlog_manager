## SUMÁRIO EXECUTIVO

Este documento apresenta um plano de implementação estruturado em 6 fases para o desenvolvimento de um sistema desktop de gestão de backlog. O projeto segue rigorosamente os princípios de Clean Architecture e será desenvolvido em Python com interface desktop (PyQt6/PySide6).

**Objetivos Principais:**
- Criar sistema desktop standalone para Windows
- Implementar ordenação inteligente de backlog com gerenciamento de dependências
- Calcular cronogramas automaticamente com alocação de desenvolvedores
- Fornecer interface intuitiva tipo Excel para gestão de tarefas
- Garantir alta qualidade de código

**Tecnologias Core:**
- **Linguagem:** Python 3.11+
- **Interface:** PyQt6 ou PySide6
- **Banco de Dados:** SQLite
- **Empacotamento:** PyInstaller
- **Testes:** pytest, pytest-cov
- **Exportação:** openpyxl (Excel)

---

## ANÁLISE DOS REQUISITOS

### 1. Complexidade do Domínio

#### Entidades Principais
1. **História (Story)**
   - Atributos complexos (11 campos)
   - Relacionamento N:N com si mesma (dependências)
   - Validações específicas (Story Points: 3, 5, 8, 13)
   - Estados de ciclo de vida (Status: BACKLOG → EXECUÇÃO → TESTES → CONCLUÍDO)

2. **Desenvolvedor (Developer)**
   - Entidade simples (2 campos)
   - Geração automática de ID baseada em regras
   - Relacionamento 1:N com História

3. **Configuração (Configuration)**
   - Singleton de configuração global
   - Cálculos derivados (Velocidade por Dia)

#### Regras de Negócio Críticas

**RN-001: Detecção de Ciclos em Dependências**
- Complexidade: Alta
- Algoritmo necessário: DFS (Depth-First Search) para detecção de ciclos em grafo direcionado
- Impacto: Crítico para integridade do sistema
- Estimativa: 8 SP

**RN-002: Ordenação de Backlog**
- Complexidade: Alta
- Algoritmo: Topological Sort (ordenação topológica) + ordenação secundária por prioridade
- Restrições: Histórias sem dependências primeiro, depois respeitar prioridade
- Estimativa: 8 SP

**RN-003: Alocação Automática Round-Robin**
- Complexidade: Média
- Lógica: Distribuir histórias igualmente entre desenvolvedores disponíveis
- Considerar: Ordem do backlog, disponibilidade de desenvolvedores
- Estimativa: 5 SP

**RN-004: Cálculo de Cronograma**
- Complexidade: Alta
- Fórmula: `Duração = ceil(Story Point / Velocidade por Dia)`
- Considerar: Apenas dias úteis (segunda a sexta)
- Dependências em cascata: Início da história B = Fim da história A + 1 dia
- Estimativa: 8 SP

**RN-005: Recálculo Reativo**
- Complexidade: Média
- Gatilhos: Mudança em SP, Prioridade, Desenvolvedor
- Impacto: Todo cronograma deve ser recalculado
- Requisito de performance: < 2s para 100 histórias
- Estimativa: 5 SP

### 2. Requisitos de Interface

**Complexidade: Média-Alta**

- Tabela editável inline (tipo Excel)
- Menu contextual e barra de ferramentas
- Formulários de CRUD
- Visualização Timeline/Roadmap (tipo Gantt)
- Atalhos de teclado
- Feedback visual em tempo real

### 3. Requisitos Não-Funcionais Críticos

**Performance:**
- Cálculo cronograma: < 2s para 100 histórias
- Operações CRUD: < 500ms
- Edição inline: < 100ms

**Arquitetura:**
- Clean Architecture estrita
- Testes integrados narrow (foco em integração de componentes)
- Código em inglês, docstrings em português

**Distribuição:**
- Executável standalone (PyInstaller)
- Sem dependências externas
- Compatível com Windows 10+

### 4. Pontos de Atenção

1. **Gestão de Complexidade Algorítmica**
   - Detecção de ciclos e ordenação topológica são algoritmos não-triviais
   - Necessidade de testes extensivos para casos extremos
   - Otimização para performance

2. **Sincronização de Estado**
   - Interface deve refletir estado do domínio em tempo real
   - Recálculo automático pode impactar UX se não otimizado
   - Necessário pattern Observer ou Event-Driven

3. **Edição Inline na Tabela**
   - Complexo de implementar com validações
   - Necessário boa experiência do usuário (tipo Excel)
   - Sincronização com banco de dados

4. **Empacotamento PyInstaller**
   - Histórico de issues com PyQt/PySide
   - Necessário testes extensivos do executável
   - Tamanho do executável pode ser grande

---

## ARQUITETURA PROPOSTA

### Estrutura de Camadas (Clean Architecture)

```
backlog_manager/
├── domain/                          # Camada de Domínio (Núcleo)
│   ├── entities/
│   │   ├── story.py                # Entidade História
│   │   ├── developer.py            # Entidade Desenvolvedor
│   │   └── configuration.py        # Entidade Configuração
│   ├── value_objects/
│   │   ├── story_point.py          # Value Object para Story Points
│   │   ├── story_status.py         # Enum Status
│   │   └── story_id.py             # Value Object para ID
│   ├── services/
│   │   ├── cycle_detector.py       # Serviço de detecção de ciclos
│   │   ├── backlog_sorter.py       # Serviço de ordenação
│   │   └── schedule_calculator.py  # Serviço de cálculo de cronograma
│   └── exceptions/
│       └── domain_exceptions.py    # Exceções de domínio
│
├── application/                     # Camada de Aplicação (Casos de Uso)
│   ├── use_cases/
│   │   ├── story/
│   │   │   ├── create_story.py
│   │   │   ├── update_story.py
│   │   │   ├── delete_story.py
│   │   │   ├── list_stories.py
│   │   │   └── duplicate_story.py
│   │   ├── developer/
│   │   │   ├── create_developer.py
│   │   │   ├── update_developer.py
│   │   │   └── delete_developer.py
│   │   ├── dependency/
│   │   │   ├── add_dependency.py
│   │   │   └── remove_dependency.py
│   │   ├── schedule/
│   │   │   ├── calculate_schedule.py
│   │   │   └── allocate_developers.py
│   │   ├── import_export/
│   │   │   ├── import_from_excel.py
│   │   │   └── export_to_excel.py
│   │   └── configuration/
│   │       └── update_configuration.py
│   ├── interfaces/                  # Interfaces (Ports)
│   │   ├── repositories/
│   │   │   ├── story_repository.py
│   │   │   ├── developer_repository.py
│   │   │   └── configuration_repository.py
│   │   └── services/
│   │       └── excel_service.py
│   └── dto/
│       └── story_dto.py            # Data Transfer Objects
│
├── infrastructure/                  # Camada de Infraestrutura
│   ├── database/
│   │   ├── sqlite_connection.py    # Conexão SQLite
│   │   ├── repositories/
│   │   │   ├── story_repository_impl.py
│   │   │   ├── developer_repository_impl.py
│   │   │   └── configuration_repository_impl.py
│   │   └── migrations/
│   │       └── create_tables.sql
│   ├── excel/
│   │   └── excel_service_impl.py   # Implementação com openpyxl
│   └── persistence/
│       └── unit_of_work.py         # Padrão Unit of Work
│
├── presentation/                    # Camada de Apresentação (UI)
│   ├── views/
│   │   ├── main_window.py          # Janela principal
│   │   ├── story_form.py           # Formulário de história
│   │   ├── developer_form.py       # Formulário de desenvolvedor
│   │   ├── configuration_dialog.py # Diálogo de configurações
│   │   ├── timeline_view.py        # Visualização Timeline
│   │   └── widgets/
│   │       ├── editable_table.py   # Tabela editável customizada
│   │       └── toolbar.py          # Barra de ferramentas
│   ├── controllers/
│   │   ├── main_controller.py      # Controlador principal
│   │   ├── story_controller.py     # Controlador de histórias
│   │   └── developer_controller.py # Controlador de desenvolvedores
│   ├── view_models/
│   │   ├── story_view_model.py     # ViewModel para histórias
│   │   └── timeline_view_model.py  # ViewModel para timeline
│   └── styles/
│       └── app_styles.qss          # Estilos Qt
│
├── tests/                           # Testes
│   ├── unit/                        # Testes unitários
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/                 # Testes de integração narrow
│   │   ├── test_story_workflows.py
│   │   ├── test_schedule_calculation.py
│   │   └── test_database_integration.py
│   └── fixtures/
│       └── sample_data.py
│
├── config/                          # Configurações
│   └── settings.py
│
├── main.py                          # Ponto de entrada
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

### Princípios Arquiteturais

**1. Dependency Rule (Regra de Dependência)**
```
Presentation → Application → Domain
Infrastructure → Application → Domain

Domain: Não depende de nada
Application: Depende apenas de Domain
Infrastructure: Depende de Application e Domain
Presentation: Depende de Application
```

**2. Interfaces e Inversão de Dependência**
```python
# Application define a interface (Port)
class StoryRepository(ABC):
    @abstractmethod
    def save(self, story: Story) -> None:
        pass

# Infrastructure implementa (Adapter)
class SQLiteStoryRepository(StoryRepository):
    def save(self, story: Story) -> None:
        # Implementação concreta
```

**3. Casos de Uso como Orquestradores**
```python
class CalculateScheduleUseCase:
    """Calcula cronograma do backlog ordenando, alocando e calculando datas"""
    
    def __init__(
        self,
        story_repo: StoryRepository,
        developer_repo: DeveloperRepository,
        config_repo: ConfigurationRepository,
        sorter: BacklogSorter,
        calculator: ScheduleCalculator
    ):
        # Dependências injetadas
```

### Padrões de Design Aplicados

1. **Repository Pattern** - Abstração de acesso a dados
2. **Use Case Pattern** - Casos de uso como classes dedicadas
3. **DTO Pattern** - Transferência de dados entre camadas
4. **Observer Pattern** - Para recálculo reativo
5. **Strategy Pattern** - Algoritmos de ordenação
6. **Factory Pattern** - Criação de entidades
7. **Unit of Work Pattern** - Transações de banco de dados

---

## PLANO DE FASES

### FASE 1: Fundação e Domínio (Base Sólida)
**Duração Estimada:** 2-3 semanas  
**Story Points:** 34 SP  
**Objetivo:** Estabelecer arquitetura base e implementar camada de domínio completa

#### Tarefas

**1.1 Setup do Projeto (3 SP)**
- [ ] Criar estrutura de diretórios conforme Clean Architecture
- [ ] Configurar ambiente virtual Python
- [ ] Criar requirements.txt com dependências:
  - pytest, pytest-cov
  - SQLite (built-in)
  - openpyxl
  - PyQt6 ou PySide6
- [ ] Configurar pytest e cobertura de testes
- [ ] Criar .gitignore apropriado
- [ ] Documentar estrutura no README.md

**1.2 Entidades de Domínio (5 SP)**
- [ ] Implementar `Story` entity com todos os atributos
- [ ] Implementar `Developer` entity
- [ ] Implementar `Configuration` entity
- [ ] Criar value objects:
  - `StoryPoint` (validação: apenas 3, 5, 8, 13)
  - `StoryStatus` (Enum)
  - `StoryId` (geração automática)
  - `DeveloperId` (geração automática)
- [ ] Implementar validações de domínio
- [ ] Testes unitários para todas as entidades (> 90% cobertura)

**1.3 Exceções de Domínio (2 SP)**
- [ ] Criar hierarquia de exceções:
  - `DomainException` (base)
  - `InvalidStoryPointException`
  - `CyclicDependencyException`
  - `DeveloperNotFoundException`
  - `StoryNotFoundException`
- [ ] Documentar cada exceção
- [ ] Testes para exceções

**1.4 Serviço de Detecção de Ciclos (8 SP)**
- [ ] Implementar `CycleDetector` service
- [ ] Algoritmo DFS para detecção de ciclos em grafo direcionado
- [ ] Método `has_cycle(dependencies: Dict[str, List[str]]) -> bool`
- [ ] Método `find_cycle_path(dependencies: Dict[str, List[str]]) -> List[str]`
- [ ] Otimizar para performance (< 100ms para 100 histórias)
- [ ] Testes extensivos:
  - Caso sem ciclo
  - Ciclo direto (A → B → A)
  - Ciclo indireto (A → B → C → A)
  - Múltiplos ciclos
  - Grafos complexos

**1.5 Serviço de Ordenação de Backlog (8 SP)**
- [ ] Implementar `BacklogSorter` service
- [ ] Algoritmo de ordenação topológica (Kahn's Algorithm)
- [ ] Ordenação secundária por prioridade dentro do mesmo nível
- [ ] Método `sort(stories: List[Story]) -> List[Story]`
- [ ] Otimizar para performance (< 500ms para 100 histórias)
- [ ] Testes extensivos:
  - Histórias sem dependências
  - Dependências simples
  - Dependências complexas (árvore e DAG)
  - Validação de ordem correta

**1.6 Serviço de Cálculo de Cronograma (8 SP)**
- [ ] Implementar `ScheduleCalculator` service
- [ ] Lógica de cálculo de duração: `ceil(SP / (VelocidadeSprint / DiasUteis))`
- [ ] Lógica de cálculo de datas (apenas dias úteis)
- [ ] Considerar alocação de desenvolvedor (histórias do mesmo dev em sequência)
- [ ] Método `calculate(stories: List[Story], config: Configuration) -> List[Story]`
- [ ] Testes extensivos:
  - Cálculo de duração correto
  - Sequenciamento por desenvolvedor
  - Histórias paralelas (desenvolvedores diferentes)
  - Casos extremos (SP 13, velocidade baixa)

#### Entregáveis da Fase 1
- ✅ Estrutura de projeto Clean Architecture
- ✅ Camada de domínio completa e testada
- ✅ Algoritmos core funcionando (ciclos, ordenação, cronograma)
- ✅ Cobertura de testes > 90% na camada de domínio
- ✅ Documentação de arquitetura

#### Critérios de Aceitação da Fase 1
- [ ] Todos os testes de domínio passando
- [ ] Cobertura > 90%
- [ ] Algoritmos validados com casos complexos
- [ ] Código revisado e seguindo PEP 8
- [ ] Docstrings completas em português

---

### FASE 2: Camada de Aplicação (Casos de Uso)
**Duração Estimada:** 2 semanas  
**Story Points:** 26 SP  
**Objetivo:** Implementar todos os casos de uso orquestrando o domínio

#### Tarefas

**2.1 Definir Interfaces (Ports) (3 SP)**
- [ ] Criar interface `StoryRepository` (ABC)
  - Métodos: save, find_by_id, find_all, delete, exists
- [ ] Criar interface `DeveloperRepository` (ABC)
  - Métodos: save, find_by_id, find_all, delete, exists
- [ ] Criar interface `ConfigurationRepository` (ABC)
  - Métodos: get, save
- [ ] Criar interface `ExcelService` (ABC)
  - Métodos: import_stories, export_backlog
- [ ] Documentar contratos das interfaces

**2.2 DTOs (Data Transfer Objects) (2 SP)**
- [ ] Criar `StoryDTO` para transferência entre camadas
- [ ] Criar `DeveloperDTO`
- [ ] Criar `ConfigurationDTO`
- [ ] Criar `BacklogDTO` (lista de histórias com metadados)
- [ ] Implementar conversores Entity ↔ DTO

**2.3 Casos de Uso de História (8 SP)**
- [ ] Implementar `CreateStoryUseCase`
  - Validar dados
  - Gerar ID automático
  - Definir prioridade inicial
  - Persistir via repository
- [ ] Implementar `UpdateStoryUseCase`
  - Validar dados
  - Verificar mudanças que requerem recálculo
  - Persistir mudanças
  - Retornar flag se requer recálculo
- [ ] Implementar `DeleteStoryUseCase`
  - Remover referências de dependências
  - Deletar história
- [ ] Implementar `ListStoriesUseCase`
  - Buscar todas histórias
  - Retornar DTOs ordenados
- [ ] Implementar `DuplicateStoryUseCase`
  - Copiar dados (exceto ID)
  - Gerar novo ID
  - Resetar campos (status, desenvolvedor)
- [ ] Testes de integração narrow para cada caso de uso

**2.4 Casos de Uso de Desenvolvedor (3 SP)**
- [ ] Implementar `CreateDeveloperUseCase`
  - Gerar ID automático (2 letras + número se conflito)
  - Validar unicidade
  - Persistir
- [ ] Implementar `UpdateDeveloperUseCase`
- [ ] Implementar `DeleteDeveloperUseCase`
  - Remover alocações em histórias
  - Deletar desenvolvedor
- [ ] Testes de integração narrow

**2.5 Casos de Uso de Dependências (3 SP)**
- [ ] Implementar `AddDependencyUseCase`
  - Validar que história dependente existe
  - Validar que não cria ciclo (usar CycleDetector)
  - Adicionar dependência
  - Retornar sucesso ou erro com ciclo detectado
- [ ] Implementar `RemoveDependencyUseCase`
- [ ] Testes com cenários de ciclos

**2.6 Casos de Uso de Cronograma (5 SP)**
- [ ] Implementar `CalculateScheduleUseCase`
  - Buscar todas histórias
  - Ordenar usando BacklogSorter
  - Alocar desenvolvedores (round-robin)
  - Calcular cronograma usando ScheduleCalculator
  - Persistir atualizações
- [ ] Implementar `AllocateDevelopersUseCase`
  - Buscar histórias não alocadas
  - Distribuir desenvolvedores (round-robin)
  - Persistir alocações
- [ ] Implementar `ChangePriorityUseCase`
  - Validar movimento (não ultrapassar limites)
  - Trocar prioridades
  - Disparar recálculo
- [ ] Testes de integração narrow

**2.7 Casos de Uso de Import/Export (2 SP)**
- [ ] Implementar `ImportFromExcelUseCase`
  - Validar arquivo Excel via ExcelService
  - Criar histórias em lote
  - Retornar relatório (sucesso/falhas)
- [ ] Implementar `ExportToExcelUseCase`
  - Buscar backlog ordenado
  - Exportar via ExcelService
- [ ] Testes com arquivos de exemplo

#### Entregáveis da Fase 2
- ✅ Todos os casos de uso implementados
- ✅ Interfaces (ports) bem definidas
- ✅ DTOs para comunicação entre camadas
- ✅ Testes de integração narrow > 85% cobertura
- ✅ Documentação de casos de uso

#### Critérios de Aceitação da Fase 2
- [ ] Todos os casos de uso testados isoladamente
- [ ] Testes de integração narrow passando
- [ ] Validações de negócio funcionando
- [ ] Contratos de interfaces claros

---

### FASE 3: Camada de Infraestrutura (Persistência)
**Duração Estimada:** 1.5 semanas  
**Story Points:** 21 SP  
**Objetivo:** Implementar persistência SQLite e serviço de Excel

#### Tarefas

**3.1 Setup do Banco de Dados (3 SP)**
- [ ] Criar `SQLiteConnection` singleton
- [ ] Implementar conexão com tratamento de erros
- [ ] Criar script SQL de migrations (create_tables.sql):
  ```sql
  CREATE TABLE stories (
      id TEXT PRIMARY KEY,
      feature TEXT NOT NULL,
      name TEXT NOT NULL,
      status TEXT NOT NULL,
      priority INTEGER NOT NULL,
      developer_id TEXT,
      dependencies TEXT,  -- JSON array
      story_point INTEGER NOT NULL,
      start_date TEXT,
      end_date TEXT,
      duration INTEGER
  );
  
  CREATE TABLE developers (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL
  );
  
  CREATE TABLE configuration (
      id INTEGER PRIMARY KEY CHECK (id = 1),
      story_points_per_sprint INTEGER NOT NULL,
      workdays_per_sprint INTEGER NOT NULL
  );
  ```
- [ ] Implementar migração automática na inicialização
- [ ] Testes de conexão e migração

**3.2 Implementar Repositories (8 SP)**
- [ ] Implementar `SQLiteStoryRepository`
  - Métodos CRUD completos
  - Serialização de dependências (JSON)
  - Conversão Entity ↔ Database
  - Queries otimizadas
- [ ] Implementar `SQLiteDeveloperRepository`
  - CRUD simples
- [ ] Implementar `SQLiteConfigurationRepository`
  - Get/Save singleton
  - Valores padrão na primeira execução
- [ ] Testes de integração para cada repository
  - Operações CRUD
  - Tratamento de erros
  - Integridade de dados

**3.3 Unit of Work Pattern (3 SP)**
- [ ] Implementar `UnitOfWork` para transações
- [ ] Métodos: begin, commit, rollback
- [ ] Integrar com repositories
- [ ] Testes de transações (commit e rollback)

**3.4 Excel Service (5 SP)**
- [ ] Implementar `ExcelServiceImpl` usando openpyxl
- [ ] Método `import_stories(filepath: str) -> List[StoryDTO]`
  - Validar colunas obrigatórias
  - Validar dados (Story Points)
  - Retornar lista de DTOs ou erros por linha
- [ ] Método `export_backlog(filepath: str, stories: List[StoryDTO])`
  - Criar planilha com formatação
  - Cabeçalho em negrito
  - Bordas nas células
  - Auto-ajustar largura de colunas
- [ ] Testes com arquivos Excel reais
  - Import sucesso
  - Import com erros
  - Export e verificação

**3.5 Testes de Integração Completos (2 SP)**
- [ ] Testar fluxo completo: Repository → Database → Recovery
- [ ] Testar cenários de erro (arquivo corrompido, falta de permissão)
- [ ] Validar performance (100 histórias < 1s)

#### Entregáveis da Fase 3
- ✅ Banco de dados SQLite configurado e migrações automáticas
- ✅ Repositories implementados e testados
- ✅ Excel service funcionando (import/export)
- ✅ Persistência de dados garantida
- ✅ Testes de integração > 85% cobertura

#### Critérios de Aceitação da Fase 3
- [ ] Dados persistem corretamente em SQLite
- [ ] Import/Export Excel funcionando
- [ ] Transações com commit e rollback
- [ ] Performance aceitável
- [ ] Testes de integração passando

---

### FASE 4: Interface Gráfica (Apresentação)
**Duração Estimada:** 3 semanas  
**Story Points:** 34 SP  
**Objetivo:** Implementar interface desktop completa com PyQt6

#### Tarefas

**4.1 Setup PyQt6 e Janela Principal (3 SP)**
- [ ] Configurar PyQt6 no projeto
- [ ] Criar `MainWindow` com layout base
- [ ] Implementar menu principal:
  - Menu Desenvolvedor
  - Menu História
  - Menu Geral
- [ ] Criar barra de ferramentas com botões principais
- [ ] Aplicar estilos básicos (QSS)
- [ ] Testar abertura da aplicação

**4.2 Tabela de Backlog Editável (13 SP)**
- [ ] Criar `EditableTableWidget` customizado (herda QTableWidget)
- [ ] Implementar colunas:
  - Prioridade, ID, Feature, Nome, Status, Desenvolvedor, Dependências, SP, Início, Fim, Duração
- [ ] Implementar edição inline:
  - Double-click habilita edição
  - Enter/Esc para salvar/cancelar
  - Validações em tempo real
  - Dropdown para Status, Desenvolvedor, Story Point
- [ ] Implementar seleção de linha
- [ ] Implementar delegates customizados para campos especiais
- [ ] Adicionar feedback visual (cores para status, erros)
- [ ] Integrar com controller para salvar mudanças
- [ ] Testes de UI:
  - Edição inline funciona
  - Validações bloqueiam valores inválidos
  - Mudanças persistem

**4.3 Formulários de CRUD (8 SP)**
- [ ] Criar `StoryFormDialog`
  - Campos: Feature, Nome, SP, Status, Dev, Dependências, Prioridade
  - Validações
  - Modo criar/editar
- [ ] Criar `DeveloperFormDialog`
  - Campo: Nome
  - Validações
- [ ] Criar `ConfigurationDialog`
  - Campos: SP por Sprint, Dias Úteis
  - Cálculo automático de velocidade
  - Botão "Restaurar Padrões"
- [ ] Implementar comunicação com controllers
- [ ] Testes de validação de formulários

**4.4 Controllers (5 SP)**
- [ ] Implementar `MainController`
  - Coordena toda aplicação
  - Gerencia eventos de menu e toolbar
  - Integra com casos de uso
- [ ] Implementar `StoryController`
  - CRUD de histórias
  - Gerencia recálculo reativo
  - Comunica com tabela
- [ ] Implementar `DeveloperController`
  - CRUD de desenvolvedores
- [ ] Implementar `ScheduleController`
  - Calcula cronograma
  - Aloca desenvolvedores
  - Muda prioridades
- [ ] Testes de integração UI → Controller → Use Case

**4.5 Atalhos de Teclado e Menu (2 SP)**
- [ ] Implementar atalhos:
  - Delete: Deletar história
  - Ctrl+D: Duplicar
  - Ctrl+Up/Down: Mover prioridade
  - F5: Recalcular cronograma
  - Ctrl+E: Exportar Excel
- [ ] Vincular atalhos aos controllers
- [ ] Adicionar menu "Ajuda" com lista de atalhos
- [ ] Testes de atalhos

**4.6 Dialogs de Confirmação e Mensagens (3 SP)**
- [ ] Criar sistema de mensagens centralizado
- [ ] Confirmações de deleção
- [ ] Mensagens de sucesso/erro
- [ ] Progress dialog para operações longas (cronograma)
- [ ] Testes de fluxo com confirmações

#### Entregáveis da Fase 4
- ✅ Interface gráfica completa e funcional
- ✅ Tabela editável tipo Excel
- ✅ Formulários de CRUD
- ✅ Atalhos de teclado
- ✅ Controllers conectando UI a casos de uso
- ✅ Aplicação desktop funcionando end-to-end

#### Critérios de Aceitação da Fase 4
- [ ] Todas as operações CRUD funcionam via UI
- [ ] Edição inline funciona e valida
- [ ] Mensagens de erro/sucesso claras
- [ ] Atalhos funcionando
- [ ] Interface responsiva

---

### FASE 5: Features Avançadas e Otimização
**Duração Estimada:** 2 semanas  
**Story Points:** 21 SP  
**Objetivo:** Implementar timeline, otimizar performance, polir UX

#### Tarefas

**5.1 Visualização Timeline/Roadmap (13 SP)**
- [ ] Pesquisar biblioteca de Gantt para Qt (ou implementar custom)
- [ ] Criar `TimelineView` widget
- [ ] Implementar:
  - Eixo horizontal: Datas (escala ajustável)
  - Eixo vertical: Desenvolvedores
  - Barras de tarefas com duração
  - Cores por desenvolvedor
  - Tooltips com detalhes
  - Navegação (scroll horizontal)
- [ ] Criar `TimelineViewModel` para preparar dados
- [ ] Integrar com MainWindow (botão ou aba)
- [ ] Testes de renderização

**5.2 Filtros de Backlog (5 SP)**
- [ ] Criar painel de filtros na UI
- [ ] Implementar filtros por:
  - Feature (multi-seleção)
  - Status (multi-seleção)
  - Desenvolvedor (multi-seleção)
  - Story Point (multi-seleção)
- [ ] Atualizar tabela em tempo real
- [ ] Mostrar contador de histórias filtradas
- [ ] Botão "Limpar Filtros"
- [ ] Testes de filtros combinados

**5.3 Otimização de Performance (3 SP)**
- [ ] Profiling do cálculo de cronograma
- [ ] Otimizar algoritmos se necessário
- [ ] Implementar cache onde apropriado
- [ ] Lazy loading na tabela (se > 100 histórias)
- [ ] Testes de performance:
  - 50 histórias < 1s
  - 100 histórias < 2s
  - Edição inline < 100ms

#### Entregáveis da Fase 5
- ✅ Visualização Timeline funcional
- ✅ Sistema de filtros completo
- ✅ Performance otimizada
- ✅ UX polida

#### Critérios de Aceitação da Fase 5
- [ ] Timeline renderiza corretamente
- [ ] Filtros funcionam em combinação
- [ ] Performance atende requisitos (< 2s)
- [ ] Interface responsiva mesmo com muitos dados

---

### FASE 6: Testes, Documentação e Empacotamento
**Duração Estimada:** 1.5 semanas  
**Story Points:** 13 SP  
**Objetivo:** Garantir qualidade, documentar e criar executável standalone

#### Tarefas

**6.1 Testes de Integração E2E (5 SP)**
- [ ] Criar suite de testes E2E simulando uso real:
  - Test: Importar planilha → Cadastrar devs → Calcular cronograma → Exportar
  - Test: Criar histórias manualmente → Adicionar dependências → Detectar ciclo
  - Test: Editar SP inline → Verificar recálculo automático
  - Test: Mudar prioridade → Verificar reordenação
  - Test: Alocar dev manualmente → Verificar cronograma
- [ ] Validar cobertura total > 90%
- [ ] Corrigir bugs encontrados

**6.2 Documentação (3 SP)**
- [ ] Atualizar README.md com:
  - Descrição do projeto
  - Arquitetura (diagrama Clean Architecture)
  - Como executar
  - Como rodar testes
- [ ] Documentar casos de uso (diagramas)
- [ ] Criar manual do usuário (PDF ou Markdown)
- [ ] Documentar requisitos de sistema
- [ ] Adicionar screenshots da aplicação

**6.3 Empacotamento com PyInstaller (3 SP)**
- [ ] Configurar PyInstaller spec file
- [ ] Resolver dependências (PyQt6, SQLite, openpyxl)
- [ ] Criar executável standalone:
  ```bash
  pyinstaller --onefile --windowed --name="BacklogManager" main.py
  ```
- [ ] Testar executável em máquina limpa Windows
- [ ] Otimizar tamanho do executável (remover módulos desnecessários)
- [ ] Incluir ícone da aplicação
- [ ] Criar instalador (opcional: com Inno Setup)

**6.4 Testes Finais em Windows (2 SP)**
- [ ] Testar executável em Windows 10
- [ ] Testar executável em Windows 11
- [ ] Verificar:
  - Inicialização sem erros
  - Criação de banco de dados
  - Todas funcionalidades
  - Import/Export Excel
  - Performance
- [ ] Corrigir issues específicos de Windows

#### Entregáveis da Fase 6
- ✅ Cobertura de testes > 90%
- ✅ Documentação completa
- ✅ Executável standalone funcionando
- ✅ Manual do usuário
- ✅ Projeto pronto para distribuição

#### Critérios de Aceitação da Fase 6
- [ ] Todos os testes passando
- [ ] Cobertura > 90%
- [ ] Executável funciona em Windows sem instalação
- [ ] Documentação completa e clara
- [ ] Zero bugs críticos

---

## CRONOGRAMA RESUMIDO

| Fase | Duração | Story Points | Entregas Principais |
|------|---------|--------------|---------------------|
| Fase 1: Fundação e Domínio | 2-3 semanas | 34 SP | Entidades, algoritmos core, detecção ciclos |
| Fase 2: Casos de Uso | 2 semanas | 26 SP | Todos os use cases, DTOs, interfaces |
| Fase 3: Infraestrutura | 1.5 semanas | 21 SP | Persistência SQLite, Excel service |
| Fase 4: Interface Gráfica | 3 semanas | 34 SP | UI completa, tabela editável, controllers |
| Fase 5: Features Avançadas | 2 semanas | 21 SP | Timeline, filtros, otimização |
| Fase 6: Testes e Empacotamento | 1.5 semanas | 13 SP | Testes E2E, docs, executável |
| **TOTAL** | **12-14 semanas** | **149 SP** | **Aplicação completa** |

---

## RISCOS E MITIGAÇÕES

### Risco 1: Complexidade dos Algoritmos de Grafo
**Probabilidade:** Média  
**Impacto:** Alto  
**Mitigação:**
- Estudar algoritmos DFS e Topological Sort antes de implementar
- Criar casos de teste complexos desde o início
- Considerar uso de bibliotecas (networkx) se complexidade for muito alta
- Alocar tempo extra na Fase 1 se necessário

### Risco 2: Performance do Recálculo Automático
**Probabilidade:** Média  
**Impacto:** Alto  
**Mitigação:**
- Implementar profiling desde o início
- Otimizar algoritmos (evitar recalcular tudo, apenas afetados)
- Implementar debouncing para evitar múltiplos recálculos
- Considerar cálculo assíncrono se necessário

### Risco 3: Dificuldades com PyInstaller
**Probabilidade:** Alta  
**Impacto:** Médio  
**Mitigação:**
- Testar empacotamento cedo (após Fase 4)
- Pesquisar issues conhecidas com PyQt6
- Considerar alternativas (cx_Freeze, Nuitka)
- Reservar tempo extra na Fase 6

### Risco 4: Edição Inline Complexa
**Probabilidade:** Média  
**Impacto:** Médio  
**Mitigação:**
- Estudar exemplos de edição inline em PyQt
- Implementar POC (Proof of Concept) antes da Fase 4
- Considerar simplificação (abrir dialog) se muito complexo
- Iterar com feedback de usuário

### Risco 5: Timeline/Gantt Chart Complexidade
**Probabilidade:** Alta  
**Impacto:** Baixo  
**Mitigação:**
- Pesquisar bibliotecas existentes (PyQtGantt, pygantt)
- Implementar versão simplificada se bibliotecas não funcionarem
- Considerar visualização alternativa (calendário)
- Feature é Prioridade Média, pode ser MVP sem ela

---

## BOAS PRÁTICAS DE IMPLEMENTAÇÃO

### 1. Test-Driven Development (TDD)
```python
# Escrever teste ANTES da implementação
def test_cycle_detector_finds_simple_cycle():
    """Deve detectar ciclo simples A -> B -> A"""
    dependencies = {"A": ["B"], "B": ["A"]}
    detector = CycleDetector()
    
    assert detector.has_cycle(dependencies) == True
    assert detector.find_cycle_path(dependencies) == ["A", "B", "A"]

# DEPOIS implementar
class CycleDetector:
    def has_cycle(self, dependencies):
        # Implementação DFS
        ...
```

### 2. Commits Atômicos e Descritivos
```bash
# Bom
git commit -m "feat(domain): implement Story entity with validations"
git commit -m "test(domain): add Story entity unit tests"
git commit -m "refactor(domain): extract StoryPoint validation to value object"

# Ruim
git commit -m "updates"
git commit -m "fix stuff"
```

### 3. Docstrings em Português
```python
class BacklogSorter:
    """
    Serviço de ordenação de backlog usando ordenação topológica.
    
    Ordena histórias considerando:
    1. Dependências técnicas (histórias sem dependências vêm primeiro)
    2. Prioridade numérica (menor número = maior prioridade)
    
    Raises:
        CyclicDependencyException: Se houver ciclo nas dependências
    """
    
    def sort(self, stories: List[Story]) -> List[Story]:
        """
        Ordena lista de histórias respeitando dependências e prioridade.
        
        Args:
            stories: Lista de histórias para ordenar
            
        Returns:
            Lista ordenada de histórias
            
        Raises:
            CyclicDependencyException: Se detectado ciclo
        """
```

### 4. Type Hints Consistentes
```python
from typing import List, Optional, Dict

def calculate_schedule(
    stories: List[Story],
    developers: List[Developer],
    config: Configuration
) -> List[Story]:
    """Calcula cronograma completo do backlog"""
    ...
```

### 5. Validações Explícitas
```python
class StoryPoint:
    """Value Object para Story Points com validação"""
    
    VALID_VALUES = [3, 5, 8, 13]
    
    def __init__(self, value: int):
        if value not in self.VALID_VALUES:
            raise InvalidStoryPointException(
                f"Story Point deve ser um de {self.VALID_VALUES}, recebido: {value}"
            )
        self._value = value
    
    @property
    def value(self) -> int:
        return self._value
```

### 6. Injeção de Dependências
```python
# Use case recebe dependências via construtor
class CalculateScheduleUseCase:
    def __init__(
        self,
        story_repository: StoryRepository,
        developer_repository: DeveloperRepository,
        config_repository: ConfigurationRepository,
        sorter: BacklogSorter,
        calculator: ScheduleCalculator
    ):
        self._story_repo = story_repository
        self._developer_repo = developer_repository
        self._config_repo = config_repository
        self._sorter = sorter
        self._calculator = calculator
    
    def execute(self) -> None:
        """Executa cálculo completo de cronograma"""
        stories = self._story_repo.find_all()
        developers = self._developer_repo.find_all()
        config = self._config_repo.get()
        
        # Orquestra serviços de domínio
        sorted_stories = self._sorter.sort(stories)
        scheduled_stories = self._calculator.calculate(
            sorted_stories, developers, config
        )
        
        # Persiste resultados
        for story in scheduled_stories:
            self._story_repo.save(story)
```

---

## MÉTRICAS DE QUALIDADE

### Objetivos de Qualidade
- **Cobertura de Testes:** ≥ 90%
- **Complexidade Ciclomática:** ≤ 10 por função
- **Duplicação de Código:** < 5%
- **Conformidade PEP 8:** 100%
- **Docstrings:** 100% de funções/classes públicas

### Ferramentas de Qualidade
```bash
# Cobertura
pytest --cov=backlog_manager --cov-report=html

# Linting
flake8 backlog_manager/
pylint backlog_manager/

# Complexidade
radon cc backlog_manager/ -a

# Type checking
mypy backlog_manager/

# Formatação
black backlog_manager/
isort backlog_manager/
```

### Integração Contínua (Opcional)
- Configurar GitHub Actions ou similar
- Rodar testes em cada commit
- Bloquear merge se testes falharem
- Verificar cobertura mínima

---

## STACK TECNOLÓGICO DETALHADO

### Core
- **Python:** 3.11+ (f-strings, type hints, dataclasses)
- **PyQt6 ou PySide6:** Interface gráfica
- **SQLite:** Banco de dados (built-in)

### Bibliotecas
```txt
# requirements.txt
PyQt6==6.6.0
openpyxl==3.1.2
pytest==7.4.3
pytest-cov==4.1.0

# requirements-dev.txt
black==23.12.0
flake8==6.1.0
pylint==3.0.3
mypy==1.7.1
isort==5.13.2
radon==6.0.1
PyInstaller==6.3.0
```

### Estrutura de Configuração
```python
# config/settings.py
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "backlog.db"
EXCEL_IMPORT_COLUMNS = ["Feature", "Nome", "StoryPoint"]

DEFAULT_STORY_POINTS_PER_SPRINT = 21
DEFAULT_WORKDAYS_PER_SPRINT = 15
```

---

## CONSIDERAÇÕES FINAIS

### Próximos Passos Imediatos
1. Criar estrutura de diretórios (Fase 1.1)
2. Configurar ambiente virtual
3. Instalar dependências
4. Implementar primeira entidade (Story) com TDD
5. Configurar testes e coverage

### Pontos de Decisão Importantes
- **Framework UI:** PyQt6 (licença GPL) vs PySide6 (licença LGPL) - Recomendo PySide6 por flexibilidade de licença
- **Timeline Library:** Pesquisar antes de implementar (Fase 5) - pode economizar tempo
- **Empacotamento:** Testar PyInstaller cedo para evitar surpresas

### Recomendações Arquiteturais
1. **Não pular camadas:** Presentation nunca chama Domain diretamente
2. **Manter domínio puro:** Zero dependências de frameworks no Domain
3. **Testes primeiro:** TDD especialmente para lógica complexa (algoritmos)
4. **Refatorar com confiança:** Testes permitem refactoring seguro

### Estimativa Realista
- **Desenvolvedor Solo:** 12-14 semanas (3-3.5 meses)
- **Dupla de Desenvolvedores:** 8-10 semanas (2-2.5 meses)
- **Time de 3+:** 6-8 semanas (1.5-2 meses)

---

**Este plano está pronto para execução. Comece pela Fase 1 e siga incrementalmente!**
