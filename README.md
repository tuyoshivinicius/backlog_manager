# Backlog Manager

Sistema desktop para planejamento inteligente de tarefas e gestão de backlog com alocação automática de desenvolvedores.

## Funcionalidades

- **Gestão de User Stories**: Criação, edição, duplicação e priorização de histórias
- **Gestão de Dependências**: Definir dependências entre histórias com detecção automática de ciclos
- **Cálculo de Cronograma**: Datas calculadas automaticamente baseadas em story points, considerando apenas dias úteis e feriados brasileiros
- **Alocação Automática**: Algoritmo inteligente de alocação de desenvolvedores com balanceamento de carga
- **Import/Export Excel**: Importação e exportação de backlog via planilhas Excel
- **Validações**: Detecção de conflitos, ciclos de dependência e períodos ociosos

## Executar a Aplicação

```bash
# Ativar ambiente virtual (Windows)
.\venv\Scripts\activate

# Executar aplicação
python -m backlog_manager.main
```

## Estrutura do Projeto

```
backlog_manager/
├── domain/          # Camada de domínio (entidades, value objects, serviços de domínio)
├── application/     # Casos de uso e DTOs
├── infrastructure/  # Persistência (SQLite) e serviços externos (Excel)
└── presentation/    # Interface gráfica (PySide6/Qt)
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

## Regras de Negócio

- **Story Points**: Escala Fibonacci (3=P, 5=M, 8=G, 13=GG)
- **Cronograma**: Considera apenas dias úteis (seg-sex) e feriados brasileiros nacionais
- **Dependências**: Devem ser acíclicas (sem ciclos de dependência)
- **Alocação**: Um desenvolvedor por história, sem sobreposição de períodos
- **Prioridade**: Menor número = maior prioridade

## Arquitetura

Este projeto segue os princípios de **Clean Architecture**:
- **Domínio**: Núcleo puro sem dependências externas (entidades, value objects, regras de negócio)
- **Aplicação**: Orquestração via casos de uso, depende apenas do domínio
- **Infraestrutura**: Implementações de persistência e serviços externos
- **Apresentação**: Interface gráfica (camada mais externa)

Para mais detalhes técnicos, consulte o arquivo `claude.md`.

## Tecnologias

**Core:**
- Python 3.11+
- PySide6 6.6.1 (Interface gráfica Qt)
- SQLite (Banco de dados)
- openpyxl 3.1.2 (Manipulação de Excel)

**Testes e Qualidade:**
- pytest 7.4.3 (Framework de testes)
- black 23.12.0 (Formatação de código)
- mypy 1.7.1 (Type checking)
- flake8 6.1.0 (Linting)
