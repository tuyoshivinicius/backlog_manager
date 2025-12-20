# Como Executar o Backlog Manager

## 🚀 Início Rápido

### Requisitos

- Python 3.11 ou superior
- Windows 10+ (recomendado)

### Instalação

```bash
# 1. Ativar ambiente virtual
.\venv\Scripts\activate

# 2. Instalar dependências (se ainda não instalou)
pip install -r requirements.txt

# 3. Executar aplicação
python main.py
```

## 📋 Primeira Execução

Na primeira vez que executar:

1. A aplicação criará automaticamente o banco de dados `backlog.db`
2. A janela principal será exibida
3. A tabela estará vazia

### Opção 1: Criar Histórias Manualmente

1. Clique em "Nova História" (ou pressione `Ctrl+N`)
2. Preencha os campos obrigatórios:
   - Feature (ex: "Login")
   - Nome (ex: "Implementar tela de login")
   - Story Point (3, 5, 8 ou 13)
   - Status (BACKLOG, EXECUÇÃO, etc.)
3. Clique em "Salvar"

### Opção 2: Importar de Excel

1. Clique em "Importar Excel" (ou pressione `Ctrl+I`)
2. Selecione um arquivo Excel com as colunas:
   - Feature
   - Nome
   - StoryPoint
3. As histórias serão importadas automaticamente

## 🎮 Atalhos de Teclado

### Arquivo
- `Ctrl+I` - Importar Excel
- `Ctrl+E` - Exportar Excel
- `Alt+F4` - Sair

### História
- `Ctrl+N` - Nova História
- `Enter` - Editar História (selecionada)
- `Ctrl+D` - Duplicar História
- `Delete` - Deletar História
- `Ctrl+Up` - Aumentar Prioridade
- `Ctrl+Down` - Diminuir Prioridade

### Desenvolvedor
- `Ctrl+Shift+N` - Novo Desenvolvedor

### Cronograma
- `F5` - Calcular Cronograma

### Geral
- `Ctrl+,` - Configurações
- `F1` - Atalhos de Teclado

## 🔧 Funcionalidades Principais

### 1. Gestão de Histórias

**Criar:** Use o formulário para criar novas histórias com todos os campos necessários.

**Editar Inline:** Double-click em qualquer campo editável na tabela para modificar diretamente.

**Editar Formulário:** Selecione uma história e pressione `Enter` para abrir o formulário completo.

**Duplicar:** Útil para criar histórias similares rapidamente.

**Deletar:** Remove história com confirmação.

### 2. Priorização

As histórias são ordenadas por prioridade (menor número = maior prioridade).

Use `Ctrl+Up/Down` para mover histórias na fila de prioridade.

### 3. Desenvolvedores

**Criar:** Adicione desenvolvedores ao sistema para alocação.

**Alocar:** Atribua desenvolvedores diretamente na tabela ou use "Alocar Desenvolvedores" para alocação automática round-robin.

### 4. Dependências

Defina dependências entre histórias para garantir ordem correta de execução.

O sistema detecta ciclos automaticamente e impede configurações inválidas.

### 5. Cálculo de Cronograma

Pressione `F5` para calcular:
- Ordenação topológica respeitando dependências
- Datas de início e fim baseadas em Story Points
- Duração em dias úteis
- Sequenciamento por desenvolvedor

### 6. Import/Export Excel

**Importar:** Arquivo Excel deve ter colunas: Feature, Nome, StoryPoint

**Exportar:** Gera planilha completa com todas as 11 colunas de dados.

## 🎨 Interface

### Tabela de Backlog

11 colunas de informação:
1. **Prioridade** - Ordem de execução (calculada)
2. **ID** - Identificador único (gerado)
3. **Feature** - Agrupamento funcional (editável)
4. **Nome** - Descrição da história (editável)
5. **Status** - Estado atual (editável)
6. **Desenvolvedor** - Alocado (editável)
7. **Dependências** - Histórias requeridas (editável)
8. **SP** - Story Points (editável: 3, 5, 8, 13)
9. **Início** - Data de início (calculada)
10. **Fim** - Data de término (calculada)
11. **Duração** - Dias úteis (calculada)

### Cores por Status

- 🔵 **BACKLOG** - Azul
- 🟠 **EXECUÇÃO** - Laranja
- 🟣 **TESTES** - Roxo
- 🟢 **CONCLUÍDO** - Verde
- 🔴 **IMPEDIDO** - Vermelho

### Menu de Contexto

Clique com botão direito em qualquer história para:
- Editar
- Duplicar
- Deletar

## ⚙️ Configurações

Acesse `Ctrl+,` para configurar:

- **Story Points por Sprint** - Velocidade do time (padrão: 21)
- **Dias Úteis por Sprint** - Quantidade de dias (padrão: 15)

A **Velocidade por Dia** é calculada automaticamente (SP/Sprint ÷ Dias/Sprint).

## 🐛 Resolução de Problemas

### Aplicação não inicia

```bash
# Verificar instalação do PySide6
python -c "from PySide6.QtWidgets import QApplication; print('OK')"

# Reinstalar se necessário
pip install --force-reinstall PySide6
```

### Erro de banco de dados

```bash
# Remover banco e recriar
rm backlog.db
python main.py
```

### Erro de importação Excel

Verifique se o arquivo Excel tem as colunas obrigatórias:
- Feature (texto)
- Nome (texto)
- StoryPoint (número: 3, 5, 8 ou 13)

## 📊 Exemplo de Uso

### Fluxo Completo

1. **Criar Desenvolvedores**
   - Menu "Desenvolvedor" → "Novo Desenvolvedor"
   - Adicione: "Gabriel", "Ana", "Carlos"

2. **Importar ou Criar Histórias**
   - Importe Excel ou crie manualmente
   - Ex: 10 histórias de diferentes features

3. **Adicionar Dependências**
   - Edite campo "Dependências" na tabela
   - Ex: "S2" depende de "S1" (digite "S1")

4. **Alocar Desenvolvedores**
   - Menu "Cronograma" → "Alocar Desenvolvedores"
   - Ou atribua manualmente na tabela

5. **Calcular Cronograma**
   - Pressione `F5`
   - Datas e duração serão calculadas automaticamente

6. **Exportar Resultados**
   - Pressione `Ctrl+E`
   - Salve como "backlog.xlsx"

## 🎯 Boas Práticas

1. **Sempre calcule cronograma** após:
   - Mudar Story Points
   - Mudar desenvolvedor alocado
   - Adicionar/remover dependências

2. **Mantenha prioridades organizadas**
   - Use números sequenciais (1, 2, 3...)
   - Recalcule após mudanças

3. **Valide dependências**
   - Sistema impede ciclos automaticamente
   - Verifique se ordem faz sentido

4. **Faça backup do banco**
   - Copie `backlog.db` periodicamente
   - Ou exporte para Excel regularmente

## 📞 Suporte

Para reportar bugs ou sugerir melhorias:
- Crie uma issue no repositório do projeto
- Descreva o problema detalhadamente
- Inclua passos para reproduzir

## 🚀 Próximas Features (Fase 5)

Em desenvolvimento:
- 📊 Timeline/Roadmap visual (estilo Gantt)
- 🔍 Sistema de filtros avançado
- ⚡ Otimizações de performance
- ↩️ Undo/Redo
- 🎨 Temas personalizáveis

---

**Versão:** 1.0.0 (Fase 4 Completa)
**Data:** Dezembro 2024
