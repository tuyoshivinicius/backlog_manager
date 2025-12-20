# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão Geral do Projeto

Sistema desktop para gestão inteligente de backlog de desenvolvimento. Organiza automaticamente tarefas considerando dependências, calcula cronogramas e aloca desenvolvedores. Arquitetura baseada em **Clean Architecture** rigorosa com separação completa entre camadas.

**Tecnologias:** Python 3.11+, PySide6/PyQt6, SQLite, openpyxl
**Distribuição:** Executável standalone via PyInstaller para Windows

## Comandos de Desenvolvimento

### Setup Inicial
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Windows)
.\venv\Scripts\activate

# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt
```

### Testes
```bash
# Executar todos os testes com cobertura
pytest

# Testes unitários apenas
pytest tests/unit -v

# Testes de um módulo específico
pytest tests/unit/domain/test_story.py -v

# Cobertura detalhada com HTML
pytest --cov=backlog_manager --cov-report=html

# Verificar cobertura de domínio especificamente
pytest --cov=backlog_manager/domain --cov-report=term --cov-fail-under=90
```

### Qualidade de Código
```bash
# Formatação automática
black backlog_manager/

# Organizar imports
isort backlog_manager/

# Linting
flake8 backlog_manager/

# Type checking
mypy backlog_manager/

# Verificar complexidade ciclomática
radon cc backlog_manager/ -a -nc
```

### Build e Distribuição
```bash
# Criar executável standalone
pyinstaller --onefile --windowed --name="BacklogManager" main.py
```

## Arquitetura

### Estrutura de Camadas (Clean Architecture)

```
backlog_manager/
├── domain/              # ✅ NÚCLEO - Sem dependências externas
│   ├── entities/        # Story, Developer, Configuration
│   ├── value_objects/   # StoryPoint, StoryStatus
│   ├── services/        # CycleDetector, BacklogSorter, ScheduleCalculator
│   └── exceptions/      # Exceções de domínio
├── application/         # ✅ Depende apenas de domain/
│   ├── use_cases/       # 23 casos de uso implementados
│   │   ├── story/       # 7 casos (Create, Update, Delete, Get, List, GetBacklog, ChangePriority)
│   │   ├── developer/   # 5 casos (Create, Update, Delete, Get, List)
│   │   ├── dependency/  # 2 casos (Add, Remove)
│   │   ├── schedule/    # 2 casos (Calculate, AllocateDevelopers)
│   │   ├── configuration/ # 2 casos (Get, Update)
│   │   └── excel/       # 2 casos (Import, Export)
│   ├── interfaces/      # Ports (5 interfaces abstratas)
│   │   ├── repositories/  # StoryRepository, DeveloperRepository, ConfigurationRepository
│   │   └── services/      # ExcelService
│   └── dto/             # 4 DTOs + conversores
├── infrastructure/      # ✅ Depende de application/ e domain/
│   ├── database/        # SQLite implementations
│   │   ├── sqlite_connection.py  # Singleton de conexão
│   │   ├── schema.sql            # Schema completo
│   │   ├── unit_of_work.py       # Padrão Unit of Work
│   │   └── repositories/         # 3 repositories (Story, Developer, Configuration)
│   └── excel/           # openpyxl implementation
│       └── openpyxl_excel_service.py  # Import/Export Excel
└── presentation/        # Depende de application/
    ├── views/           # PySide6 UI (IMPLEMENTADO)
    ├── controllers/     # Controladores de UI (IMPLEMENTADO)
    ├── utils/           # Utilitários de UI
    └── styles/          # Temas e estilos QSS
```

### Regra de Dependência

**CRÍTICO:** As dependências sempre apontam para dentro (em direção ao domínio):
- `domain/` → Não depende de nada
- `application/` → Depende apenas de `domain/`
- `infrastructure/` → Depende de `application/` e `domain/`
- `presentation/` → Depende de `application/`

**NUNCA** faça:
- Domain importar de Application/Infrastructure/Presentation
- Application importar de Infrastructure/Presentation
- Presentation chamar Domain diretamente (sempre via Application)

## Algoritmos Core do Domínio

### 1. Detecção de Ciclos (CycleDetector)
- **Algoritmo:** DFS (Depth-First Search)
- **Localização:** `domain/services/cycle_detector.py`
- **Complexidade:** O(V + E)
- **Performance:** < 100ms para 100 histórias
- **Uso:** Validar dependências antes de adicionar/modificar

### 2. Ordenação de Backlog (BacklogSorter)
- **Algoritmo:** Topological Sort (Kahn's Algorithm) + ordenação por prioridade
- **Localização:** `domain/services/backlog_sorter.py`
- **Complexidade:** O(V + E)
- **Performance:** < 500ms para 100 histórias
- **Critérios:** 1) Dependências técnicas, 2) Prioridade numérica

### 3. Cálculo de Cronograma (ScheduleCalculator)
- **Fórmula:** `Duração (dias) = ceil(StoryPoints / VelocidadePorDia)`
- **Localização:** `domain/services/schedule_calculator.py`
- **Considera:** Apenas dias úteis (segunda a sexta)
- **Sequenciamento:** Histórias do mesmo desenvolvedor executam em sequência

## Regras de Negócio Críticas

### Story Points
- **Valores Válidos:** 3, 5, 8, 13 (escala Fibonacci modificada)
- **Mapeamento:** P=3, M=5, G=8, GG=13
- **Validação:** No value object `StoryPoint`

### Status de História
- **Fluxo:** BACKLOG → EXECUÇÃO → TESTES → CONCLUÍDO
- **Alternativo:** Qualquer → IMPEDIDO
- **Tipo:** Enum em `StoryStatus`

### Dependências
- **Proibido:** Ciclos e auto-referências
- **Validação:** Via `CycleDetector` antes de salvar
- **Impacto:** Mudança em dependências requer recálculo de cronograma

### Recálculo Reativo
**Gatilhos que requerem recálculo automático:**
- Mudança em Story Points
- Mudança em prioridade
- Alocação/mudança de desenvolvedor
- Adição/remoção de dependência

## Padrões de Código

### Código em Inglês, Docstrings em Português
```python
class BacklogSorter:
    """
    Serviço de ordenação de backlog usando ordenação topológica.

    Ordena histórias considerando dependências e prioridade.
    """

    def sort(self, stories: List[Story]) -> List[Story]:
        """
        Ordena lista de histórias respeitando dependências.

        Args:
            stories: Lista de histórias para ordenar

        Returns:
            Lista ordenada de histórias

        Raises:
            CyclicDependencyException: Se detectado ciclo
        """
```

### Injeção de Dependências (Casos de Uso)
```python
class CalculateScheduleUseCase:
    def __init__(
        self,
        story_repository: StoryRepository,  # Interface abstrata
        sorter: BacklogSorter,
        calculator: ScheduleCalculator
    ):
        self._story_repo = story_repository
        self._sorter = sorter
        self._calculator = calculator
```

### Validações Explícitas (Entidades)
```python
@dataclass
class Story:
    id: str
    feature: str
    # ...

    def __post_init__(self) -> None:
        """Valida invariantes após inicialização."""
        self._validate()

    def _validate(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("ID da história não pode ser vazio")
```

### Repository Pattern (Interfaces)
```python
# Application define o contrato (Port)
class StoryRepository(ABC):
    @abstractmethod
    def save(self, story: Story) -> None:
        pass

# Infrastructure implementa (Adapter)
class SQLiteStoryRepository(StoryRepository):
    def save(self, story: Story) -> None:
        # Implementação concreta com SQLite
```

## Fases de Implementação

O projeto está dividido em 6 fases (detalhes em [plano_fase1.md](plano_fase1.md), [plano_fase2.md](plano_fase2.md), [plano_fase3.md](plano_fase3.md) e [plano_implementacao.md](plano_implementacao.md)):

1. **Fase 1 (✅ CONCLUÍDA):** Fundação e Domínio - Entidades, value objects, algoritmos core
   - Documentação: [FASE1_COMPLETA.md](FASE1_COMPLETA.md)
   - 34 SP implementados - 94 testes unitários - Cobertura >90%

2. **Fase 2 (✅ CONCLUÍDA):** Casos de Uso - Application layer com todos os use cases
   - Documentação: [FASE2_COMPLETA.md](FASE2_COMPLETA.md)
   - 26 SP implementados - 23 casos de uso - 5 interfaces (Ports)

3. **Fase 3 (✅ CONCLUÍDA):** Infraestrutura - SQLite repositories e Excel service
   - Documentação: [FASE3_COMPLETA.md](FASE3_COMPLETA.md)
   - 21 SP implementados - 3 repositories - Unit of Work - Excel Service

4. **Fase 4 (✅ CONCLUÍDA):** Interface Gráfica - PySide6 com tabela editável
   - Documentação: [FASE4_COMPLETA.md](FASE4_COMPLETA.md)
   - 34 SP implementados - 20 arquivos - Interface desktop completa
5. **Fase 5 (PRÓXIMA):** Features Avançadas - Timeline/Roadmap, filtros, otimização
6. **Fase 6:** Testes E2E, documentação e empacotamento

## Métricas de Qualidade

**Requisitos Obrigatórios:**
- Cobertura de testes: **≥ 90%**
- Complexidade ciclomática: **≤ 10 por função**
- Conformidade PEP 8: **100%**
- Type hints: **100% em funções públicas**
- Docstrings: **100% em classes/funções públicas**

**Performance:**
- Detecção de ciclos: < 100ms para 100 histórias
- Ordenação de backlog: < 500ms para 100 histórias
- Cálculo de cronograma completo: < 2s para 100 histórias
- Edição inline na UI: < 100ms

## Entidades Principais

### Story (História)
```python
@dataclass
class Story:
    id: str                      # Ex: "S1", "A3" (primeira letra feature + número)
    feature: str                 # Agrupamento funcional
    name: str                    # Nome descritivo
    story_point: StoryPoint      # 3, 5, 8 ou 13
    status: StoryStatus          # BACKLOG, EXECUÇÃO, TESTES, CONCLUÍDO, IMPEDIDO
    priority: int                # Ordem de prioridade (menor = mais prioritário)
    developer_id: Optional[str]  # Desenvolvedor alocado
    dependencies: list[str]      # IDs de histórias das quais depende
    start_date: Optional[date]   # Data início (calculada)
    end_date: Optional[date]     # Data fim (calculada)
    duration: Optional[int]      # Duração em dias úteis (calculada)
```

### Developer (Desenvolvedor)
```python
@dataclass
class Developer:
    id: str    # Ex: "GA" (2 primeiras letras do nome)
    name: str  # Nome completo
```

### Configuration (Configuração Global)
```python
@dataclass
class Configuration:
    story_points_per_sprint: int = 21  # Velocidade do time
    workdays_per_sprint: int = 15      # Dias úteis por sprint

    @property
    def velocity_per_day(self) -> float:
        """Calcula SP por dia útil"""
        return self.story_points_per_sprint / self.workdays_per_sprint
```

## Casos de Uso Principais

### Fluxo de Trabalho Típico
1. **Importar histórias** do Excel (`ImportFromExcelUseCase`)
2. **Cadastrar desenvolvedores** (`CreateDeveloperUseCase`)
3. **Adicionar dependências** entre histórias (`AddDependencyUseCase`)
4. **Calcular cronograma** - ordena, aloca devs, calcula datas (`CalculateScheduleUseCase`)
5. **Exportar para Excel** (`ExportToExcelUseCase`)

### Recálculo Automático
Ao editar Story Point, prioridade ou desenvolvedor, disparar automaticamente:
```python
CalculateScheduleUseCase.execute()
```

## Pontos de Atenção

### ⚠️ Testes Primeiro (TDD)
Especialmente para algoritmos complexos (detecção de ciclos, ordenação topológica). Escreva o teste ANTES da implementação.

### ⚠️ Não Pular Camadas
- Presentation **NUNCA** chama Domain diretamente
- Sempre passar por Application (use cases)

### ⚠️ Domínio Puro
- Nenhuma importação de frameworks em `domain/`
- Sem SQLAlchemy, PyQt, openpyxl no domínio
- Apenas Python standard library e tipos básicos

### ⚠️ Performance
- Algoritmos de grafo devem ser otimizados (DFS, Topological Sort)
- Evitar recálculos desnecessários (implementar dirty checking)
- Testar com 100 histórias regularmente

## Estrutura de Arquivos Excel

### Import (3 colunas obrigatórias)
```
Feature | Nome               | StoryPoint
--------|-------------------|------------
Login   | Implementar tela  | 5
Login   | Validar credenc.  | 3
```

### Export (11 colunas)
```
Prioridade | ID | Feature | Nome | Status | Desenvolvedor | Dependências | SP | Início | Fim | Duração
```

## Referências

- **Requisitos Detalhados:** [requisitos.md](requisitos.md)
- **Plano Fase 1:** [plano_fase1.md](plano_fase1.md) (ATUAL)
- **Plano Completo:** [plano_implementacao.md](plano_implementacao.md)
