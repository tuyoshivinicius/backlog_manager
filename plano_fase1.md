# PLANO DE IMPLEMENTAÇÃO - FASE 1
**Projeto:** Sistema de Gestão de Backlog  
**Fase:** Fundação e Domínio (Base Sólida)  
**Versão:** 1.0  
**Data:** 20/12/2025

---

## VISÃO GERAL DA FASE 1

### Objetivos Estratégicos

Esta fase estabelece os **alicerces fundamentais** do sistema. Aqui criamos o coração da aplicação - a camada de domínio - que contém toda a lógica de negócio crítica, independente de frameworks, banco de dados ou interface gráfica.

**Objetivos Principais:**
1. ✅ Criar estrutura de projeto seguindo Clean Architecture rigorosamente
2. ✅ Implementar entidades de domínio puras (Story, Developer, Configuration)
3. ✅ Desenvolver algoritmos complexos core do sistema (detecção de ciclos, ordenação topológica, cronograma)
4. ✅ Estabelecer padrões de qualidade (TDD, >90% cobertura, PEP 8)
5. ✅ Criar fundação sólida para desenvolvimento das próximas fases

### Importância Crítica da Fase 1

Esta fase é a **mais importante do projeto**. Erros ou decisões ruins aqui terão impacto em cascata em todas as fases seguintes. Por outro lado, uma implementação sólida facilitará enormemente o desenvolvimento futuro.

**Por que começar pelo domínio?**
- **Independência:** Domínio não depende de frameworks, pode ser testado isoladamente
- **Foco no negócio:** Implementamos regras de negócio sem distrações de UI ou banco de dados
- **Testes confiáveis:** Testes de domínio são rápidos e determinísticos
- **Facilita mudanças:** Se precisar mudar UI ou banco, o domínio permanece intacto

### Métricas de Sucesso

| Métrica | Meta | Como Medir |
|---------|------|------------|
| Cobertura de Testes | ≥ 90% | `pytest --cov=backlog_manager/domain --cov-report=term` |
| Testes Passando | 100% | `pytest backlog_manager/domain -v` |
| Complexidade Ciclomática | ≤ 10/função | `radon cc backlog_manager/domain -a` |
| Conformidade PEP 8 | 100% | `flake8 backlog_manager/domain` |
| Performance - Detecção Ciclos | < 100ms para 100 histórias | Testes de benchmark |
| Performance - Ordenação | < 500ms para 100 histórias | Testes de benchmark |
| Docstrings | 100% classes/funções públicas | Revisão manual |

### Cronograma Detalhado

**Duração Total:** 2-3 semanas (10-15 dias úteis)  
**Story Points:** 34 SP  
**Velocidade Assumida:** ~12-15 SP/semana

```
Semana 1 (Dias 1-5):
├─ Dia 1-2: Setup do Projeto (3 SP)
├─ Dia 3-4: Entidades de Domínio (5 SP)
└─ Dia 5: Exceções de Domínio (2 SP)

Semana 2 (Dias 6-10):
├─ Dia 6-8: Serviço de Detecção de Ciclos (8 SP)
└─ Dia 9-10: Início Ordenação de Backlog (4 SP de 8 SP)

Semana 3 (Dias 11-15):
├─ Dia 11-12: Finalizar Ordenação de Backlog (4 SP restantes)
├─ Dia 13-15: Serviço de Cálculo de Cronograma (8 SP)
└─ Dia 15: Revisão final e ajustes
```

---

## TAREFA 1.1: SETUP DO PROJETO

**Story Points:** 3 SP  
**Duração Estimada:** 1-2 dias  
**Prioridade:** Crítica (bloqueia todas as outras)

### Objetivo

Criar a fundação técnica do projeto: estrutura de diretórios, ambiente virtual, dependências e configuração de ferramentas de qualidade.

### Pré-requisitos

- Python 3.11+ instalado
- Git instalado e configurado
- Editor de código (VS Code recomendado)
- Windows 10/11

### Subtarefas Detalhadas

#### 1.1.1 Criar Estrutura de Diretórios

**Comando:**
```bash
# No diretório raiz do projeto
mkdir -p backlog_manager/domain/entities
mkdir -p backlog_manager/domain/value_objects
mkdir -p backlog_manager/domain/services
mkdir -p backlog_manager/domain/exceptions
mkdir -p tests/unit/domain
mkdir -p config
```

**Estrutura esperada:**
```
backlog_manager/
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   └── __init__.py
│   ├── value_objects/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   └── exceptions/
│       └── __init__.py
├── tests/
│   └── unit/
│       └── domain/
│           └── __init__.py
├── config/
│   └── __init__.py
└── main.py
```

**Checklist:**
- [ ] Todos os diretórios criados
- [ ] Arquivos `__init__.py` em cada pacote Python
- [ ] Estrutura validada com `tree` ou `ls -R`

#### 1.1.2 Configurar Ambiente Virtual

**Comandos:**
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
.\venv\Scripts\activate

# Verificar Python correto
python --version  # Deve ser 3.11+
```

**Checklist:**
- [ ] Ambiente virtual criado
- [ ] Ambiente ativado (prompt deve mostrar `(venv)`)
- [ ] Python correto no ambiente

#### 1.1.3 Criar requirements.txt

**Arquivo: `requirements.txt`**
```txt
# Testing
pytest==7.4.3
pytest-cov==4.1.0

# Excel handling
openpyxl==3.1.2

# GUI (escolher um)
# PyQt6==6.6.0
PySide6==6.6.1

# Type checking
mypy==1.7.1
```

**Arquivo: `requirements-dev.txt`**
```txt
# Include production requirements
-r requirements.txt

# Code quality
black==23.12.0
flake8==6.1.0
pylint==3.0.3
isort==5.13.2
radon==6.0.1

# Packaging
PyInstaller==6.3.0

# Development tools
ipython==8.18.1
```

**Instalar dependências:**
```bash
pip install -r requirements-dev.txt
```

**Checklist:**
- [ ] Arquivos `requirements.txt` e `requirements-dev.txt` criados
- [ ] Todas as dependências instaladas sem erros
- [ ] Verificar instalação: `pip list`

#### 1.1.4 Configurar pytest

**Arquivo: `pytest.ini`**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=backlog_manager
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=90
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Tests that take more than 1s
```

**Arquivo: `.coveragerc`**
```ini
[run]
source = backlog_manager
omit = 
    */tests/*
    */venv/*
    */__init__.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

**Testar configuração:**
```bash
pytest --version
pytest --co  # Collect tests (deve estar vazio ainda)
```

**Checklist:**
- [ ] `pytest.ini` criado
- [ ] `.coveragerc` criado
- [ ] pytest funciona sem erros

#### 1.1.5 Configurar Ferramentas de Qualidade

**Arquivo: `.flake8`**
```ini
[flake8]
max-line-length = 100
exclude = 
    .git,
    __pycache__,
    venv,
    .venv,
    build,
    dist
ignore = 
    E203,  # whitespace before ':'
    W503,  # line break before binary operator
per-file-ignores =
    __init__.py:F401
```

**Arquivo: `pyproject.toml`**
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
```

**Testar ferramentas:**
```bash
black --version
flake8 --version
isort --version
mypy --version
```

**Checklist:**
- [ ] `.flake8` criado
- [ ] `pyproject.toml` criado
- [ ] Todas as ferramentas instaladas e funcionando

#### 1.1.6 Criar .gitignore

**Arquivo: `.gitignore`**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/
ENV/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Project specific
backlog.db
*.xlsx
dist/
build/
*.spec

# OS
.DS_Store
Thumbs.db
```

**Checklist:**
- [ ] `.gitignore` criado
- [ ] Git inicializado: `git init`
- [ ] Primeiro commit: `git add . && git commit -m "Initial project setup"`

#### 1.1.7 Criar README.md Inicial

**Arquivo: `README.md`**
```markdown
# Backlog Manager

Sistema desktop para planejamento inteligente de tarefas e gestão de backlog.

## Fase de Desenvolvimento

🚧 **Fase 1: Fundação e Domínio** - Em andamento

## Estrutura do Projeto

```
backlog_manager/
├── domain/          # Camada de domínio (regras de negócio)
├── application/     # Casos de uso (a implementar)
├── infrastructure/  # Persistência e serviços externos (a implementar)
└── presentation/    # Interface gráfica (a implementar)
```

## Setup de Desenvolvimento

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Windows)
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements-dev.txt
```

## Rodar Testes

```bash
# Todos os testes com cobertura
pytest

# Apenas testes unitários
pytest tests/unit -v

# Com relatório HTML de cobertura
pytest --cov-report=html
```

## Qualidade de Código

```bash
# Formatação
black backlog_manager/

# Imports ordenados
isort backlog_manager/

# Linting
flake8 backlog_manager/

# Type checking
mypy backlog_manager/

# Complexidade
radon cc backlog_manager/ -a
```

## Arquitetura

Este projeto segue os princípios de **Clean Architecture**:
- Domínio não depende de nada (núcleo puro)
- Aplicação depende apenas do domínio
- Infraestrutura e Apresentação são camadas externas

## Tecnologias

- Python 3.11+
- PySide6 (GUI)
- SQLite (Database)
- pytest (Testing)
- openpyxl (Excel)
```

**Checklist:**
- [ ] `README.md` criado
- [ ] Instruções de setup validadas

### Critérios de Aceitação da Tarefa 1.1

- [ ] Estrutura de diretórios conforme Clean Architecture criada
- [ ] Ambiente virtual funcionando
- [ ] Todas as dependências instaladas
- [ ] pytest configurado e funcionando
- [ ] Ferramentas de qualidade configuradas (black, flake8, isort, mypy)
- [ ] `.gitignore` criado
- [ ] README.md documentado
- [ ] Repositório Git inicializado com primeiro commit
- [ ] Executar sem erros: `pytest --co` (coleta 0 testes, sem erros)
- [ ] Executar sem erros: `black --check backlog_manager/`
- [ ] Executar sem erros: `flake8 backlog_manager/`

### Validação Final

Execute os seguintes comandos para validar o setup:

```bash
# 1. Verificar Python
python --version

# 2. Verificar dependências instaladas
pip list | grep -E "pytest|black|flake8"

# 3. Verificar estrutura
tree backlog_manager  # ou ls -R backlog_manager

# 4. Testar pytest
pytest --version

# 5. Commit inicial
git log --oneline
```

**Resultado esperado:** Todos os comandos executam sem erros.

---

## TAREFA 1.2: ENTIDADES DE DOMÍNIO

**Story Points:** 5 SP  
**Duração Estimada:** 2 dias  
**Prioridade:** Alta  
**Dependências:** Tarefa 1.1 concluída

### Objetivo

Implementar as três entidades principais do domínio (Story, Developer, Configuration) e seus value objects associados, seguindo princípios de DDD (Domain-Driven Design) e garantindo validações robustas.

### Conceitos de Domain-Driven Design

**Entidade vs Value Object:**
- **Entidade:** Tem identidade única (ID), pode mudar ao longo do tempo
  - Exemplo: Story, Developer
- **Value Object:** Sem identidade, imutável, definido por seus valores
  - Exemplo: StoryPoint, StoryStatus

### Subtarefas Detalhadas

#### 1.2.1 Implementar Value Object: StoryPoint

**Objetivo:** Encapsular validação de Story Points (apenas 3, 5, 8, 13 permitidos)

**Arquivo: `backlog_manager/domain/value_objects/story_point.py`**

```python
"""Value Object para Story Points."""
from typing import Final


class StoryPoint:
    """
    Value Object que representa a medida de esforço de uma história.
    
    Story Points seguem escala Fibonacci modificada:
    - 3: Tarefa Pequena (P)
    - 5: Tarefa Média (M)
    - 8: Tarefa Grande (G)
    - 13: Tarefa Muito Grande (GG)
    
    Raises:
        ValueError: Se o valor não estiver na escala permitida
    """
    
    VALID_VALUES: Final[tuple[int, ...]] = (3, 5, 8, 13)
    
    def __init__(self, value: int) -> None:
        """
        Inicializa StoryPoint com validação.
        
        Args:
            value: Valor numérico do story point
            
        Raises:
            ValueError: Se valor não for 3, 5, 8 ou 13
        """
        if value not in self.VALID_VALUES:
            raise ValueError(
                f"Story Point inválido: {value}. "
                f"Valores permitidos: {self.VALID_VALUES}"
            )
        self._value = value
    
    @property
    def value(self) -> int:
        """Retorna valor do story point."""
        return self._value
    
    def __eq__(self, other: object) -> bool:
        """Compara igualdade de StoryPoints."""
        if not isinstance(other, StoryPoint):
            return False
        return self._value == other._value
    
    def __hash__(self) -> int:
        """Hash para uso em sets e dicts."""
        return hash(self._value)
    
    def __repr__(self) -> str:
        """Representação string para debug."""
        return f"StoryPoint({self._value})"
    
    def __str__(self) -> str:
        """Representação string legível."""
        return str(self._value)
    
    @classmethod
    def from_size_label(cls, label: str) -> "StoryPoint":
        """
        Cria StoryPoint a partir de label de tamanho.
        
        Args:
            label: 'P', 'M', 'G' ou 'GG'
            
        Returns:
            StoryPoint correspondente
            
        Raises:
            ValueError: Se label inválido
        """
        mapping = {
            "P": 3,
            "M": 5,
            "G": 8,
            "GG": 13
        }
        if label not in mapping:
            raise ValueError(f"Label inválido: {label}. Use P, M, G ou GG")
        return cls(mapping[label])
```

**Arquivo de teste: `tests/unit/domain/test_story_point.py`**

```python
"""Testes unitários para StoryPoint value object."""
import pytest
from backlog_manager.domain.value_objects.story_point import StoryPoint


class TestStoryPoint:
    """Testes para StoryPoint."""
    
    def test_create_valid_story_point(self):
        """Deve criar StoryPoint com valores válidos."""
        for value in [3, 5, 8, 13]:
            sp = StoryPoint(value)
            assert sp.value == value
    
    def test_reject_invalid_story_point(self):
        """Deve rejeitar valores inválidos."""
        invalid_values = [1, 2, 4, 6, 7, 9, 10, 21, 0, -1]
        for value in invalid_values:
            with pytest.raises(ValueError, match="Story Point inválido"):
                StoryPoint(value)
    
    def test_story_point_equality(self):
        """Deve comparar igualdade corretamente."""
        sp1 = StoryPoint(5)
        sp2 = StoryPoint(5)
        sp3 = StoryPoint(8)
        
        assert sp1 == sp2
        assert sp1 != sp3
    
    def test_story_point_immutability(self):
        """Value object deve ser imutável."""
        sp = StoryPoint(5)
        with pytest.raises(AttributeError):
            sp._value = 8  # type: ignore
    
    def test_story_point_hashable(self):
        """Deve ser hashable para uso em sets."""
        sp1 = StoryPoint(5)
        sp2 = StoryPoint(5)
        sp3 = StoryPoint(8)
        
        story_points_set = {sp1, sp2, sp3}
        assert len(story_points_set) == 2  # sp1 e sp2 são iguais
    
    def test_from_size_label(self):
        """Deve criar a partir de label."""
        assert StoryPoint.from_size_label("P").value == 3
        assert StoryPoint.from_size_label("M").value == 5
        assert StoryPoint.from_size_label("G").value == 8
        assert StoryPoint.from_size_label("GG").value == 13
    
    def test_from_invalid_label(self):
        """Deve rejeitar label inválido."""
        with pytest.raises(ValueError, match="Label inválido"):
            StoryPoint.from_size_label("XL")
    
    def test_string_representation(self):
        """Deve ter representação string clara."""
        sp = StoryPoint(5)
        assert str(sp) == "5"
        assert repr(sp) == "StoryPoint(5)"
```

**Checklist Tarefa 1.2.1:**
- [ ] `story_point.py` implementado
- [ ] `test_story_point.py` implementado
- [ ] Todos os testes passando: `pytest tests/unit/domain/test_story_point.py -v`
- [ ] Cobertura 100%: `pytest tests/unit/domain/test_story_point.py --cov=backlog_manager.domain.value_objects.story_point --cov-report=term`
- [ ] Type checking OK: `mypy backlog_manager/domain/value_objects/story_point.py`
- [ ] Linting OK: `flake8 backlog_manager/domain/value_objects/story_point.py`

#### 1.2.2 Implementar Enum: StoryStatus

**Arquivo: `backlog_manager/domain/value_objects/story_status.py`**

```python
"""Enum para status de histórias."""
from enum import Enum


class StoryStatus(str, Enum):
    """
    Status possíveis de uma história no ciclo de vida.
    
    Fluxo normal: BACKLOG → EXECUÇÃO → TESTES → CONCLUÍDO
    Fluxo alternativo: Qualquer estado → IMPEDIDO
    """
    
    BACKLOG = "BACKLOG"
    EXECUCAO = "EXECUÇÃO"
    TESTES = "TESTES"
    CONCLUIDO = "CONCLUÍDO"
    IMPEDIDO = "IMPEDIDO"
    
    @classmethod
    def from_string(cls, value: str) -> "StoryStatus":
        """
        Cria StoryStatus a partir de string (case-insensitive).
        
        Args:
            value: String representando o status
            
        Returns:
            StoryStatus correspondente
            
        Raises:
            ValueError: Se string não corresponder a nenhum status
        """
        value_upper = value.upper()
        for status in cls:
            if status.value.upper() == value_upper:
                return status
        raise ValueError(
            f"Status inválido: {value}. "
            f"Valores válidos: {[s.value for s in cls]}"
        )
```

**Arquivo de teste: `tests/unit/domain/test_story_status.py`**

```python
"""Testes para StoryStatus enum."""
import pytest
from backlog_manager.domain.value_objects.story_status import StoryStatus


class TestStoryStatus:
    """Testes para enum StoryStatus."""
    
    def test_all_statuses_exist(self):
        """Deve ter todos os status esperados."""
        expected = ["BACKLOG", "EXECUÇÃO", "TESTES", "CONCLUÍDO", "IMPEDIDO"]
        actual = [s.value for s in StoryStatus]
        assert actual == expected
    
    def test_from_string_case_insensitive(self):
        """Deve aceitar string case-insensitive."""
        assert StoryStatus.from_string("backlog") == StoryStatus.BACKLOG
        assert StoryStatus.from_string("BACKLOG") == StoryStatus.BACKLOG
        assert StoryStatus.from_string("Backlog") == StoryStatus.BACKLOG
    
    def test_from_string_invalid(self):
        """Deve rejeitar string inválida."""
        with pytest.raises(ValueError, match="Status inválido"):
            StoryStatus.from_string("INVALID")
    
    def test_status_as_string(self):
        """Enum deve funcionar como string."""
        status = StoryStatus.BACKLOG
        assert status == "BACKLOG"
        assert str(status) == "BACKLOG"
```

**Checklist Tarefa 1.2.2:**
- [ ] `story_status.py` implementado
- [ ] `test_story_status.py` implementado
- [ ] Todos os testes passando
- [ ] Cobertura 100%

#### 1.2.3 Implementar Entidade: Story

**Arquivo: `backlog_manager/domain/entities/story.py`**

```python
"""Entidade Story (História)."""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


@dataclass
class Story:
    """
    Entidade que representa uma história (user story) no backlog.
    
    Uma história é uma unidade de trabalho a ser desenvolvida,
    com esforço medido em Story Points e com possíveis dependências.
    
    Attributes:
        id: Identificador único (gerado automaticamente)
        feature: Agrupamento funcional da história
        name: Nome descritivo da história
        story_point: Esforço de implementação (3, 5, 8 ou 13)
        status: Estado atual no ciclo de vida
        priority: Ordem de prioridade (menor = mais prioritário)
        developer_id: ID do desenvolvedor alocado (opcional)
        dependencies: Lista de IDs de histórias das quais depende
        start_date: Data de início planejada
        end_date: Data de término planejada
        duration: Duração em dias úteis
    """
    
    id: str
    feature: str
    name: str
    story_point: StoryPoint
    status: StoryStatus = StoryStatus.BACKLOG
    priority: int = 0
    developer_id: Optional[str] = None
    dependencies: list[str] = field(default_factory=list)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration: Optional[int] = None
    
    def __post_init__(self) -> None:
        """Valida dados após inicialização."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Valida invariantes da entidade.
        
        Raises:
            ValueError: Se dados inválidos
        """
        if not self.id or not self.id.strip():
            raise ValueError("ID da história não pode ser vazio")
        
        if not self.feature or not self.feature.strip():
            raise ValueError("Feature não pode ser vazia")
        
        if not self.name or not self.name.strip():
            raise ValueError("Nome da história não pode ser vazio")
        
        if self.priority < 0:
            raise ValueError("Prioridade não pode ser negativa")
        
        if self.duration is not None and self.duration < 0:
            raise ValueError("Duração não pode ser negativa")
        
        # Validar que não depende de si mesma
        if self.id in self.dependencies:
            raise ValueError("História não pode depender de si mesma")
    
    def add_dependency(self, story_id: str) -> None:
        """
        Adiciona dependência a outra história.
        
        Args:
            story_id: ID da história da qual depende
            
        Raises:
            ValueError: Se tentar adicionar dependência circular
        """
        if story_id == self.id:
            raise ValueError("História não pode depender de si mesma")
        
        if story_id not in self.dependencies:
            self.dependencies.append(story_id)
    
    def remove_dependency(self, story_id: str) -> None:
        """
        Remove dependência de outra história.
        
        Args:
            story_id: ID da história para remover dependência
        """
        if story_id in self.dependencies:
            self.dependencies.remove(story_id)
    
    def has_dependency(self, story_id: str) -> bool:
        """
        Verifica se depende de determinada história.
        
        Args:
            story_id: ID da história para verificar
            
        Returns:
            True se depende, False caso contrário
        """
        return story_id in self.dependencies
    
    def allocate_developer(self, developer_id: str) -> None:
        """
        Aloca desenvolvedor à história.
        
        Args:
            developer_id: ID do desenvolvedor
        """
        if not developer_id or not developer_id.strip():
            raise ValueError("ID do desenvolvedor não pode ser vazio")
        self.developer_id = developer_id
    
    def deallocate_developer(self) -> None:
        """Remove desenvolvedor alocado."""
        self.developer_id = None
    
    def is_allocated(self) -> bool:
        """Verifica se tem desenvolvedor alocado."""
        return self.developer_id is not None
    
    def __eq__(self, other: object) -> bool:
        """Entidades são iguais se têm mesmo ID."""
        if not isinstance(other, Story):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash baseado no ID."""
        return hash(self.id)
```

**Arquivo de teste parcial: `tests/unit/domain/test_story.py`** (continua...)

```python
"""Testes unitários para entidade Story."""
import pytest
from datetime import date

from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.value_objects.story_point import StoryPoint
from backlog_manager.domain.value_objects.story_status import StoryStatus


class TestStory:
    """Testes para entidade Story."""
    
    def test_create_valid_story(self):
        """Deve criar história com dados válidos."""
        story = Story(
            id="S1",
            feature="Autenticação",
            name="Implementar login",
            story_point=StoryPoint(5),
            priority=1
        )
        
        assert story.id == "S1"
        assert story.feature == "Autenticação"
        assert story.name == "Implementar login"
        assert story.story_point.value == 5
        assert story.status == StoryStatus.BACKLOG
        assert story.priority == 1
        assert story.developer_id is None
        assert story.dependencies == []
    
    def test_reject_empty_id(self):
        """Deve rejeitar ID vazio."""
        with pytest.raises(ValueError, match="ID da história não pode ser vazio"):
            Story(
                id="",
                feature="Test",
                name="Test",
                story_point=StoryPoint(5)
            )
    
    def test_reject_empty_feature(self):
        """Deve rejeitar feature vazia."""
        with pytest.raises(ValueError, match="Feature não pode ser vazia"):
            Story(
                id="S1",
                feature="",
                name="Test",
                story_point=StoryPoint(5)
            )
    
    def test_reject_negative_priority(self):
        """Deve rejeitar prioridade negativa."""
        with pytest.raises(ValueError, match="Prioridade não pode ser negativa"):
            Story(
                id="S1",
                feature="Test",
                name="Test",
                story_point=StoryPoint(5),
                priority=-1
            )
    
    def test_add_dependency(self):
        """Deve adicionar dependência."""
        story = Story(
            id="S1",
            feature="Test",
            name="Test",
            story_point=StoryPoint(5)
        )
        
        story.add_dependency("S2")
        assert story.has_dependency("S2")
        assert "S2" in story.dependencies
    
    def test_reject_self_dependency(self):
        """Não deve permitir dependência de si mesma."""
        story = Story(
            id="S1",
            feature="Test",
            name="Test",
            story_point=StoryPoint(5)
        )
        
        with pytest.raises(ValueError, match="não pode depender de si mesma"):
            story.add_dependency("S1")
    
    def test_remove_dependency(self):
        """Deve remover dependência."""
        story = Story(
            id="S1",
            feature="Test",
            name="Test",
            story_point=StoryPoint(5)
        )
        
        story.add_dependency("S2")
        story.remove_dependency("S2")
        assert not story.has_dependency("S2")
    
    def test_allocate_developer(self):
        """Deve alocar desenvolvedor."""
        story = Story(
            id="S1",
            feature="Test",
            name="Test",
            story_point=StoryPoint(5)
        )
        
        assert not story.is_allocated()
        story.allocate_developer("DEV1")
        assert story.is_allocated()
        assert story.developer_id == "DEV1"
    
    def test_deallocate_developer(self):
        """Deve desalocar desenvolvedor."""
        story = Story(
            id="S1",
            feature="Test",
            name="Test",
            story_point=StoryPoint(5),
            developer_id="DEV1"
        )
        
        story.deallocate_developer()
        assert not story.is_allocated()
    
    def test_story_equality_by_id(self):
        """Histórias são iguais se têm mesmo ID."""
        story1 = Story(
            id="S1",
            feature="Feature1",
            name="Name1",
            story_point=StoryPoint(5)
        )
        story2 = Story(
            id="S1",
            feature="Feature2",
            name="Name2",
            story_point=StoryPoint(8)
        )
        story3 = Story(
            id="S2",
            feature="Feature1",
            name="Name1",
            story_point=StoryPoint(5)
        )
        
        assert story1 == story2  # Mesmo ID
        assert story1 != story3  # IDs diferentes
```

**Checklist Tarefa 1.2.3:**
- [ ] `story.py` implementado completo
- [ ] `test_story.py` com todos os testes
- [ ] Testes passando 100%
- [ ] Cobertura ≥ 90%

#### 1.2.4 Implementar Entidade: Developer

**Arquivo: `backlog_manager/domain/entities/developer.py`**

```python
"""Entidade Developer (Desenvolvedor)."""
from dataclasses import dataclass


@dataclass
class Developer:
    """
    Entidade que representa um desenvolvedor que pode ser alocado a histórias.
    
    Attributes:
        id: Identificador único (gerado automaticamente)
        name: Nome do desenvolvedor
    """
    
    id: str
    name: str
    
    def __post_init__(self) -> None:
        """Valida dados após inicialização."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Valida invariantes da entidade.
        
        Raises:
            ValueError: Se dados inválidos
        """
        if not self.id or not self.id.strip():
            raise ValueError("ID do desenvolvedor não pode ser vazio")
        
        if not self.name or not self.name.strip():
            raise ValueError("Nome do desenvolvedor não pode ser vazio")
    
    def __eq__(self, other: object) -> bool:
        """Desenvolvedores são iguais se têm mesmo ID."""
        if not isinstance(other, Developer):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash baseado no ID."""
        return hash(self.id)
```

**Testes:** Similar aos de Story (validações, igualdade por ID, etc.)

#### 1.2.5 Implementar Entidade: Configuration

**Arquivo: `backlog_manager/domain/entities/configuration.py`**

```python
"""Entidade Configuration (Configuração global)."""
from dataclasses import dataclass


@dataclass
class Configuration:
    """
    Configuração global do sistema para cálculo de cronograma.
    
    Attributes:
        story_points_per_sprint: Velocidade do time em SP por sprint
        workdays_per_sprint: Dias úteis em uma sprint
    """
    
    story_points_per_sprint: int = 21
    workdays_per_sprint: int = 15
    
    def __post_init__(self) -> None:
        """Valida configuração."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Valida valores de configuração.
        
        Raises:
            ValueError: Se valores inválidos
        """
        if self.story_points_per_sprint <= 0:
            raise ValueError("Story Points por sprint deve ser maior que zero")
        
        if self.workdays_per_sprint <= 0:
            raise ValueError("Dias úteis por sprint deve ser maior que zero")
    
    @property
    def velocity_per_day(self) -> float:
        """
        Calcula velocidade do time por dia útil.
        
        Returns:
            Story Points por dia útil
        """
        return self.story_points_per_sprint / self.workdays_per_sprint
```

**Testes:** Validações e cálculo de velocidade por dia.

### Critérios de Aceitação da Tarefa 1.2

- [ ] Todos os value objects implementados (StoryPoint, StoryStatus)
- [ ] Todas as entidades implementadas (Story, Developer, Configuration)
- [ ] Todos os testes unitários passando
- [ ] Cobertura ≥ 90% para todas as classes de domínio
- [ ] Type checking passa sem erros
- [ ] Linting passa sem erros
- [ ] Docstrings completas em português

---

## TAREFA 1.3: EXCEÇÕES DE DOMÍNIO

**Story Points:** 2 SP  
**Duração Estimada:** 1 dia  
**Prioridade:** Alta

### Objetivo

Criar hierarquia de exceções customizadas para representar erros de domínio de forma clara e específica.

### Implementação

**Arquivo: `backlog_manager/domain/exceptions/domain_exceptions.py`**

```python
"""Exceções de domínio."""


class DomainException(Exception):
    """Exceção base para erros de domínio."""
    pass


class InvalidStoryPointException(DomainException):
    """Lançada quando Story Point inválido."""
    pass


class CyclicDependencyException(DomainException):
    """Lançada quando detectada dependência cíclica."""
    
    def __init__(self, cycle_path: list[str]):
        """
        Inicializa exceção com caminho do ciclo.
        
        Args:
            cycle_path: Lista de IDs formando o ciclo
        """
        self.cycle_path = cycle_path
        cycle_str = " → ".join(cycle_path)
        super().__init__(f"Dependência cíclica detectada: {cycle_str}")


class StoryNotFoundException(DomainException):
    """Lançada quando história não encontrada."""
    
    def __init__(self, story_id: str):
        """
        Inicializa exceção.
        
        Args:
            story_id: ID da história não encontrada
        """
        self.story_id = story_id
        super().__init__(f"História não encontrada: {story_id}")


class DeveloperNotFoundException(DomainException):
    """Lançada quando desenvolvedor não encontrado."""
    
    def __init__(self, developer_id: str):
        """
        Inicializa exceção.
        
        Args:
            developer_id: ID do desenvolvedor não encontrado
        """
        self.developer_id = developer_id
        super().__init__(f"Desenvolvedor não encontrado: {developer_id}")
```

### Critérios de Aceitação

- [ ] Hierarquia de exceções criada
- [ ] Todas as exceções documentadas
- [ ] Testes garantem que exceções funcionam corretamente
- [ ] Mensagens de erro claras e informativas

---

## TAREFA 1.4: SERVIÇO DE DETECÇÃO DE CICLOS

**Story Points:** 8 SP  
**Duração Estimada:** 3 dias  
**Prioridade:** Crítica  
**Complexidade:** Alta (algoritmo de grafo)

### Objetivo

Implementar serviço de domínio que detecta ciclos em grafo de dependências usando algoritmo DFS (Depth-First Search).

### Contexto Teórico

**Por que detectar ciclos é crucial?**
- Dependências cíclicas tornam impossível ordenar o backlog
- Exemplo de ciclo: A depende de B, B depende de C, C depende de A
- Sistema deve impedir criação de ciclos proativamente

**Algoritmo DFS para Detecção de Ciclos:**
1. Marcar nós como: Não visitado, Visitando, Visitado
2. Para cada nó não visitado, iniciar DFS
3. Se durante DFS encontrarmos um nó "Visitando", há ciclo
4. Ao terminar DFS de um nó, marcá-lo como "Visitado"

### Implementação

**Arquivo: `backlog_manager/domain/services/cycle_detector.py`**

```python
"""Serviço para detecção de ciclos em grafo de dependências."""
from typing import Dict, List, Set, Optional
from enum import Enum

from backlog_manager.domain.exceptions.domain_exceptions import CyclicDependencyException


class NodeState(Enum):
    """Estado de um nó durante DFS."""
    UNVISITED = "unvisited"
    VISITING = "visiting"
    VISITED = "visited"


class CycleDetector:
    """
    Serviço de domínio para detectar ciclos em grafo de dependências.
    
    Utiliza algoritmo DFS (Depth-First Search) para detectar ciclos
    em grafo direcionado de dependências entre histórias.
    
    Complexidade: O(V + E) onde V = vértices, E = arestas
    """
    
    def has_cycle(self, dependencies: Dict[str, List[str]]) -> bool:
        """
        Verifica se existe ciclo no grafo de dependências.
        
        Args:
            dependencies: Dicionário {story_id: [list_of_dependencies]}
            
        Returns:
            True se houver ciclo, False caso contrário
            
        Example:
            >>> detector = CycleDetector()
            >>> deps = {"A": ["B"], "B": ["A"]}
            >>> detector.has_cycle(deps)
            True
        """
        try:
            self.find_cycle_path(dependencies)
            return False
        except CyclicDependencyException:
            return True
    
    def find_cycle_path(self, dependencies: Dict[str, List[str]]) -> Optional[List[str]]:
        """
        Encontra caminho do ciclo se existir.
        
        Args:
            dependencies: Dicionário {story_id: [list_of_dependencies]}
            
        Returns:
            Lista de IDs formando o ciclo, ou None se sem ciclo
            
        Raises:
            CyclicDependencyException: Se ciclo detectado
        """
        # Inicializar estados de todos os nós
        states: Dict[str, NodeState] = {}
        all_nodes = set(dependencies.keys())
        for deps_list in dependencies.values():
            all_nodes.update(deps_list)
        
        for node in all_nodes:
            states[node] = NodeState.UNVISITED
        
        # DFS para cada nó não visitado
        for node in all_nodes:
            if states[node] == NodeState.UNVISITED:
                path: List[str] = []
                cycle = self._dfs(node, dependencies, states, path)
                if cycle:
                    raise CyclicDependencyException(cycle)
        
        return None
    
    def _dfs(
        self,
        node: str,
        dependencies: Dict[str, List[str]],
        states: Dict[str, NodeState],
        path: List[str]
    ) -> Optional[List[str]]:
        """
        Executa DFS recursivo a partir de um nó.
        
        Args:
            node: Nó atual
            dependencies: Grafo de dependências
            states: Estados dos nós
            path: Caminho atual sendo explorado
            
        Returns:
            Lista formando ciclo se detectado, None caso contrário
        """
        states[node] = NodeState.VISITING
        path.append(node)
        
        # Visitar dependências
        for dependency in dependencies.get(node, []):
            if states.get(dependency, NodeState.UNVISITED) == NodeState.VISITING:
                # Ciclo detectado! Construir caminho do ciclo
                cycle_start_index = path.index(dependency)
                cycle_path = path[cycle_start_index:] + [dependency]
                return cycle_path
            
            if states.get(dependency, NodeState.UNVISITED) == NodeState.UNVISITED:
                cycle = self._dfs(dependency, dependencies, states, path)
                if cycle:
                    return cycle
        
        states[node] = NodeState.VISITED
        path.pop()
        return None
```

### Testes Extensivos

**Arquivo: `tests/unit/domain/test_cycle_detector.py`**

```python
"""Testes para CycleDetector."""
import pytest

from backlog_manager.domain.services.cycle_detector import CycleDetector
from backlog_manager.domain.exceptions.domain_exceptions import CyclicDependencyException


class TestCycleDetector:
    """Testes para detecção de ciclos."""
    
    def test_no_cycle_empty_graph(self):
        """Grafo vazio não tem ciclo."""
        detector = CycleDetector()
        assert not detector.has_cycle({})
    
    def test_no_cycle_single_node(self):
        """Nó único sem dependências não tem ciclo."""
        detector = CycleDetector()
        deps = {"A": []}
        assert not detector.has_cycle(deps)
    
    def test_no_cycle_linear_dependency(self):
        """Dependência linear não tem ciclo."""
        detector = CycleDetector()
        deps = {
            "A": ["B"],
            "B": ["C"],
            "C": []
        }
        assert not detector.has_cycle(deps)
    
    def test_detects_simple_cycle(self):
        """Deve detectar ciclo simples A → B → A."""
        detector = CycleDetector()
        deps = {
            "A": ["B"],
            "B": ["A"]
        }
        assert detector.has_cycle(deps)
        
        with pytest.raises(CyclicDependencyException) as exc_info:
            detector.find_cycle_path(deps)
        
        assert "A" in exc_info.value.cycle_path
        assert "B" in exc_info.value.cycle_path
    
    def test_detects_indirect_cycle(self):
        """Deve detectar ciclo indireto A → B → C → A."""
        detector = CycleDetector()
        deps = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"]
        }
        assert detector.has_cycle(deps)
    
    def test_detects_self_loop(self):
        """Deve detectar auto-referência A → A."""
        detector = CycleDetector()
        deps = {"A": ["A"]}
        assert detector.has_cycle(deps)
    
    def test_complex_graph_no_cycle(self):
        """Grafo complexo sem ciclo (DAG)."""
        detector = CycleDetector()
        deps = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": ["E"],
            "E": []
        }
        assert not detector.has_cycle(deps)
    
    def test_complex_graph_with_cycle(self):
        """Grafo complexo com ciclo escondido."""
        detector = CycleDetector()
        deps = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": ["E"],
            "E": ["B"]  # Ciclo: B → D → E → B
        }
        assert detector.has_cycle(deps)
    
    def test_performance_large_graph(self):
        """Deve processar grafo grande rapidamente."""
        import time
        
        detector = CycleDetector()
        
        # Criar grafo com 100 nós em cadeia (sem ciclo)
        deps = {f"S{i}": [f"S{i+1}"] for i in range(99)}
        deps["S99"] = []
        
        start = time.time()
        result = detector.has_cycle(deps)
        elapsed = time.time() - start
        
        assert not result
        assert elapsed < 0.1  # Deve ser < 100ms
```

### Critérios de Aceitação

- [ ] `CycleDetector` implementado com DFS
- [ ] Detecta todos os tipos de ciclos (direto, indireto, self-loop)
- [ ] Retorna caminho do ciclo quando detectado
- [ ] Performance < 100ms para 100 histórias
- [ ] Testes extensivos cobrindo casos extremos
- [ ] Cobertura ≥ 95%

---

## TAREFA 1.5: SERVIÇO DE ORDENAÇÃO DE BACKLOG

**Story Points:** 8 SP  
**Duração Estimada:** 3 dias  
**Prioridade:** Crítica  
**Complexidade:** Alta (ordenação topológica)

### Objetivo

Implementar ordenação topológica (Kahn's Algorithm) para ordenar backlog respeitando dependências, com ordenação secundária por prioridade.

### Algoritmo de Kahn (Topological Sort)

1. Calcular in-degree (número de dependências) de cada nó
2. Adicionar nós com in-degree 0 a uma fila
3. Enquanto fila não vazia:
   - Remover nó da fila
   - Adicionar à ordenação final
   - Decrementar in-degree dos vizinhos
   - Se vizinho atingir in-degree 0, adicionar à fila
4. Se todos os nós foram ordenados, sucesso; caso contrário, há ciclo

### Implementação (resumida - arquivo completo no projeto)

```python
class BacklogSorter:
    """
    Serviço para ordenar backlog considerando dependências e prioridade.
    
    Critérios de ordenação:
    1. Histórias sem dependências vêm primeiro
    2. Dentro do mesmo nível, ordenar por prioridade (menor primeiro)
    """
    
    def sort(self, stories: List[Story]) -> List[Story]:
        """Ordena histórias usando Kahn's Algorithm + prioridade."""
        # Implementação...
```

### Testes

- Histórias sem dependências
- Dependências simples (cadeia)
- Dependências complexas (DAG)
- Ordenação por prioridade no mesmo nível
- Performance < 500ms para 100 histórias

---

## TAREFA 1.6: SERVIÇO DE CÁLCULO DE CRONOGRAMA

**Story Points:** 8 SP  
**Duração Estimada:** 3 dias  
**Prioridade:** Alta  
**Complexidade:** Média-Alta

### Objetivo

Calcular datas de início, fim e duração para cada história, considerando Story Points, velocidade do time e alocação de desenvolvedores.

### Fórmula de Cálculo

```
Duração (dias) = ceil(Story Points / (Velocidade do Time / Dias Úteis por Sprint))

Exemplo:
- Story Point: 8
- Velocidade: 21 SP / 15 dias = 1.4 SP/dia
- Duração: ceil(8 / 1.4) = ceil(5.71) = 6 dias
```

### Regras de Sequenciamento

- Histórias do mesmo desenvolvedor executam em sequência
- Histórias de desenvolvedores diferentes executam em paralelo
- Considerar apenas dias úteis (segunda a sexta)

### Implementação

```python
class ScheduleCalculator:
    """Calcula cronograma (datas e durações) para histórias."""
    
    def calculate(
        self,
        stories: List[Story],
        config: Configuration
    ) -> List[Story]:
        """
        Calcula cronograma completo.
        
        Args:
            stories: Histórias ordenadas
            config: Configuração (velocidade)
            
        Returns:
            Histórias com datas calculadas
        """
        # Implementação...
```

---

## VALIDAÇÃO FINAL DA FASE 1

### Checklist Completo

**Setup e Estrutura:**
- [ ] Estrutura de diretórios Clean Architecture criada
- [ ] Ambiente virtual configurado
- [ ] Dependências instaladas
- [ ] pytest configurado
- [ ] Ferramentas de qualidade configuradas

**Entidades e Value Objects:**
- [ ] StoryPoint implementado e testado
- [ ] StoryStatus implementado e testado
- [ ] Story implementado e testado
- [ ] Developer implementado e testado
- [ ] Configuration implementado e testado

**Exceções:**
- [ ] Hierarquia de exceções criada
- [ ] Todas exceções documentadas e testadas

**Serviços de Domínio:**
- [ ] CycleDetector implementado com DFS
- [ ] BacklogSorter implementado com Kahn's Algorithm
- [ ] ScheduleCalculator implementado

**Qualidade:**
- [ ] Todos os testes passando: `pytest tests/unit/domain -v`
- [ ] Cobertura ≥ 90%: `pytest --cov=backlog_manager/domain --cov-report=term`
- [ ] Type checking OK: `mypy backlog_manager/domain`
- [ ] Linting OK: `flake8 backlog_manager/domain`
- [ ] Formatting OK: `black --check backlog_manager/domain`

**Performance:**
- [ ] CycleDetector: < 100ms para 100 histórias
- [ ] BacklogSorter: < 500ms para 100 histórias
- [ ] ScheduleCalculator: < 1s para 100 histórias

**Documentação:**
- [ ] Todas as classes têm docstrings em português
- [ ] README.md atualizado
- [ ] Commits organizados e descritivos

### Comando de Validação Final

```bash
# Execute este script para validar tudo
# validar_fase1.sh

echo "=== Validação Fase 1 ==="

echo "\n1. Executando testes..."
pytest tests/unit/domain -v

echo "\n2. Verificando cobertura..."
pytest --cov=backlog_manager/domain --cov-report=term --cov-fail-under=90

echo "\n3. Type checking..."
mypy backlog_manager/domain

echo "\n4. Linting..."
flake8 backlog_manager/domain

echo "\n5. Verificando formatação..."
black --check backlog_manager/domain

echo "\n6. Medindo complexidade..."
radon cc backlog_manager/domain -a -nc

echo "\n=== Validação Completa! ==="
```

### Critérios de Sucesso

✅ **Fase 1 está completa quando:**
1. Todos os testes passam (100%)
2. Cobertura ≥ 90%
3. Type checking sem erros
4. Linting sem warnings
5. Performance dentro dos limites
6. Documentação completa
7. Código revisado e aprovado

---

## PRÓXIMOS PASSOS

Após concluir a Fase 1, você terá:
- ✅ Fundação sólida de domínio
- ✅ Algoritmos core funcionando
- ✅ Base para Fase 2 (Casos de Uso)

**Preparação para Fase 2:**
- Revisar interfaces (Ports) que serão necessárias
- Planejar DTOs para comunicação entre camadas
- Estudar padrões de casos de uso

---

**A Fase 1 é o alicerce de todo o projeto. Invista tempo aqui para economizar semanas depois!**
