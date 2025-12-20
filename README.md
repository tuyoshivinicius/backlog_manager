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
