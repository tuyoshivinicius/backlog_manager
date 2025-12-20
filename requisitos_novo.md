# ESPECIFICAÇÃO DE REQUISITOS DO SISTEMA
**Projeto:** Gestão de Backlog  
**Versão:** 2.0  
**Data:** 20/12/2025  
**Descrição:** Sistema desktop para planejamento inteligente de tarefas, organização automática de backlog, gerenciamento de dependências e otimização de alocação de desenvolvedores.

---

## SUMÁRIO
1. [Requisitos Funcionais](#requisitos-funcionais)
2. [Requisitos de Dados](#requisitos-de-dados)
3. [Requisitos de Interface](#requisitos-de-interface)
4. [Requisitos Não-Funcionais](#requisitos-não-funcionais)
5. [Requisitos de Qualidade](#requisitos-de-qualidade)
6. [Glossário](#glossário)
7. [Premissas e Restrições](#premissas-e-restrições)
8. [Matriz de Rastreabilidade](#matriz-de-rastreabilidade)
9. [Caso de Uso Principal](#caso-de-uso-principal)

---

## REQUISITOS FUNCIONAIS

### RF-001 - Cadastrar História
**Descrição:** O sistema deve permitir ao usuário cadastrar uma nova história no backlog através de formulário dedicado.  
**Critérios de Aceitação:**
- O formulário deve solicitar obrigatoriamente: Feature, Nome e Story Point
- Após confirmação, a história deve ser persistida no banco de dados
- Um ID único deve ser gerado automaticamente no formato: primeira letra da Feature + número incremental (ex: S1, S2)
- A prioridade inicial deve ser definida automaticamente como o último valor disponível
- O status inicial deve ser "BACKLOG"
- O sistema deve exibir mensagem de sucesso após cadastro  

**Prioridade:** Alta  
**Dependências:** RD-001

---

### RF-002 - Editar História
**Descrição:** O sistema deve permitir ao usuário editar os dados de uma história existente através de formulário dedicado.  
**Critérios de Aceitação:**
- O formulário deve permitir alteração de: Feature, Nome, Story Point, Status, Desenvolvedor, Dependências e Prioridade
- O ID da história não pode ser alterado
- Alterações devem ser persistidas imediatamente no banco de dados
- O sistema deve validar os dados antes de salvar
- O sistema deve exibir mensagem de sucesso após edição  

**Prioridade:** Alta  
**Dependências:** RF-001, RD-001

---

### RF-003 - Deletar História
**Descrição:** O sistema deve permitir ao usuário excluir permanentemente uma história do backlog.  
**Critérios de Aceitação:**
- O sistema deve solicitar confirmação antes de excluir
- Após confirmação, a história deve ser removida do banco de dados
- Se outras histórias dependem da história sendo excluída, o sistema deve remover essa dependência automaticamente
- O sistema deve exibir mensagem de sucesso após exclusão  

**Prioridade:** Alta  
**Dependências:** RF-001, RF-005

---

### RF-004 - Listar Histórias
**Descrição:** O sistema deve exibir todas as histórias cadastradas em formato de tabela ordenada.  
**Critérios de Aceitação:**
- A tabela deve exibir as colunas: Prioridade, ID, Feature, Nome, Status, Desenvolvedor, Dependências, Story Point, Início, Fim e Duração
- As histórias devem ser ordenadas conforme algoritmo de ordenação do backlog (RF-014)
- A tabela deve ser atualizada automaticamente quando houver alterações nos dados  

**Prioridade:** Alta  
**Dependências:** RF-001, RF-014

---

### RF-005 - Gerenciar Dependências entre Histórias
**Descrição:** O sistema deve permitir ao usuário definir que uma história depende de uma ou mais outras histórias.  
**Critérios de Aceitação:**
- O usuário deve poder adicionar dependências informando o ID de histórias existentes
- O usuário deve poder remover dependências existentes
- As dependências devem ser armazenadas como lista de IDs de histórias
- O sistema deve exibir erro se o ID informado não existir  

**Prioridade:** Alta  
**Dependências:** RF-001, RD-001

---

### RF-006 - Detectar Dependências Cíclicas
**Descrição:** O sistema deve detectar e impedir a criação de dependências cíclicas entre histórias.  
**Critérios de Aceitação:**
- Ao adicionar uma dependência, o sistema deve validar se não cria ciclo
- Um ciclo é configurado quando: A depende de B, B depende de C, C depende de A (direto ou indireto)
- Se detectado ciclo, o sistema deve exibir mensagem de erro e não permitir a operação
- A mensagem deve indicar quais histórias formam o ciclo  

**Prioridade:** Alta  
**Dependências:** RF-005

---

### RF-007 - Cadastrar Desenvolvedor
**Descrição:** O sistema deve permitir ao usuário cadastrar um novo desenvolvedor.  
**Critérios de Aceitação:**
- O formulário deve solicitar obrigatoriamente o Nome do desenvolvedor
- Um ID único deve ser gerado automaticamente usando as duas primeiras letras do nome em maiúsculo (ex: Gabriela = GA, Lucas = LU)
- Se o ID gerado já existir, deve adicionar número incremental (ex: GA1, GA2)
- Após confirmação, o desenvolvedor deve ser persistido no banco de dados
- O sistema deve exibir mensagem de sucesso após cadastro  

**Prioridade:** Alta  
**Dependências:** RD-002

---

### RF-008 - Editar Desenvolvedor
**Descrição:** O sistema deve permitir ao usuário editar os dados de um desenvolvedor existente.  
**Critérios de Aceitação:**
- O formulário deve permitir alteração do Nome
- O ID do desenvolvedor não pode ser alterado
- Alterações devem ser persistidas imediatamente no banco de dados
- O sistema deve exibir mensagem de sucesso após edição  

**Prioridade:** Média  
**Dependências:** RF-007, RD-002

---

### RF-009 - Deletar Desenvolvedor
**Descrição:** O sistema deve permitir ao usuário excluir permanentemente um desenvolvedor.  
**Critérios de Aceitação:**
- O sistema deve solicitar confirmação antes de excluir
- Se o desenvolvedor está alocado em alguma história, deve remover a alocação automaticamente
- Após confirmação, o desenvolvedor deve ser removido do banco de dados
- O sistema deve exibir mensagem de sucesso após exclusão  

**Prioridade:** Média  
**Dependências:** RF-007

---

### RF-010 - Alocar Desenvolvedor Manualmente
**Descrição:** O sistema deve permitir ao usuário alocar manualmente um desenvolvedor específico a uma história.  
**Critérios de Aceitação:**
- O usuário deve poder selecionar um desenvolvedor da lista de desenvolvedores cadastrados
- A alocação deve ser salva imediatamente no campo "Desenvolvedor" da história
- O sistema deve validar se o desenvolvedor existe
- Após alocação manual, o sistema deve executar o cálculo de cronograma automaticamente (RF-014)  

**Prioridade:** Alta  
**Dependências:** RF-001, RF-007, RF-014

---

### RF-011 - Alocar Desenvolvedores Automaticamente
**Descrição:** O sistema deve alocar automaticamente desenvolvedores disponíveis às histórias não alocadas quando solicitado pelo usuário.  
**Critérios de Aceitação:**
- Deve processar apenas histórias que não possuem desenvolvedor alocado
- Deve considerar apenas desenvolvedores cadastrados no sistema
- Deve respeitar a ordem de prioridade do backlog ordenado
- Deve respeitar as dependências entre histórias
- A alocação deve seguir estratégia round-robin (distribuição equilibrada entre desenvolvedores)
- Após alocação, deve persistir as alterações no banco de dados  

**Prioridade:** Alta  
**Dependências:** RF-001, RF-007, RF-014

---

### RF-012 - Alterar Prioridade Manualmente
**Descrição:** O sistema deve permitir ao usuário alterar a prioridade de uma história através de botões "Mover para Cima" e "Mover para Baixo".  
**Critérios de Aceitação:**
- Apenas uma história pode ser selecionada por vez
- "Mover para Cima" deve diminuir o valor numérico da prioridade em 1
- "Mover para Baixo" deve aumentar o valor numérico da prioridade em 1
- Não deve permitir mover além dos limites (primeira ou última posição)
- Após alteração, deve ajustar a prioridade da história afetada pela troca
- Deve executar cálculo de cronograma automaticamente após mudança (RF-014)  

**Prioridade:** Média  
**Dependências:** RF-001, RF-014

---

### RF-013 - Duplicar História
**Descrição:** O sistema deve permitir ao usuário duplicar uma história existente, criando uma nova com os mesmos dados exceto ID.  
**Critérios de Aceitação:**
- Deve copiar todos os campos exceto ID (que deve ser gerado automaticamente)
- A nova história deve receber prioridade como último valor disponível
- O status deve ser resetado para "BACKLOG"
- O desenvolvedor alocado não deve ser copiado (campo vazio)
- Deve persistir a nova história no banco de dados
- O sistema deve exibir mensagem de sucesso  

**Prioridade:** Baixa  
**Dependências:** RF-001

---

### RF-014 - Calcular Cronograma Automaticamente
**Descrição:** O sistema deve calcular automaticamente o cronograma completo do backlog, incluindo ordenação, alocação de desenvolvedores e cálculo de datas.  
**Critérios de Aceitação:**
- Deve ordenar as histórias considerando: 1º dependências técnicas (histórias sem dependências vêm antes), 2º prioridade numérica (menor número = maior prioridade)
- Deve alocar desenvolvedores disponíveis seguindo estratégia round-robin
- Deve calcular data de início de cada história considerando a data de término da última história alocada ao mesmo desenvolvedor
- Deve calcular duração em dias úteis usando a fórmula: `Duração = Story Point / (Velocidade do Time / Dias Úteis por Sprint)`
- Deve calcular data de fim somando a duração à data de início
- Deve executar todo processo em tempo inferior a 2 segundos para backlogs de até 100 histórias
- Deve atualizar a tabela de backlog automaticamente após conclusão  

**Prioridade:** Alta  
**Dependências:** RF-001, RF-005, RF-007, RNF-003

---

### RF-015 - Recalcular Cronograma Automaticamente
**Descrição:** O sistema deve recalcular automaticamente o cronograma sempre que houver alteração em Story Point, Prioridade ou Alocação de Desenvolvedor de uma história.  
**Critérios de Aceitação:**
- Deve detectar alterações nos campos: Story Point, Prioridade, Desenvolvedor
- Deve executar o cálculo de cronograma (RF-014) de forma reativa e automática
- Não deve requerer ação manual do usuário
- Deve atualizar a interface imediatamente após recálculo  

**Prioridade:** Alta  
**Dependências:** RF-002, RF-010, RF-012, RF-014

---

### RF-016 - Importar Histórias de Planilha Excel
**Descrição:** O sistema deve permitir ao usuário importar histórias a partir de um arquivo Excel (.xlsx).  
**Critérios de Aceitação:**
- A planilha deve conter obrigatoriamente as colunas: Feature, Nome, StoryPoint
- O sistema deve validar a existência e formato das colunas antes de importar
- Para cada linha válida, deve criar uma nova história no banco de dados
- Deve gerar ID automaticamente para cada história importada
- Deve validar que Story Point seja um dos valores permitidos (3, 5, 8, 13)
- Deve exibir relatório ao final indicando quantas histórias foram importadas e quantas falharam
- Se houver erros, deve exibir detalhes (linha e motivo)  

**Prioridade:** Alta  
**Dependências:** RF-001

---

### RF-017 - Exportar Backlog para Excel
**Descrição:** O sistema deve permitir ao usuário exportar a tabela de backlog completa para um arquivo Excel (.xlsx).  
**Critérios de Aceitação:**
- O arquivo deve conter todas as colunas exibidas na tabela de backlog
- Deve manter a ordenação atual do backlog
- Deve incluir formatação básica (cabeçalho em negrito, bordas nas células)
- O usuário deve poder escolher o local e nome do arquivo
- Deve exibir mensagem de sucesso indicando onde o arquivo foi salvo  

**Prioridade:** Alta  
**Dependências:** RF-004

---

### RF-018 - Filtrar Histórias
**Descrição:** O sistema deve permitir ao usuário filtrar histórias exibidas na tabela por diferentes critérios.  
**Critérios de Aceitação:**
- Deve permitir filtrar por: Feature, Status, Desenvolvedor, Story Point
- Deve permitir múltiplos filtros simultaneamente
- Deve atualizar a tabela em tempo real conforme filtros são aplicados
- Deve exibir contador de histórias filtradas
- Deve permitir limpar todos os filtros com um único clique  

**Prioridade:** Média  
**Dependências:** RF-004

---

### RF-019 - Configurar Velocidade do Time
**Descrição:** O sistema deve permitir ao usuário configurar a velocidade de entrega do time para cálculo de cronograma.  
**Critérios de Aceitação:**
- Deve solicitar: Story Points por Sprint e Dias Úteis por Sprint
- Deve calcular automaticamente: Story Points por Dia Útil = SP por Sprint / Dias Úteis por Sprint
- Deve validar que ambos os valores sejam números positivos maiores que zero
- Deve persistir a configuração no banco de dados
- Deve ser acessível através do menu "Configurações"
- Valores padrão: 21 SP por Sprint, 15 Dias Úteis por Sprint (1.4 SP/dia)  

**Prioridade:** Alta  
**Dependências:** RF-014, RD-003

---

### RF-020 - Editar História Inline na Tabela
**Descrição:** O sistema deve permitir ao usuário editar campos da história diretamente nas células da tabela, sem necessidade de abrir formulário.  
**Critérios de Aceitação:**
- Deve permitir edição inline dos campos: Feature, Nome, Story Point, Dependências, Desenvolvedor
- Ao clicar duas vezes em uma célula editável, deve habilitar modo de edição
- Ao pressionar Enter ou clicar fora, deve salvar a alteração
- Ao pressionar Esc, deve cancelar a edição
- Deve validar o valor antes de salvar
- Se o campo editado for Story Point, Prioridade ou Desenvolvedor, deve executar recálculo de cronograma (RF-015)  

**Prioridade:** Alta  
**Dependências:** RF-002, RF-015, RI-002

---

### RF-021 - Visualizar Timeline/Roadmap
**Descrição:** O sistema deve fornecer uma visualização do cronograma em formato de timeline ou roadmap.  
**Critérios de Aceitação:**
- Deve exibir as histórias distribuídas ao longo de uma linha do tempo
- Deve mostrar data de início, duração e data de fim visualmente
- Deve diferenciar visualmente histórias por desenvolvedor (cores distintas)
- Deve permitir navegação pela linha do tempo (scroll horizontal)
- Deve exibir tooltips com detalhes da história ao passar o mouse
- Deve ser acessível através de botão ou aba dedicada na interface  

**Prioridade:** Média  
**Dependências:** RF-014

---

---

## REQUISITOS DE DADOS

### RD-001 - Estrutura de Dados da História
**Descrição:** O sistema deve armazenar histórias com estrutura de dados específica.  
**Critérios de Aceitação:**
- **ID** [String]: Gerado automaticamente (primeira letra da Feature + número incremental)
- **Feature** [String]: Obrigatório, texto livre
- **Nome** [String]: Obrigatório, texto livre
- **Status** [Enum]: Obrigatório, valores permitidos: BACKLOG, EXECUÇÃO, TESTES, CONCLUÍDO, IMPEDIDO
- **Prioridade** [Integer]: Obrigatório, número inteiro positivo
- **Desenvolvedor** [String]: Opcional, ID de desenvolvedor existente ou NULL
- **Dependências** [Array<String>]: Opcional, lista de IDs de histórias existentes
- **StoryPoint** [Integer]: Obrigatório, valores permitidos: 3, 5, 8, 13
- **Início** [Date]: Opcional, formato DD/MM/YYYY
- **Fim** [Date]: Opcional, formato DD/MM/YYYY
- **Duração** [Integer]: Calculado, número de dias úteis  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RD-002 - Estrutura de Dados do Desenvolvedor
**Descrição:** O sistema deve armazenar desenvolvedores com estrutura de dados específica.  
**Critérios de Aceitação:**
- **ID** [String]: Gerado automaticamente (duas primeiras letras do nome em maiúsculo)
- **Nome** [String]: Obrigatório, texto livre  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RD-003 - Estrutura de Dados de Configuração
**Descrição:** O sistema deve armazenar configurações globais.  
**Critérios de Aceitação:**
- **StoryPointsPorSprint** [Integer]: Obrigatório, valor padrão 21
- **DiasUteisPorSprint** [Integer]: Obrigatório, valor padrão 15
- **VelocidadePorDia** [Decimal]: Calculado automaticamente (SP por Sprint / Dias Úteis)  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RD-004 - Validação de Story Points
**Descrição:** O sistema deve validar que Story Points sigam a escala Fibonacci modificada.  
**Critérios de Aceitação:**
- Apenas os valores 3, 5, 8, 13 são permitidos
- 3 = Tarefa Pequena (P)
- 5 = Tarefa Média (M)
- 8 = Tarefa Grande (G)
- 13 = Tarefa Muito Grande (GG)
- Qualquer outro valor deve ser rejeitado com mensagem de erro  

**Prioridade:** Alta  
**Dependências:** RD-001

---

### RD-005 - Cálculo de Duração
**Descrição:** O sistema deve calcular a duração de uma história em dias úteis.  
**Critérios de Aceitação:**
- Fórmula: `Duração = (Story Point / Velocidade por Dia)`
- Velocidade por Dia = Story Points por Sprint / Dias Úteis por Sprint
- O resultado deve ser arredondado para o próximo número inteiro (ceiling)
- Exemplo: SP=8, Velocidade=1.4 → Duração = 8/1.4 = 5.71 → 6 dias  

**Prioridade:** Alta  
**Dependências:** RD-001, RD-003

---

---

## REQUISITOS DE INTERFACE

### RI-001 - Menu Principal
**Descrição:** O sistema deve fornecer menu principal organizado por contexto.  
**Critérios de Aceitação:**
- **Menu Desenvolvedor:**
  - Cadastrar Desenvolvedor
  - Editar Desenvolvedor
  - Deletar Desenvolvedor
- **Menu História:**
  - Cadastrar História
  - Editar História
  - Deletar História
  - Importar Histórias
  - Filtrar Histórias
- **Menu Geral:**
  - Configurações
- Todos os itens devem ser acessíveis via mouse
- Cada item deve executar a ação correspondente  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RI-002 - Tabela de Backlog
**Descrição:** O sistema deve exibir o backlog em formato de tabela com colunas específicas.  
**Critérios de Aceitação:**
- Colunas obrigatórias na ordem: Prioridade, ID, Feature, Nome, Status, Desenvolvedor, Dependências, Story Point, Início, Fim, Duração
- Cabeçalhos devem ser fixos (não rolar com o conteúdo)
- Deve permitir seleção de linha única
- Deve permitir ordenação visual (não altera dados, apenas exibição)
- Deve suportar edição inline (RF-020)
- Deve atualizar automaticamente quando dados mudarem  

**Prioridade:** Alta  
**Dependências:** RF-004

---

### RI-003 - Barra de Ferramentas
**Descrição:** O sistema deve fornecer barra de ferramentas com ações rápidas.  
**Critérios de Aceitação:**
- Botão "Mover para Cima" (ícone seta para cima)
- Botão "Mover para Baixo" (ícone seta para baixo)
- Botão "Calcular Cronograma"
- Botão "Exportar para Excel"
- Botão "Timeline/Roadmap"
- Botões devem ser habilitados/desabilitados conforme contexto
- Deve exibir tooltips ao passar o mouse  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RI-004 - Atalhos de Teclado
**Descrição:** O sistema deve fornecer atalhos de teclado para ações frequentes.  
**Critérios de Aceitação:**
- **Delete**: Deletar história selecionada
- **Ctrl+D**: Duplicar história selecionada
- **Ctrl+Up**: Mover história para cima
- **Ctrl+Down**: Mover história para baixo
- **F5**: Recalcular cronograma
- **Ctrl+E**: Exportar para Excel
- Atalhos devem funcionar quando a tabela está em foco
- Deve exibir lista de atalhos acessível via menu Ajuda  

**Prioridade:** Média  
**Dependências:** RF-003, RF-012, RF-013, RF-014, RF-017

---

### RI-005 - Formulário de Cadastro/Edição de História
**Descrição:** O sistema deve fornecer formulário dedicado para cadastro e edição de histórias.  
**Critérios de Aceitação:**
- Campos: Feature, Nome, Story Point, Status, Desenvolvedor, Dependências, Prioridade
- Story Point deve ser dropdown com valores: 3, 5, 8, 13
- Status deve ser dropdown com valores do enum
- Desenvolvedor deve ser dropdown com lista de desenvolvedores cadastrados + opção "Nenhum"
- Dependências deve permitir múltipla seleção de histórias existentes
- Botões: Salvar, Cancelar
- Deve validar campos obrigatórios antes de salvar  

**Prioridade:** Alta  
**Dependências:** RF-001, RF-002

---

### RI-006 - Formulário de Cadastro/Edição de Desenvolvedor
**Descrição:** O sistema deve fornecer formulário dedicado para cadastro e edição de desenvolvedores.  
**Critérios de Aceitação:**
- Campo: Nome
- Botões: Salvar, Cancelar
- Deve validar que o nome não esteja vazio
- Em modo edição, deve exibir o ID (não editável)  

**Prioridade:** Alta  
**Dependências:** RF-007, RF-008

---

### RI-007 - Tela de Configurações
**Descrição:** O sistema deve fornecer tela dedicada para configurações globais.  
**Critérios de Aceitação:**
- Campos: Story Points por Sprint, Dias Úteis por Sprint
- Deve exibir em tempo real: Velocidade por Dia (calculada)
- Botões: Salvar, Cancelar, Restaurar Padrões
- Deve validar que valores sejam números positivos
- Deve exibir valores atuais ao abrir  

**Prioridade:** Alta  
**Dependências:** RF-019

---

### RI-008 - Visualização Timeline/Roadmap
**Descrição:** O sistema deve fornecer interface de visualização tipo Gantt ou Timeline.  
**Critérios de Aceitação:**
- Eixo horizontal: Datas (escala de dias/semanas)
- Eixo vertical: Histórias agrupadas por desenvolvedor
- Barras horizontais representando duração de cada história
- Cores distintas por desenvolvedor
- Tooltips exibindo: ID, Nome, Desenvolvedor, Story Point, Início, Fim
- Navegação horizontal por scroll ou botões
- Botão "Voltar para Tabela"  

**Prioridade:** Média  
**Dependências:** RF-021

---

---

## REQUISITOS NÃO-FUNCIONAIS

### RNF-001 - Executável Standalone
**Descrição:** O sistema deve ser distribuído como executável único que não requer instalação de dependências.  
**Critérios de Aceitação:**
- Deve ser empacotado usando PyInstaller
- Não deve requerer instalação de Python ou bibliotecas adicionais
- Não deve requerer conexão com internet para funcionar
- Deve incluir todas as dependências embarcadas
- Deve funcionar em sistemas Windows sem instalação prévia de software  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RNF-002 - Compatibilidade com Windows
**Descrição:** O sistema deve ser totalmente compatível com sistemas operacionais Windows.  
**Critérios de Aceitação:**
- Deve funcionar em Windows 10 ou superior
- Deve seguir convenções de interface do Windows
- Deve utilizar caminhos de arquivo compatíveis com Windows
- Não deve apresentar erros específicos de plataforma  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RNF-003 - Tempo de Resposta
**Descrição:** O sistema deve executar operações em tempo aceitável para boa experiência do usuário.  
**Critérios de Aceitação:**
- Cálculo de cronograma para até 100 histórias: máximo 2 segundos
- Operações de CRUD (Create, Read, Update, Delete): máximo 500ms
- Edição inline na tabela: resposta imediata (< 100ms)
- Exportação para Excel: máximo 3 segundos para 100 histórias
- Interface deve permanecer responsiva durante processamento  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RNF-004 - Persistência de Dados
**Descrição:** O sistema deve armazenar todos os dados de forma persistente em banco de dados local.  
**Critérios de Aceitação:**
- Deve utilizar SQLite como banco de dados
- Arquivo do banco deve ser criado automaticamente no primeiro uso
- Arquivo do banco deve estar localizado na mesma pasta do executável
- Dados devem persistir entre sessões da aplicação
- Não deve haver perda de dados ao fechar a aplicação normalmente  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RNF-005 - Usabilidade
**Descrição:** O sistema deve fornecer interface intuitiva e fácil de usar.  
**Critérios de Aceitação:**
- Interface deve seguir padrões de design consistentes
- Mensagens de erro devem ser claras e orientar o usuário
- Formulários devem ter validação em tempo real
- Deve fornecer feedback visual para todas as ações
- Cores e ícones devem seguir convenções (verde=sucesso, vermelho=erro, etc.)  

**Prioridade:** Média  
**Dependências:** Nenhuma

---

---

## REQUISITOS DE QUALIDADE

### RQ-001 - Arquitetura Limpa
**Descrição:** O código deve seguir rigorosamente os princípios da Clean Architecture.  
**Critérios de Aceitação:**
- Camada de Domínio: Entidades e regras de negócio, sem dependências externas
- Camada de Aplicação: Casos de uso, orquestra domínio e infraestrutura
- Camada de Infraestrutura: Implementações concretas (banco de dados, UI)
- Camada de Interface: Controladores e adaptadores
- Dependências devem apontar sempre para dentro (Infraestrutura → Aplicação → Domínio)
- Nenhuma camada interna pode conhecer camadas externas  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RQ-002 - Testes Integrados Narrow
**Descrição:** O código deve implementar testes integrados narrow para a integração dos componentes.
**Critérios de Aceitação:**
- Testes de integração para casos de uso
- Testes devem ser automatizados e executáveis via comando

**Prioridade:** Alta  
**Dependências:** RQ-001

---

### RQ-003 - Qualidade de Código
**Descrição:** O código deve seguir boas práticas de desenvolvimento.  
**Critérios de Aceitação:**
- Nomes de variáveis, funções e classes em inglês
- Docstrings em português para todas as funções e classes públicas
- Código deve seguir PEP 8 (Python Style Guide)
- Complexidade ciclomática máxima de 10 por função
- Evitar duplicação de código (DRY - Don't Repeat Yourself)
- Funções devem ter responsabilidade única (SRP - Single Responsibility Principle)  

**Prioridade:** Alta  
**Dependências:** Nenhuma

---

### RQ-004 - Simplicidade
**Descrição:** O código deve priorizar simplicidade sobre complexidade desnecessária.  
**Critérios de Aceitação:**
- Evitar over-engineering e padrões complexos sem justificativa
- Preferir soluções diretas e legíveis
- Comentários devem explicar "por quê", não "o quê"
- Código deve ser auto-explicativo sempre que possível
- Evitar abstrações prematuras  

**Prioridade:** Média  
**Dependências:** Nenhuma

---

---

## GLOSSÁRIO

**Backlog:** Lista ordenada de histórias a serem desenvolvidas.

**História (User Story):** Unidade de trabalho que representa uma funcionalidade ou tarefa a ser implementada.

**Story Point (SP):** Medida relativa de esforço necessário para implementar uma história. Escala utilizada: 3 (P), 5 (M), 8 (G), 13 (GG).

**Dependência:** Relacionamento entre histórias onde uma história não pode ser iniciada antes que outra seja concluída.

**Dependência Cíclica:** Situação inválida onde um conjunto de histórias dependem umas das outras em formato circular.

**Prioridade:** Número inteiro que determina a ordem de execução de histórias quando não há restrições por dependências. Menor número = maior prioridade.

**Desenvolvedor:** Recurso humano que pode ser alocado para implementar histórias.

**Velocidade do Time:** Capacidade de entrega medida em Story Points por Sprint.

**Sprint:** Período fixo de tempo (ex: 2 semanas) usado para planejamento e medição de progresso.

**Dias Úteis:** Dias de trabalho efetivo, excluindo finais de semana e feriados (simplificado: segunda a sexta).

**Cronograma:** Plano temporal que define quando cada história será iniciada e concluída.

**Alocação:** Atribuição de um desenvolvedor específico a uma história.

**Timeline/Roadmap:** Visualização gráfica do cronograma ao longo do tempo.

**Feature:** Agrupamento lógico de histórias relacionadas (ex: Autenticação, Relatórios).

**Clean Architecture:** Arquitetura de software que promove separação de responsabilidades em camadas concêntricas.

**Inline Editing:** Capacidade de editar dados diretamente em uma célula de tabela sem abrir formulário separado.

**Round-Robin:** Estratégia de distribuição que aloca recursos de forma equilibrada e rotativa.

---

## PREMISSAS E RESTRIÇÕES

### Premissas
1. O usuário tem conhecimento básico de planejamento ágil e conceito de Story Points
2. O time trabalha de segunda a sexta (5 dias úteis por semana)
3. A velocidade do time é relativamente estável ao longo do tempo
4. Desenvolvedores têm capacidade similar de entrega
5. Uma história é atribuída a apenas um desenvolvedor por vez
6. O sistema será usado por times de até 10 desenvolvedores e backlogs de até 100 histórias
7. Windows 10 ou superior está instalado na máquina do usuário
8. Microsoft Excel está instalado para visualizar arquivos exportados

### Restrições
1. **Tecnológica:** Deve ser desenvolvido em Python
2. **Plataforma:** Funciona apenas em Windows
3. **Banco de Dados:** Deve usar SQLite (sem servidor de banco de dados)
4. **Empacotamento:** Deve usar PyInstaller
5. **Interface:** Desktop (não é aplicação web)
6. **Performance:** Máximo 2 segundos para cálculo de cronograma com 100 histórias
7. **Arquitetura:** Deve seguir Clean Architecture estritamente
8. **Idioma:** Código em inglês, docstrings em português
9. **Offline:** Não requer conexão com internet

---

## MATRIZ DE RASTREABILIDADE

### Dependências de Requisitos Funcionais

| Requisito | Depende de | Impacta em |
|-----------|-----------|------------|
| RF-001 | RD-001 | RF-002, RF-003, RF-004, RF-005, RF-010, RF-012, RF-013, RF-016, RF-018, RF-020 |
| RF-002 | RF-001, RD-001 | RF-015, RF-020 |
| RF-003 | RF-001, RF-005 | - |
| RF-004 | RF-001, RF-014 | RF-017, RF-018, RI-002 |
| RF-005 | RF-001, RD-001 | RF-003, RF-006, RF-014 |
| RF-006 | RF-005 | - |
| RF-007 | RD-002 | RF-008, RF-009, RF-010, RF-011 |
| RF-008 | RF-007, RD-002 | - |
| RF-009 | RF-007 | - |
| RF-010 | RF-001, RF-007, RF-014 | RF-015 |
| RF-011 | RF-001, RF-007, RF-014 | - |
| RF-012 | RF-001, RF-014 | RF-015 |
| RF-013 | RF-001 | - |
| RF-014 | RF-001, RF-005, RF-007, RNF-003 | RF-010, RF-011, RF-012, RF-015, RF-021 |
| RF-015 | RF-002, RF-010, RF-012, RF-014 | - |
| RF-016 | RF-001 | - |
| RF-017 | RF-004 | - |
| RF-018 | RF-004 | - |
| RF-019 | RF-014, RD-003 | - |
| RF-020 | RF-002, RF-015, RI-002 | - |
| RF-021 | RF-014 | - |

### Dependências entre Requisitos de Dados

| Requisito | Depende de |
|-----------|-----------|
| RD-001 | - |
| RD-002 | - |
| RD-003 | - |
| RD-004 | RD-001 |
| RD-005 | RD-001, RD-003 |

### Dependências de Requisitos de Interface

| Requisito | Depende de |
|-----------|-----------|
| RI-001 | - |
| RI-002 | RF-004 |
| RI-003 | - |
| RI-004 | RF-003, RF-012, RF-013, RF-014, RF-017 |
| RI-005 | RF-001, RF-002 |
| RI-006 | RF-007, RF-008 |
| RI-007 | RF-019 |
| RI-008 | RF-021 |

---

## CASO DE USO PRINCIPAL

**Título:** Planejamento Completo de Backlog

**Ator Principal:** Gerente de Projeto / Scrum Master

**Pré-condições:**
- Sistema instalado e executando
- Planilha Excel com histórias preparada (colunas: Feature, Nome, StoryPoint)
- Lista de desenvolvedores do time disponível

**Fluxo Principal:**

1. Usuário inicia a aplicação
2. Sistema exibe tela principal com tabela de backlog vazia
3. Usuário acessa Menu História → Importar Histórias
4. Sistema exibe diálogo de seleção de arquivo
5. Usuário seleciona arquivo Excel e confirma
6. Sistema valida o arquivo e importa as histórias
7. Sistema exibe mensagem: "15 histórias importadas com sucesso"
8. Sistema atualiza tabela de backlog com histórias importadas
9. Usuário acessa Menu Desenvolvedor → Cadastrar Desenvolvedor
10. Sistema exibe formulário de cadastro
11. Usuário preenche nome "Gabriela" e confirma
12. Sistema gera ID "GA" e salva desenvolvedor
13. Usuário repete passos 9-12 para cadastrar "Lucas" (ID: LU) e "Marina" (ID: MA)
14. Usuário clica no botão "Calcular Cronograma" na barra de ferramentas
15. Sistema executa algoritmo de ordenação considerando dependências e prioridades
16. Sistema aloca desenvolvedores automaticamente usando estratégia round-robin
17. Sistema calcula datas de início, fim e duração para cada história
18. Sistema atualiza tabela de backlog com todas as informações calculadas
19. Sistema exibe mensagem: "Cronograma calculado com sucesso"
20. Usuário revisa o backlog ordenado e alocado
21. Usuário clica no botão "Exportar para Excel"
22. Sistema exibe diálogo para salvar arquivo
23. Usuário escolhe local e nome "Backlog_Planejado_2025.xlsx"
24. Sistema gera arquivo Excel com todos os dados
25. Sistema exibe mensagem: "Arquivo exportado para C:\Users\...\Backlog_Planejado_2025.xlsx"

**Pós-condições:**
- Backlog completo está ordenado, com desenvolvedores alocados e cronograma calculado
- Dados estão persistidos no banco de dados
- Arquivo Excel com cronograma completo foi gerado

**Fluxos Alternativos:**

**FA1 - Erro na Importação (após passo 6)**
- 6a. Sistema detecta que arquivo não possui colunas obrigatórias
- 6b. Sistema exibe mensagem: "Erro: A planilha deve conter as colunas Feature, Nome e StoryPoint"
- 6c. Retorna ao passo 3

**FA2 - Ajuste Manual de Prioridade (após passo 20)**
- 20a. Usuário identifica que história H-15 deveria ter prioridade maior
- 20b. Usuário seleciona história H-15 na tabela
- 20c. Usuário clica 3 vezes no botão "Mover para Cima"
- 20d. Sistema ajusta prioridade e recalcula cronograma automaticamente
- 20e. Continua no passo 21

**FA3 - Alocação Manual Específica (após passo 20)**
- 20a. Usuário identifica que história H-7 deve ser feita especificamente por "Gabriela"
- 20b. Usuário clica duas vezes na célula "Desenvolvedor" da linha H-7
- 20c. Sistema habilita modo de edição inline
- 20d. Usuário seleciona "GA - Gabriela" do dropdown
- 20e. Sistema salva alteração e recalcula cronograma automaticamente
- 20f. Continua no passo 21

**Requisitos Relacionados:**
- RF-001, RF-007, RF-010, RF-011, RF-012, RF-014, RF-016, RF-017, RF-020
- RI-001, RI-002, RI-003
- RNF-003, RNF-004

---

## SUGESTÕES DE MELHORIAS ARQUITETURAIS

### 1. Padrão Repository
Implementar Repository Pattern para abstração de acesso a dados:
- `HistoryRepository`: CRUD de histórias
- `DeveloperRepository`: CRUD de desenvolvedores
- `ConfigurationRepository`: Gestão de configurações

**Benefício:** Facilita troca de banco de dados e testes unitários com mock.

### 2. Padrão Observer para Recálculo Reativo
Implementar Observer Pattern para reação automática a mudanças:
- Histórias observam mudanças em SP, Prioridade, Desenvolvedor
- Quando detectada mudança, notifica `ScheduleCalculator`
- `ScheduleCalculator` executa recálculo automaticamente

**Benefício:** Desacopla lógica de interface e domínio, facilita manutenção.

### 3. Command Pattern para Operações Reversíveis
Implementar Command Pattern para ações do usuário:
- Cada ação (editar, mover, deletar) encapsulada em Command
- Permite implementação futura de Undo/Redo

**Benefício:** Maior controle sobre operações e possibilidade de auditoria.

### 4. Strategy Pattern para Algoritmos de Ordenação
Separar algoritmos de ordenação em strategies distintas:
- `DependencyFirstStrategy`: Ordena por dependências
- `PriorityStrategy`: Ordena por prioridade
- `CompositeStrategy`: Combina ambas

**Benefício:** Facilita adição de novos critérios de ordenação.

### 5. Validação com Chain of Responsibility
Implementar cadeia de validadores:
- `CyclicDependencyValidator`
- `StoryPointValidator`
- `DeveloperExistsValidator`

**Benefício:** Validações modulares e reutilizáveis.

### 6. Camada de Serviço para Casos de Uso Complexos
Criar serviços de aplicação dedicados:
- `ScheduleCalculationService`
- `DeveloperAllocationService`
- `BacklogOrderingService`

**Benefício:** Separa orquestração complexa de regras de domínio simples.

---

**Fim da Especificação de Requisitos**
