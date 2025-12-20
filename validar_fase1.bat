@echo off
echo === VALIDACAO FASE 1 ===
echo.

echo 1. Verificando estrutura de diretorios...
if not exist "backlog_manager\domain\entities" (
    echo FALHA: Diretorio entities nao encontrado
    exit /b 1
)
if not exist "backlog_manager\domain\value_objects" (
    echo FALHA: Diretorio value_objects nao encontrado
    exit /b 1
)
if not exist "backlog_manager\domain\services" (
    echo FALHA: Diretorio services nao encontrado
    exit /b 1
)
if not exist "tests\unit\domain" (
    echo FALHA: Diretorio tests nao encontrado
    exit /b 1
)
echo OK - Estrutura de diretorios correta
echo.

echo 2. Executando testes...
pytest tests/unit/domain -v
if errorlevel 1 (
    echo FALHA: Testes nao passaram
    exit /b 1
)
echo.

echo 3. Verificando cobertura...
pytest --cov=backlog_manager/domain --cov-report=term --cov-fail-under=90
if errorlevel 1 (
    echo FALHA: Cobertura abaixo de 90%%
    exit /b 1
)
echo.

echo 4. Type checking...
mypy backlog_manager/domain
if errorlevel 1 (
    echo FALHA: Erros de type checking
    exit /b 1
)
echo.

echo 5. Linting...
flake8 backlog_manager/domain
if errorlevel 1 (
    echo FALHA: Erros de linting
    exit /b 1
)
echo.

echo 6. Verificando formatacao...
black --check backlog_manager/domain
if errorlevel 1 (
    echo AVISO: Codigo nao formatado. Execute: black backlog_manager/
)
echo.

echo === VALIDACAO COMPLETA COM SUCESSO! ===
