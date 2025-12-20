# PLANO DE EXECUÇÃO - FASE 2: Camada de Aplicação

## 📋 VISÃO GERAL

### Objetivo da Fase
Implementar a **camada de aplicação** do sistema seguindo os princípios de Clean Architecture, criando todos os casos de uso que orquestram a lógica de domínio e definem as interfaces (ports) para comunicação com a infraestrutura.

### Contexto
A Fase 2 conecta a camada de domínio (implementada na Fase 1) com as camadas externas (infraestrutura e apresentação). Esta camada é responsável por:
- Definir os contratos (interfaces/ports) que a infraestrutura deve implementar
- Implementar os casos de uso que orquestram as regras de negócio
- Facilitar a transferência de dados entre camadas usando DTOs
- Garantir que a lógica de aplicação seja independente de frameworks e infraestrutura

### Duração Estimada
**2 semanas** (10 dias úteis)

### Story Points Totais
**26 SP**

### Dependências
- ✅ Fase 1 completa: Camada de domínio implementada e testada
  - Entidades: Story, Developer, Configuration
  - Value Objects: StoryPoint, StoryStatus
  - Serviços: CycleDetector, BacklogSorter, ScheduleCalculator
  - Exceções de domínio
  - Cobertura de testes > 90%

---

## 🎯 OBJETIVOS DETALHADOS

### Objetivos Principais

1. **Definir Contratos Claros**
   - Criar interfaces (Abstract Base Classes) para todos os repositórios
   - Definir contratos para serviços externos (Excel)
   - Estabelecer a fronteira entre aplicação e infraestrutura
   - Garantir inversão de dependência (Dependency Inversion Principle)

2. **Implementar Casos de Uso Completos**
   - CRUD de Histórias (Create, Read, Update, Delete, List, Duplicate)
   - CRUD de Desenvolvedores
   - Gerenciamento de Dependências (Add, Remove)
   - Cálculo de Cronograma e Alocação
   - Import/Export de dados

3. **Estabelecer Camada de Transferência de Dados**
   - Criar DTOs para comunicação entre camadas
   - Implementar conversores Entity ↔ DTO
   - Garantir isolamento das entidades de domínio

4. **Garantir Qualidade e Testabilidade**
   - Testes de integração narrow para cada caso de uso
   - Cobertura > 85% na camada de aplicação
   - Documentação completa de cada caso de uso

### Objetivos Secundários

- Preparar estrutura para testes com mocks de repositórios
- Documentar fluxos de dados entre camadas
- Criar exemplos de uso dos casos de uso para a camada de apresentação

---

## 📂 ESTRUTURA DE ARQUIVOS

### Estrutura da Camada de Aplicação

```
backlog_manager/
├── application/
│   ├── __init__.py
│   │
│   ├── interfaces/                      # Ports (Contratos)
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── story_repository.py      # Interface para persistência de histórias
│   │   │   ├── developer_repository.py  # Interface para persistência de devs
│   │   │   └── configuration_repository.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── excel_service.py         # Interface para import/export Excel
│   │
│   ├── dto/                             # Data Transfer Objects
│   │   ├── __init__.py
│   │   ├── story_dto.py                 # DTO para Story
│   │   ├── developer_dto.py             # DTO para Developer
│   │   ├── configuration_dto.py         # DTO para Configuration
│   │   ├── backlog_dto.py               # DTO para backlog completo
│   │   └── converters.py                # Conversores Entity ↔ DTO
│   │
│   └── use_cases/                       # Casos de Uso
│       ├── __init__.py
│       │
│       ├── story/
│       │   ├── __init__.py
│       │   ├── create_story.py          # UC: Criar história
│       │   ├── update_story.py          # UC: Atualizar história
│       │   ├── delete_story.py          # UC: Deletar história
│       │   ├── list_stories.py          # UC: Listar histórias
│       │   ├── get_story.py             # UC: Buscar história por ID
│       │   └── duplicate_story.py       # UC: Duplicar história
│       │
│       ├── developer/
│       │   ├── __init__.py
│       │   ├── create_developer.py      # UC: Criar desenvolvedor
│       │   ├── update_developer.py      # UC: Atualizar desenvolvedor
│       │   ├── delete_developer.py      # UC: Deletar desenvolvedor
│       │   ├── list_developers.py       # UC: Listar desenvolvedores
│       │   └── get_developer.py         # UC: Buscar desenvolvedor
│       │
│       ├── dependency/
│       │   ├── __init__.py
│       │   ├── add_dependency.py        # UC: Adicionar dependência
│       │   └── remove_dependency.py     # UC: Remover dependência
│       │
│       ├── schedule/
│       │   ├── __init__.py
│       │   ├── calculate_schedule.py    # UC: Calcular cronograma completo
│       │   ├── allocate_developers.py   # UC: Alocar devs (round-robin)
│       │   └── change_priority.py       # UC: Mudar prioridade de história
│       │
│       ├── import_export/
│       │   ├── __init__.py
│       │   ├── import_from_excel.py     # UC: Importar do Excel
│       │   └── export_to_excel.py       # UC: Exportar para Excel
│       │
│       └── configuration/
│           ├── __init__.py
│           ├── get_configuration.py     # UC: Buscar configuração
│           └── update_configuration.py  # UC: Atualizar configuração
```

---

## 📝 TAREFAS DETALHADAS

### 2.1 Definir Interfaces (Ports) - 3 SP

**Objetivo:** Estabelecer os contratos que a camada de infraestrutura deve implementar.

#### 2.1.1 Interface StoryRepository
- **Arquivo:** `application/interfaces/repositories/story_repository.py`
- **Descrição:** Define contrato para persistência de histórias
- **Métodos:**
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Optional
  from backlog_manager.domain.entities.story import Story
  
  class StoryRepository(ABC):
      @abstractmethod
      def save(self, story: Story) -> None:
          """Salva ou atualiza uma história"""
          pass
      
      @abstractmethod
      def find_by_id(self, story_id: str) -> Optional[Story]:
          """Busca história por ID"""
          pass
      
      @abstractmethod
      def find_all(self) -> List[Story]:
          """Retorna todas as histórias"""
          pass
      
      @abstractmethod
      def delete(self, story_id: str) -> None:
          """Remove uma história"""
          pass
      
      @abstractmethod
      def exists(self, story_id: str) -> bool:
          """Verifica se história existe"""
          pass
  ```

#### 2.1.2 Interface DeveloperRepository
- **Arquivo:** `application/interfaces/repositories/developer_repository.py`
- **Descrição:** Define contrato para persistência de desenvolvedores
- **Métodos:**
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Optional
  from backlog_manager.domain.entities.developer import Developer
  
  class DeveloperRepository(ABC):
      @abstractmethod
      def save(self, developer: Developer) -> None:
          """Salva ou atualiza um desenvolvedor"""
          pass
      
      @abstractmethod
      def find_by_id(self, developer_id: str) -> Optional[Developer]:
          """Busca desenvolvedor por ID"""
          pass
      
      @abstractmethod
      def find_all(self) -> List[Developer]:
          """Retorna todos os desenvolvedores"""
          pass
      
      @abstractmethod
      def delete(self, developer_id: str) -> None:
          """Remove um desenvolvedor"""
          pass
      
      @abstractmethod
      def exists(self, developer_id: str) -> bool:
          """Verifica se desenvolvedor existe"""
          pass
      
      @abstractmethod
      def id_is_available(self, developer_id: str) -> bool:
          """Verifica se ID está disponível"""
          pass
  ```

#### 2.1.3 Interface ConfigurationRepository
- **Arquivo:** `application/interfaces/repositories/configuration_repository.py`
- **Descrição:** Define contrato para persistência de configuração (singleton)
- **Métodos:**
  ```python
  from abc import ABC, abstractmethod
  from backlog_manager.domain.entities.configuration import Configuration
  
  class ConfigurationRepository(ABC):
      @abstractmethod
      def get(self) -> Configuration:
          """Retorna configuração única do sistema"""
          pass
      
      @abstractmethod
      def save(self, configuration: Configuration) -> None:
          """Salva configuração"""
          pass
  ```

#### 2.1.4 Interface ExcelService
- **Arquivo:** `application/interfaces/services/excel_service.py`
- **Descrição:** Define contrato para serviço de import/export Excel
- **Métodos:**
  ```python
  from abc import ABC, abstractmethod
  from typing import List
  from backlog_manager.application.dto.story_dto import StoryDTO
  
  class ExcelService(ABC):
      @abstractmethod
      def import_stories(self, filepath: str) -> List[StoryDTO]:
          """Importa histórias de arquivo Excel"""
          pass
      
      @abstractmethod
      def export_backlog(self, filepath: str, stories: List[StoryDTO]) -> None:
          """Exporta backlog para arquivo Excel"""
          pass
  ```

#### Testes
- **Arquivo:** `tests/unit/application/interfaces/test_interfaces.py`
- **Validações:**
  - Verificar que todas as interfaces são ABC
  - Verificar que métodos são abstract
  - Testar que não é possível instanciar diretamente

**Critérios de Aceitação:**
- [ ] Todas as interfaces definidas como ABC
- [ ] Métodos decorados com @abstractmethod
- [ ] Docstrings completas em português
- [ ] Type hints corretos
- [ ] Testes de validação das interfaces

---

### 2.2 DTOs (Data Transfer Objects) - 2 SP

**Objetivo:** Criar objetos simples para transferência de dados entre camadas.

#### 2.2.1 StoryDTO
- **Arquivo:** `application/dto/story_dto.py`
- **Descrição:** DTO para transferir dados de Story
- **Estrutura:**
  ```python
  from dataclasses import dataclass
  from typing import Optional, List
  from datetime import date
  
  @dataclass
  class StoryDTO:
      id: str
      feature: str
      name: str
      status: str
      priority: int
      developer_id: Optional[str]
      dependencies: List[str]
      story_point: int
      start_date: Optional[date]
      end_date: Optional[date]
      duration: Optional[int]
  ```

#### 2.2.2 DeveloperDTO
- **Arquivo:** `application/dto/developer_dto.py`
- **Estrutura:**
  ```python
  from dataclasses import dataclass
  
  @dataclass
  class DeveloperDTO:
      id: str
      name: str
  ```

#### 2.2.3 ConfigurationDTO
- **Arquivo:** `application/dto/configuration_dto.py`
- **Estrutura:**
  ```python
  from dataclasses import dataclass
  
  @dataclass
  class ConfigurationDTO:
      story_points_per_sprint: int
      workdays_per_sprint: int
      velocity_per_day: float
  ```

#### 2.2.4 BacklogDTO
- **Arquivo:** `application/dto/backlog_dto.py`
- **Descrição:** DTO para backlog completo com metadados
- **Estrutura:**
  ```python
  from dataclasses import dataclass
  from typing import List
  
  @dataclass
  class BacklogDTO:
      stories: List[StoryDTO]
      total_count: int
      total_story_points: int
      estimated_duration_days: int
  ```

#### 2.2.5 Conversores
- **Arquivo:** `application/dto/converters.py`
- **Descrição:** Funções para converter Entity ↔ DTO
- **Funções:**
  ```python
  def story_to_dto(story: Story) -> StoryDTO:
      """Converte Story entity para StoryDTO"""
      pass
  
  def dto_to_story(dto: StoryDTO) -> Story:
      """Converte StoryDTO para Story entity"""
      pass
  
  def developer_to_dto(developer: Developer) -> DeveloperDTO:
      """Converte Developer entity para DeveloperDTO"""
      pass
  
  def dto_to_developer(dto: DeveloperDTO) -> Developer:
      """Converte DeveloperDTO para Developer entity"""
      pass
  
  def configuration_to_dto(config: Configuration) -> ConfigurationDTO:
      """Converte Configuration entity para ConfigurationDTO"""
      pass
  
  def dto_to_configuration(dto: ConfigurationDTO) -> Configuration:
      """Converte ConfigurationDTO para Configuration entity"""
      pass
  ```

#### Testes
- **Arquivo:** `tests/unit/application/dto/test_converters.py`
- **Validações:**
  - Conversão Story → DTO → Story preserva dados
  - Conversão Developer → DTO → Developer preserva dados
  - Conversão Configuration → DTO → Configuration preserva dados
  - Listas de dependências são copiadas corretamente
  - Campos opcionais (None) são tratados corretamente

**Critérios de Aceitação:**
- [ ] DTOs implementados como dataclasses
- [ ] Conversores bidirecionais funcionando
- [ ] Testes de round-trip (Entity → DTO → Entity)
- [ ] Type hints completos
- [ ] Documentação clara

---

### 2.3 Casos de Uso de História - 8 SP

**Objetivo:** Implementar todos os casos de uso relacionados a histórias.

#### 2.3.1 CreateStoryUseCase
- **Arquivo:** `application/use_cases/story/create_story.py`
- **Descrição:** Cria nova história no sistema
- **Responsabilidades:**
  1. Gerar ID automático sequencial (US-001, US-002, etc)
  2. Validar dados de entrada
  3. Criar entidade Story
  4. Definir prioridade inicial (última posição)
  5. Persistir via repository
  6. Retornar DTO da história criada
- **Estrutura:**
  ```python
  from backlog_manager.application.interfaces.repositories.story_repository import StoryRepository
  from backlog_manager.application.dto.story_dto import StoryDTO
  from backlog_manager.domain.entities.story import Story
  
  class CreateStoryUseCase:
      def __init__(self, story_repository: StoryRepository):
          self._story_repository = story_repository
      
      def execute(self, story_data: dict) -> StoryDTO:
          """
          Cria nova história.
          
          Args:
              story_data: Dicionário com dados da história
                  - feature: str
                  - name: str
                  - story_point: int (3, 5, 8 ou 13)
                  - dependencies: List[str] (opcional)
          
          Returns:
              StoryDTO com dados da história criada
          
          Raises:
              InvalidStoryPointException: Se story point inválido
              ValidationException: Se dados inválidos
          """
          # 1. Gerar próximo ID
          # 2. Determinar prioridade (última)
          # 3. Criar entidade Story
          # 4. Persistir
          # 5. Retornar DTO
          pass
  ```
- **Testes:**
  - Criar história válida
  - ID gerado corretamente (US-001, US-002, etc)
  - Prioridade definida como última
  - Story point inválido gera exceção
  - Dados obrigatórios ausentes geram exceção

#### 2.3.2 UpdateStoryUseCase
- **Arquivo:** `application/use_cases/story/update_story.py`
- **Descrição:** Atualiza história existente
- **Responsabilidades:**
  1. Buscar história existente
  2. Validar novos dados
  3. Detectar mudanças que requerem recálculo (SP, prioridade, desenvolvedor)
  4. Atualizar entidade
  5. Persistir
  6. Retornar DTO e flag de recálculo necessário
- **Estrutura:**
  ```python
  from typing import Tuple
  
  class UpdateStoryUseCase:
      def __init__(self, story_repository: StoryRepository):
          self._story_repository = story_repository
      
      def execute(self, story_id: str, updates: dict) -> Tuple[StoryDTO, bool]:
          """
          Atualiza história existente.
          
          Args:
              story_id: ID da história
              updates: Dicionário com campos a atualizar
          
          Returns:
              Tupla (StoryDTO atualizado, requer_recalculo: bool)
          
          Raises:
              StoryNotFoundException: Se história não existe
              ValidationException: Se dados inválidos
          """
          # 1. Buscar história
          # 2. Verificar mudanças críticas
          # 3. Atualizar campos
          # 4. Persistir
          # 5. Retornar (DTO, flag_recalculo)
          pass
  ```
- **Testes:**
  - Atualizar campos simples (feature, name)
  - Atualizar SP dispara flag de recálculo
  - Atualizar desenvolvedor dispara flag de recálculo
  - História inexistente gera exceção
  - Validações de dados

#### 2.3.3 DeleteStoryUseCase
- **Arquivo:** `application/use_cases/story/delete_story.py`
- **Descrição:** Remove história do sistema
- **Responsabilidades:**
  1. Verificar se história existe
  2. Buscar histórias que dependem desta
  3. Remover referências de dependências
  4. Deletar história
- **Estrutura:**
  ```python
  class DeleteStoryUseCase:
      def __init__(self, story_repository: StoryRepository):
          self._story_repository = story_repository
      
      def execute(self, story_id: str) -> None:
          """
          Remove história do sistema.
          
          Args:
              story_id: ID da história a deletar
          
          Raises:
              StoryNotFoundException: Se história não existe
          """
          # 1. Verificar existência
          # 2. Remover de dependências de outras histórias
          # 3. Deletar
          pass
  ```
- **Testes:**
  - Deletar história sem dependências
  - Deletar história que é dependência de outra
  - História inexistente gera exceção

#### 2.3.4 ListStoriesUseCase
- **Arquivo:** `application/use_cases/story/list_stories.py`
- **Descrição:** Lista todas as histórias
- **Responsabilidades:**
  1. Buscar todas histórias do repository
  2. Converter para DTOs
  3. Retornar lista ordenada por prioridade
- **Estrutura:**
  ```python
  class ListStoriesUseCase:
      def __init__(self, story_repository: StoryRepository):
          self._story_repository = story_repository
      
      def execute(self) -> List[StoryDTO]:
          """
          Retorna todas as histórias ordenadas por prioridade.
          
          Returns:
              Lista de StoryDTO ordenada por prioridade
          """
          # 1. Buscar todas
          # 2. Ordenar por prioridade
          # 3. Converter para DTOs
          pass
  ```
- **Testes:**
  - Listar histórias em ordem de prioridade
  - Lista vazia quando não há histórias
  - Conversão correta para DTOs

#### 2.3.5 GetStoryUseCase
- **Arquivo:** `application/use_cases/story/get_story.py`
- **Descrição:** Busca história específica por ID
- **Estrutura:**
  ```python
  class GetStoryUseCase:
      def __init__(self, story_repository: StoryRepository):
          self._story_repository = story_repository
      
      def execute(self, story_id: str) -> StoryDTO:
          """
          Busca história por ID.
          
          Args:
              story_id: ID da história
          
          Returns:
              StoryDTO da história encontrada
          
          Raises:
              StoryNotFoundException: Se história não existe
          """
          pass
  ```
- **Testes:**
  - Buscar história existente
  - Buscar história inexistente gera exceção

#### 2.3.6 DuplicateStoryUseCase
- **Arquivo:** `application/use_cases/story/duplicate_story.py`
- **Descrição:** Duplica história existente com novo ID
- **Responsabilidades:**
  1. Buscar história original
  2. Copiar dados (exceto ID)
  3. Gerar novo ID
  4. Resetar campos (status → BACKLOG, desenvolvedor → None)
  5. Limpar datas e duração
  6. Persistir nova história
- **Estrutura:**
  ```python
  class DuplicateStoryUseCase:
      def __init__(self, story_repository: StoryRepository):
          self._story_repository = story_repository
      
      def execute(self, story_id: str) -> StoryDTO:
          """
          Duplica história existente.
          
          Args:
              story_id: ID da história a duplicar
          
          Returns:
              StoryDTO da nova história criada
          
          Raises:
              StoryNotFoundException: Se história original não existe
          """
          # 1. Buscar original
          # 2. Copiar dados
          # 3. Gerar novo ID
          # 4. Resetar campos
          # 5. Persistir
          pass
  ```
- **Testes:**
  - Duplicar história válida
  - Novo ID gerado corretamente
  - Status resetado para BACKLOG
  - Desenvolvedor removido
  - Datas e duração zeradas

**Critérios de Aceitação:**
- [ ] Todos os 6 casos de uso implementados
- [ ] Injeção de dependências via construtor
- [ ] Métodos execute() bem definidos
- [ ] Tratamento de exceções
- [ ] Testes de integração narrow para cada caso de uso
- [ ] Docstrings completas

---

### 2.4 Casos de Uso de Desenvolvedor - 3 SP

**Objetivo:** Implementar CRUD completo de desenvolvedores.

#### 2.4.1 CreateDeveloperUseCase
- **Arquivo:** `application/use_cases/developer/create_developer.py`
- **Responsabilidades:**
  1. Validar nome do desenvolvedor
  2. Gerar ID automático (2 primeiras letras maiúsculas do nome)
  3. Se ID já existe, adicionar número sequencial (ex: JO → JO2)
  4. Criar entidade Developer
  5. Persistir
- **Estrutura:**
  ```python
  class CreateDeveloperUseCase:
      def __init__(self, developer_repository: DeveloperRepository):
          self._developer_repository = developer_repository
      
      def execute(self, name: str) -> DeveloperDTO:
          """
          Cria novo desenvolvedor.
          
          Args:
              name: Nome do desenvolvedor (min 2 caracteres)
          
          Returns:
              DeveloperDTO criado
          
          Raises:
              ValidationException: Se nome inválido
          """
          # 1. Validar nome
          # 2. Gerar ID
          # 3. Resolver conflitos (JO → JO2)
          # 4. Criar entidade
          # 5. Persistir
          pass
  ```
- **Testes:**
  - Criar desenvolvedor com nome válido
  - ID gerado corretamente (2 letras)
  - Conflito de ID resolvido (JO → JO2 → JO3)
  - Nome muito curto gera exceção

#### 2.4.2 UpdateDeveloperUseCase
- **Arquivo:** `application/use_cases/developer/update_developer.py`
- **Descrição:** Atualiza nome de desenvolvedor
- **Testes:**
  - Atualizar nome válido
  - Desenvolvedor inexistente gera exceção

#### 2.4.3 DeleteDeveloperUseCase
- **Arquivo:** `application/use_cases/developer/delete_developer.py`
- **Responsabilidades:**
  1. Verificar se desenvolvedor existe
  2. Buscar histórias alocadas a este desenvolvedor
  3. Remover alocação (developer_id → None)
  4. Deletar desenvolvedor
- **Testes:**
  - Deletar desenvolvedor sem histórias
  - Deletar desenvolvedor com histórias alocadas
  - Histórias perdem alocação após deleção

#### 2.4.4 ListDevelopersUseCase
- **Arquivo:** `application/use_cases/developer/list_developers.py`
- **Testes:**
  - Listar desenvolvedores ordenados por nome
  - Lista vazia quando não há desenvolvedores

#### 2.4.5 GetDeveloperUseCase
- **Arquivo:** `application/use_cases/developer/get_developer.py`
- **Testes:**
  - Buscar desenvolvedor existente
  - Desenvolvedor inexistente gera exceção

**Critérios de Aceitação:**
- [ ] 5 casos de uso implementados
- [ ] Geração de ID automático funcionando
- [ ] Remoção de alocações ao deletar
- [ ] Testes completos

---

### 2.5 Casos de Uso de Dependências - 3 SP

**Objetivo:** Gerenciar dependências entre histórias com validação de ciclos.

#### 2.5.1 AddDependencyUseCase
- **Arquivo:** `application/use_cases/dependency/add_dependency.py`
- **Descrição:** Adiciona dependência entre histórias validando ciclos
- **Responsabilidades:**
  1. Validar que ambas histórias existem
  2. Buscar todas as dependências atuais
  3. Simular adição da nova dependência
  4. Usar CycleDetector para validar ciclo
  5. Se válido, adicionar dependência
  6. Se inválido, retornar erro com caminho do ciclo
- **Estrutura:**
  ```python
  from backlog_manager.domain.services.cycle_detector import CycleDetector
  
  class AddDependencyUseCase:
      def __init__(
          self,
          story_repository: StoryRepository,
          cycle_detector: CycleDetector
      ):
          self._story_repository = story_repository
          self._cycle_detector = cycle_detector
      
      def execute(self, story_id: str, depends_on_id: str) -> None:
          """
          Adiciona dependência entre histórias.
          
          Args:
              story_id: ID da história dependente
              depends_on_id: ID da história da qual depende
          
          Raises:
              StoryNotFoundException: Se alguma história não existe
              CyclicDependencyException: Se criaria ciclo (com caminho)
          """
          # 1. Validar existência das histórias
          # 2. Buscar todas dependências
          # 3. Simular adição
          # 4. Detectar ciclo
          # 5. Se válido, adicionar
          pass
  ```
- **Testes:**
  - Adicionar dependência válida
  - Ciclo direto (A → B, tentar B → A)
  - Ciclo indireto (A → B → C, tentar C → A)
  - História inexistente gera exceção
  - Mensagem de erro inclui caminho do ciclo

#### 2.5.2 RemoveDependencyUseCase
- **Arquivo:** `application/use_cases/dependency/remove_dependency.py`
- **Descrição:** Remove dependência entre histórias
- **Testes:**
  - Remover dependência existente
  - Remover dependência inexistente (não gera erro)
  - História inexistente gera exceção

**Critérios de Aceitação:**
- [ ] Detecção de ciclos funcionando
- [ ] Mensagens de erro informativas
- [ ] Testes com cenários complexos de dependências
- [ ] Integração com CycleDetector da camada de domínio

---

### 2.6 Casos de Uso de Cronograma - 5 SP

**Objetivo:** Implementar cálculo de cronograma e alocação de desenvolvedores.

#### 2.6.1 CalculateScheduleUseCase
- **Arquivo:** `application/use_cases/schedule/calculate_schedule.py`
- **Descrição:** Calcula cronograma completo do backlog
- **Responsabilidades:**
  1. Buscar todas as histórias
  2. Buscar configuração
  3. Ordenar backlog usando BacklogSorter
  4. Calcular datas usando ScheduleCalculator
  5. Persistir histórias atualizadas
  6. Retornar BacklogDTO com cronograma
- **Estrutura:**
  ```python
  from backlog_manager.domain.services.backlog_sorter import BacklogSorter
  from backlog_manager.domain.services.schedule_calculator import ScheduleCalculator
  
  class CalculateScheduleUseCase:
      def __init__(
          self,
          story_repository: StoryRepository,
          configuration_repository: ConfigurationRepository,
          backlog_sorter: BacklogSorter,
          schedule_calculator: ScheduleCalculator
      ):
          self._story_repository = story_repository
          self._configuration_repository = configuration_repository
          self._backlog_sorter = backlog_sorter
          self._schedule_calculator = schedule_calculator
      
      def execute(self) -> BacklogDTO:
          """
          Calcula cronograma completo do backlog.
          
          Returns:
              BacklogDTO com histórias ordenadas e cronograma calculado
          
          Raises:
              CyclicDependencyException: Se houver ciclo nas dependências
          """
          # 1. Buscar histórias e configuração
          # 2. Ordenar backlog
          # 3. Calcular cronograma
          # 4. Persistir atualizações
          # 5. Retornar BacklogDTO
          pass
  ```
- **Testes:**
  - Calcular cronograma com histórias simples
  - Calcular com dependências
  - Calcular com múltiplos desenvolvedores
  - Verificar persistência das datas
  - Performance < 2s para 100 histórias

#### 2.6.2 AllocateDevelopersUseCase
- **Arquivo:** `application/use_cases/schedule/allocate_developers.py`
- **Descrição:** Aloca desenvolvedores em histórias usando round-robin
- **Responsabilidades:**
  1. Buscar histórias não alocadas (developer_id = None)
  2. Buscar desenvolvedores disponíveis
  3. Distribuir histórias usando round-robin
  4. Persistir alocações
- **Estrutura:**
  ```python
  class AllocateDevelopersUseCase:
      def __init__(
          self,
          story_repository: StoryRepository,
          developer_repository: DeveloperRepository
      ):
          self._story_repository = story_repository
          self._developer_repository = developer_repository
      
      def execute(self) -> int:
          """
          Aloca desenvolvedores nas histórias não alocadas.
          
          Returns:
              Número de histórias alocadas
          
          Raises:
              NoDevelopersAvailableException: Se não há desenvolvedores
          """
          # 1. Buscar histórias sem desenvolvedor
          # 2. Buscar desenvolvedores
          # 3. Distribuir round-robin
          # 4. Persistir
          pass
  ```
- **Testes:**
  - Alocar com 1 desenvolvedor
  - Alocar com múltiplos desenvolvedores (round-robin)
  - Sem desenvolvedores gera exceção
  - Histórias já alocadas não são alteradas

#### 2.6.3 ChangePriorityUseCase
- **Arquivo:** `application/use_cases/schedule/change_priority.py`
- **Descrição:** Altera prioridade de história (mover para cima/baixo)
- **Responsabilidades:**
  1. Buscar história
  2. Validar movimento (não ultrapassar limites)
  3. Trocar prioridades com história adjacente
  4. Persistir mudanças
  5. Retornar flag indicando necessidade de recálculo
- **Estrutura:**
  ```python
  from enum import Enum
  
  class Direction(Enum):
      UP = "up"
      DOWN = "down"
  
  class ChangePriorityUseCase:
      def __init__(self, story_repository: StoryRepository):
          self._story_repository = story_repository
      
      def execute(self, story_id: str, direction: Direction) -> bool:
          """
          Altera prioridade de história.
          
          Args:
              story_id: ID da história
              direction: Direction.UP ou Direction.DOWN
          
          Returns:
              True se necessário recalcular cronograma
          
          Raises:
              StoryNotFoundException: Se história não existe
              InvalidMoveException: Se movimento inválido (já é primeira/última)
          """
          # 1. Buscar história e lista completa
          # 2. Validar movimento
          # 3. Trocar prioridades
          # 4. Persistir
          pass
  ```
- **Testes:**
  - Mover história para cima
  - Mover história para baixo
  - Não pode mover primeira para cima
  - Não pode mover última para baixo
  - Prioridades trocadas corretamente

**Critérios de Aceitação:**
- [ ] Cálculo de cronograma completo funcionando
- [ ] Alocação round-robin correta
- [ ] Mudança de prioridade com validações
- [ ] Testes de integração com serviços de domínio
- [ ] Performance adequada

---

### 2.7 Casos de Uso de Import/Export - 2 SP

**Objetivo:** Implementar importação e exportação de dados em Excel.

#### 2.7.1 ImportFromExcelUseCase
- **Arquivo:** `application/use_cases/import_export/import_from_excel.py`
- **Descrição:** Importa histórias de arquivo Excel
- **Responsabilidades:**
  1. Validar arquivo via ExcelService
  2. Converter DTOs para entidades
  3. Validar dados de negócio
  4. Criar histórias em lote
  5. Retornar relatório de sucesso/falhas
- **Estrutura:**
  ```python
  from dataclasses import dataclass
  from typing import List
  
  @dataclass
  class ImportResult:
      total: int
      success: int
      failures: List[str]  # Mensagens de erro por linha
  
  class ImportFromExcelUseCase:
      def __init__(
          self,
          story_repository: StoryRepository,
          excel_service: ExcelService
      ):
          self._story_repository = story_repository
          self._excel_service = excel_service
      
      def execute(self, filepath: str) -> ImportResult:
          """
          Importa histórias de arquivo Excel.
          
          Args:
              filepath: Caminho do arquivo Excel
          
          Returns:
              ImportResult com estatísticas da importação
          
          Raises:
              FileNotFoundException: Se arquivo não existe
              InvalidExcelFormatException: Se formato inválido
          """
          # 1. Importar DTOs via ExcelService
          # 2. Validar cada história
          # 3. Criar entidades válidas
          # 4. Persistir
          # 5. Retornar relatório
          pass
  ```
- **Testes:**
  - Importar arquivo válido
  - Importar com linhas inválidas (parcial)
  - Arquivo inexistente gera exceção
  - Formato inválido gera exceção
  - Relatório correto

#### 2.7.2 ExportToExcelUseCase
- **Arquivo:** `application/use_cases/import_export/export_to_excel.py`
- **Descrição:** Exporta backlog ordenado para Excel
- **Responsabilidades:**
  1. Buscar todas histórias ordenadas
  2. Converter para DTOs
  3. Exportar via ExcelService
- **Estrutura:**
  ```python
  class ExportToExcelUseCase:
      def __init__(
          self,
          story_repository: StoryRepository,
          excel_service: ExcelService
      ):
          self._story_repository = story_repository
          self._excel_service = excel_service
      
      def execute(self, filepath: str) -> None:
          """
          Exporta backlog para arquivo Excel.
          
          Args:
              filepath: Caminho do arquivo de destino
          
          Raises:
              PermissionException: Se sem permissão de escrita
          """
          # 1. Buscar histórias ordenadas
          # 2. Converter para DTOs
          # 3. Exportar via ExcelService
          pass
  ```
- **Testes:**
  - Exportar backlog completo
  - Exportar backlog vazio
  - Sem permissão de escrita gera exceção

**Critérios de Aceitação:**
- [ ] Import com validação e relatório
- [ ] Export com formatação
- [ ] Tratamento de erros
- [ ] Testes com arquivos reais

---

### 2.8 Casos de Uso de Configuração - 1 SP

**Objetivo:** Gerenciar configuração do sistema.

#### 2.8.1 GetConfigurationUseCase
- **Arquivo:** `application/use_cases/configuration/get_configuration.py`
- **Testes:**
  - Buscar configuração existente
  - Primeira execução retorna defaults

#### 2.8.2 UpdateConfigurationUseCase
- **Arquivo:** `application/use_cases/configuration/update_configuration.py`
- **Responsabilidades:**
  1. Validar novos valores
  2. Atualizar configuração
  3. Persistir
  4. Retornar flag de recálculo necessário
- **Testes:**
  - Atualizar velocidade dispara recálculo
  - Valores inválidos geram exceção

**Critérios de Aceitação:**
- [ ] Get e Update implementados
- [ ] Validações de valores
- [ ] Flag de recálculo

---

## ✅ CRITÉRIOS DE ACEITAÇÃO DA FASE 2

### Implementação
- [ ] Todas as interfaces (ports) definidas como ABC
- [ ] Todos os DTOs implementados como dataclasses
- [ ] Conversores Entity ↔ DTO funcionando
- [ ] 23 casos de uso implementados e funcionando:
  - 6 casos de uso de Story
  - 5 casos de uso de Developer
  - 2 casos de uso de Dependency
  - 3 casos de uso de Schedule
  - 2 casos de uso de Import/Export
  - 2 casos de uso de Configuration
  - 3 casos auxiliares (List/Get)

### Qualidade de Código
- [ ] Type hints completos em todos os arquivos
- [ ] Docstrings em português (padrão Google/NumPy)
- [ ] Seguindo PEP 8
- [ ] Sem warnings do linter
- [ ] Injeção de dependências via construtor

### Testes
- [ ] Cobertura > 85% na camada de aplicação
- [ ] Testes de integração narrow para cada caso de uso
- [ ] Mocks de repositórios funcionando
- [ ] Testes de cenários de erro
- [ ] Testes de validação de dados

### Documentação
- [ ] README atualizado com casos de uso
- [ ] Exemplos de uso de cada caso de uso
- [ ] Diagramas de fluxo (opcional)
- [ ] Comentários em código complexo

### Integração
- [ ] Casos de uso orquestrando domínio corretamente
- [ ] Serviços de domínio sendo utilizados
- [ ] Exceções de domínio propagadas adequadamente
- [ ] DTOs isolando domínio da infraestrutura

---

## 📊 ESTRATÉGIA DE TESTES

### Tipos de Testes na Fase 2

#### 1. Testes Unitários de DTOs
- **Foco:** Conversores Entity ↔ DTO
- **Ferramentas:** pytest
- **Cobertura:** 100%
- **Exemplo:**
  ```python
  def test_story_to_dto_conversion():
      # Arrange
      story = Story(...)
      
      # Act
      dto = story_to_dto(story)
      
      # Assert
      assert dto.id == story.id
      assert dto.feature == story.feature
      # ... todos os campos
  ```

#### 2. Testes de Integração Narrow de Casos de Uso
- **Foco:** Orquestração de lógica de domínio
- **Ferramentas:** pytest, mocks
- **Cobertura:** > 85%
- **Estratégia:** Usar mocks de repositórios
- **Exemplo:**
  ```python
  def test_create_story_use_case():
      # Arrange
      mock_repo = Mock(spec=StoryRepository)
      mock_repo.find_all.return_value = []
      use_case = CreateStoryUseCase(mock_repo)
      
      # Act
      result = use_case.execute({
          'feature': 'Login',
          'name': 'Login form',
          'story_point': 5
      })
      
      # Assert
      assert result.id == 'US-001'
      assert result.feature == 'Login'
      mock_repo.save.assert_called_once()
  ```

#### 3. Testes de Validação
- **Foco:** Validações de dados e regras de negócio
- **Cobertura:** Todos os cenários de erro
- **Exemplo:**
  ```python
  def test_add_dependency_detects_cycle():
      # Arrange
      story_a = Story(id='US-001', dependencies=['US-002'])
      story_b = Story(id='US-002', dependencies=[])
      mock_repo = Mock(spec=StoryRepository)
      mock_repo.find_by_id.side_effect = [story_b, story_a]
      mock_repo.find_all.return_value = [story_a, story_b]
      
      cycle_detector = CycleDetector()
      use_case = AddDependencyUseCase(mock_repo, cycle_detector)
      
      # Act & Assert
      with pytest.raises(CyclicDependencyException) as exc_info:
          use_case.execute('US-002', 'US-001')
      
      assert 'US-002 -> US-001 -> US-002' in str(exc_info.value)
  ```

### Fixtures e Dados de Teste
- **Arquivo:** `tests/fixtures/sample_data.py`
- **Conteúdo:** Factories para criar entidades e DTOs de teste
- **Exemplo:**
  ```python
  def create_sample_story(**kwargs):
      defaults = {
          'id': 'US-001',
          'feature': 'Test Feature',
          'name': 'Test Story',
          'status': StoryStatus.BACKLOG,
          'priority': 1,
          'story_point': StoryPoint(5)
      }
      defaults.update(kwargs)
      return Story(**defaults)
  ```

---

## 🔄 FLUXO DE TRABALHO

### Ordem de Implementação Recomendada

1. **Dia 1-2: Fundação**
   - 2.1: Definir interfaces (3 SP)
   - 2.2: Implementar DTOs (2 SP)
   - Validar estrutura com testes básicos

2. **Dia 3-5: Casos de Uso Core**
   - 2.3: Casos de uso de História (8 SP)
   - Implementar testes de integração narrow
   - Validar com mocks

3. **Dia 6-7: Casos de Uso Complementares**
   - 2.4: Casos de uso de Desenvolvedor (3 SP)
   - 2.8: Casos de uso de Configuração (1 SP)

4. **Dia 8: Dependências e Cronograma**
   - 2.5: Casos de uso de Dependências (3 SP)
   - 2.6.1-2.6.2: Alocação e Cálculo (4 SP)

5. **Dia 9: Import/Export e Finalização**
   - 2.7: Casos de uso de Import/Export (2 SP)
   - 2.6.3: Mudança de prioridade (1 SP)

6. **Dia 10: Revisão e Documentação**
   - Revisar todos os casos de uso
   - Garantir cobertura > 85%
   - Atualizar documentação
   - Preparar para Fase 3

### Checklist Diário

- [ ] Implementar casos de uso planejados
- [ ] Escrever testes de integração narrow
- [ ] Validar cobertura de código
- [ ] Executar todos os testes (Fase 1 + Fase 2)
- [ ] Revisar código (self-review)
- [ ] Atualizar documentação
- [ ] Commit com mensagem descritiva

---

## 📈 MÉTRICAS DE SUCESSO

### Cobertura de Testes
- **Meta:** > 85% na camada de aplicação
- **Comando:** `pytest --cov=backlog_manager/application tests/`
- **Critério:** Todas as linhas críticas cobertas

### Performance
- **CalculateScheduleUseCase:** < 2s para 100 histórias
- **Outros casos de uso:** < 500ms

### Qualidade de Código
- **Pylint:** Score > 9.0
- **Mypy:** 0 erros de type checking
- **Complexidade ciclomática:** < 10 por função

---

## 🎓 CONCEITOS IMPORTANTES

### Clean Architecture - Camada de Aplicação

1. **Dependency Rule (Regra de Dependência)**
   - Application depende apenas de Domain
   - Application define interfaces (ports)
   - Infrastructure implementa essas interfaces (adapters)

2. **Use Case Pattern**
   - Cada caso de uso é uma classe dedicada
   - Um único método público: `execute()`
   - Dependências injetadas via construtor
   - Orquestra entidades e serviços de domínio

3. **DTO Pattern**
   - Objetos simples para transferir dados
   - Não contém lógica de negócio
   - Isola camadas internas de camadas externas

4. **Port and Adapter Pattern**
   - Ports: Interfaces definidas na camada de aplicação
   - Adapters: Implementações na camada de infraestrutura
   - Inversão de dependência

### Princípios SOLID Aplicados

- **S - Single Responsibility:** Cada caso de uso tem uma única responsabilidade
- **O - Open/Closed:** Extensível via novos casos de uso
- **L - Liskov Substitution:** Repositórios podem ser substituídos (mock, in-memory, SQLite)
- **I - Interface Segregation:** Interfaces específicas e coesas
- **D - Dependency Inversion:** Aplicação depende de abstrações, não de implementações

---

## 📚 REFERÊNCIAS

### Arquitetura
- Clean Architecture (Robert C. Martin)
- Domain-Driven Design (Eric Evans)
- Patterns of Enterprise Application Architecture (Martin Fowler)

### Python
- PEP 8 - Style Guide for Python Code
- PEP 484 - Type Hints
- Python Testing with pytest (Brian Okken)

### Ferramentas
- pytest: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/
- unittest.mock: https://docs.python.org/3/library/unittest.mock.html

---

## ✨ PRÓXIMOS PASSOS

Após conclusão da Fase 2, seguir para:

**FASE 3: Camada de Infraestrutura (Persistência)**
- Implementar repositories SQLite
- Implementar Excel service
- Setup do banco de dados
- Migrations automáticas

---

## 📝 NOTAS FINAIS

### Boas Práticas

1. **Sempre use injeção de dependências:**
   ```python
   # ✅ Bom
   class CreateStoryUseCase:
       def __init__(self, story_repository: StoryRepository):
           self._story_repository = story_repository
   
   # ❌ Ruim
   class CreateStoryUseCase:
       def __init__(self):
           self._story_repository = SQLiteStoryRepository()
   ```

2. **Use type hints completos:**
   ```python
   def execute(self, story_id: str) -> StoryDTO:
       ...
   ```

3. **Docstrings sempre em português:**
   ```python
   def execute(self, story_id: str) -> StoryDTO:
       """
       Busca história por ID.
       
       Args:
           story_id: Identificador único da história
       
       Returns:
           StoryDTO com dados da história
       
       Raises:
           StoryNotFoundException: Se história não existe
       """
   ```

4. **Trate exceções adequadamente:**
   ```python
   story = self._story_repository.find_by_id(story_id)
   if story is None:
       raise StoryNotFoundException(f"História {story_id} não encontrada")
   ```

### Armadilhas Comuns

- ❌ Não instancie repositórios dentro de casos de uso
- ❌ Não coloque lógica de negócio em DTOs
- ❌ Não acesse banco de dados diretamente
- ❌ Não use imports absolutos da infraestrutura
- ❌ Não retorne entidades de domínio para camada de apresentação

---

**Versão:** 1.0  
**Data:** Dezembro de 2024  
**Autor:** Backlog Manager Development Team
