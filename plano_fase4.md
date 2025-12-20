# FASE 4: Interface Gráfica (Apresentação)

## 🎯 VISÃO GERAL DA FASE

### Objetivo Principal
Implementar a camada de apresentação completa do sistema, criando uma interface desktop profissional e intuitiva que permita aos usuários interagir com todas as funcionalidades do backlog manager através de componentes visuais eficientes e uma experiência tipo Excel para gestão de histórias.

### Contexto
Com as três primeiras fases concluídas (Domínio, Aplicação e Infraestrutura), temos uma base sólida de regras de negócio, casos de uso e persistência de dados. A Fase 4 conecta toda essa lógica a uma interface gráfica desktop, seguindo os princípios de Clean Architecture onde a camada de apresentação depende apenas da camada de aplicação.

### Tecnologias Principais
- **Framework UI:** PySide6 ou PyQt6 (Recomendação: PySide6 por flexibilidade de licença LGPL)
- **Arquitetura UI:** MVC (Model-View-Controller) com ViewModels
- **Componentes:** QMainWindow, QTableWidget customizado, QDialog, QMenuBar, QToolBar
- **Estilos:** QSS (Qt Style Sheets) para personalização visual

### Métricas de Sucesso
- ✅ Todas operações CRUD funcionam via interface gráfica
- ✅ Edição inline na tabela com validações em tempo real
- ✅ Performance: Edição inline < 100ms, operações < 500ms
- ✅ UX intuitiva e responsiva, similar a ferramentas desktop profissionais
- ✅ Zero acoplamento entre UI e camadas inferiores (apenas via Application)
- ✅ Interface testável e manutenível

---

## 📊 ESTIMATIVAS

| Métrica | Valor |
|---------|-------|
| **Story Points Totais** | 34 SP |
| **Duração Estimada** | 3 semanas |
| **Subtarefas** | 6 grandes tarefas |
| **Arquivos Novos** | ~15-20 arquivos Python |
| **Testes** | ~40-50 testes de UI |
| **Cobertura Alvo** | ≥ 85% |

---

## 🏗️ ARQUITETURA DA CAMADA DE APRESENTAÇÃO

### Estrutura de Diretórios

```
backlog_manager/presentation/
├── __init__.py
├── views/                          # Componentes visuais (Views)
│   ├── __init__.py
│   ├── main_window.py              # Janela principal da aplicação
│   ├── story_form.py               # Formulário de criação/edição de história
│   ├── developer_form.py           # Formulário de desenvolvedor
│   ├── configuration_dialog.py     # Diálogo de configurações
│   └── widgets/                    # Widgets customizados reutilizáveis
│       ├── __init__.py
│       ├── editable_table.py       # Tabela editável tipo Excel
│       ├── story_point_delegate.py # Delegate para Story Points
│       ├── status_delegate.py      # Delegate para Status
│       ├── developer_delegate.py   # Delegate para Desenvolvedor
│       └── toolbar.py              # Barra de ferramentas customizada
├── controllers/                    # Controladores (Lógica de coordenação)
│   ├── __init__.py
│   ├── main_controller.py          # Controlador principal
│   ├── story_controller.py         # Controlador de histórias
│   ├── developer_controller.py     # Controlador de desenvolvedores
│   └── schedule_controller.py      # Controlador de cronograma
├── view_models/                    # ViewModels (Adaptadores de dados)
│   ├── __init__.py
│   ├── story_table_model.py        # Modelo de dados para tabela
│   └── backlog_view_model.py       # ViewModel do backlog completo
├── styles/                         # Estilos visuais
│   ├── app_styles.qss              # Qt Style Sheet principal
│   └── themes.py                   # Constantes de cores e temas
└── utils/                          # Utilitários de UI
    ├── __init__.py
    ├── message_box.py              # Sistema de mensagens centralizado
    └── validators.py               # Validadores de UI
```

### Princípios Arquiteturais da Camada

**1. Separação de Responsabilidades**
- **Views:** Apenas renderização e captura de eventos do usuário
- **Controllers:** Orquestração entre Views e Use Cases, lógica de apresentação
- **ViewModels:** Adaptação de dados do domínio para formato consumível pela UI

**2. Fluxo de Dados**
```
User Interaction → View → Controller → Use Case → Repository → Database
                    ↑                       ↓
                    ← ViewModel ← DTO ← Result
```

**3. Inversão de Dependência**
```python
# Controller depende de interfaces de Application, nunca de Domain
class StoryController:
    def __init__(
        self,
        create_story_use_case: CreateStoryUseCase,
        update_story_use_case: UpdateStoryUseCase,
        # ...
    ):
        # Dependências injetadas
```

**4. Comunicação via Sinais Qt**
```python
# View emite sinais
class MainWindow(QMainWindow):
    story_created = pyqtSignal(dict)  # Sinal de história criada

    def on_create_story(self):
        self.story_created.emit(form_data)

# Controller conecta sinais
controller.connect_view_signals(main_window)
```

---

## 📋 TAREFAS DETALHADAS

### 4.1 Setup PySide6/PyQt6 e Janela Principal (3 SP)

#### Objetivo
Configurar o ambiente gráfico, criar a janela principal da aplicação e estabelecer a estrutura base da interface, incluindo menu, toolbar e layout principal.

#### Subtarefas

**4.1.1 Configuração de Ambiente**
- [ ] Adicionar PySide6 (ou PyQt6) ao `requirements.txt`
- [ ] Verificar compatibilidade com Python 3.11+
- [ ] Testar importação básica: `from PySide6.QtWidgets import QApplication`
- [ ] Documentar escolha de framework (PySide6 vs PyQt6) e justificativa

**4.1.2 Ponto de Entrada da Aplicação**
- [ ] Criar `main.py` na raiz do projeto
- [ ] Implementar inicialização do QApplication
- [ ] Configurar aplicação para Windows (ícone, nome, versão)
- [ ] Implementar tratamento de exceções global
```python
# main.py
import sys
from PySide6.QtWidgets import QApplication
from backlog_manager.presentation.views.main_window import MainWindow
from backlog_manager.presentation.controllers.main_controller import MainController

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Backlog Manager")
    app.setApplicationVersion("1.0.0")

    # Dependency injection setup
    main_controller = MainController(
        # Inject use cases...
    )

    main_window = MainWindow()
    main_controller.connect_view(main_window)

    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**4.1.3 Criar MainWindow (Janela Principal)**
- [ ] Criar classe `MainWindow` herdando de `QMainWindow`
- [ ] Definir tamanho inicial: 1280x720 (mínimo: 1024x600)
- [ ] Implementar layout principal com `QVBoxLayout`
- [ ] Criar widget central para conter a tabela de backlog
- [ ] Configurar título da janela: "Backlog Manager - [Nome do Projeto]"
- [ ] Adicionar ícone da janela (criar arquivo `icon.png` em `resources/`)
- [ ] Implementar método `closeEvent` para confirmação de fechamento

**4.1.4 Menu Principal**
- [ ] Criar `QMenuBar` com os seguintes menus:
  - **Menu "Arquivo"**
    - Importar Excel (Ctrl+I)
    - Exportar Excel (Ctrl+E)
    - Separador
    - Sair (Alt+F4)
  - **Menu "História"**
    - Nova História (Ctrl+N)
    - Editar História (Ctrl+E ou Enter)
    - Duplicar História (Ctrl+D)
    - Deletar História (Delete)
    - Separador
    - Mover para Cima (Ctrl+Up)
    - Mover para Baixo (Ctrl+Down)
  - **Menu "Desenvolvedor"**
    - Novo Desenvolvedor (Ctrl+Shift+N)
    - Editar Desenvolvedor
    - Deletar Desenvolvedor
  - **Menu "Cronograma"**
    - Calcular Cronograma (F5)
    - Alocar Desenvolvedores
  - **Menu "Configurações"**
    - Configurações do Sistema (Ctrl+,)
  - **Menu "Ajuda"**
    - Atalhos de Teclado (F1)
    - Sobre

**4.1.5 Barra de Ferramentas**
- [ ] Criar `QToolBar` com botões principais:
  - Botão "Nova História" (ícone +)
  - Botão "Editar História" (ícone lápis)
  - Botão "Deletar História" (ícone lixeira)
  - Separador
  - Botão "Importar Excel" (ícone documento)
  - Botão "Exportar Excel" (ícone salvar)
  - Separador
  - Botão "Calcular Cronograma" (ícone calendário)
- [ ] Adicionar tooltips descritivos em cada botão
- [ ] Configurar ícones (usar ícones do Qt ou criar SVGs simples)
- [ ] Tornar toolbar destacável e posicionável

**4.1.6 Barra de Status**
- [ ] Criar `QStatusBar` para mensagens temporárias
- [ ] Implementar método `show_message(text, timeout=3000)`
- [ ] Adicionar indicador de "Pronto" quando idle
- [ ] Adicionar contador de histórias no canto direito

**4.1.7 Estilos Básicos (QSS)**
- [ ] Criar arquivo `presentation/styles/app_styles.qss`
- [ ] Definir paleta de cores:
  - Primária: #2196F3 (azul)
  - Secundária: #4CAF50 (verde)
  - Erro: #F44336 (vermelho)
  - Warning: #FF9800 (laranja)
  - Background: #FAFAFA
  - Texto: #212121
- [ ] Estilizar menu e toolbar
- [ ] Aplicar estilos à janela principal: `app.setStyleSheet(qss_content)`

**4.1.8 Testes Iniciais**
- [ ] Testar abertura da aplicação (janela aparece)
- [ ] Verificar menu e toolbar renderizam corretamente
- [ ] Testar atalhos de teclado básicos
- [ ] Verificar responsividade ao redimensionar janela

#### Critérios de Aceitação
- [x] Aplicação abre sem erros
- [x] Janela principal possui menu, toolbar e status bar
- [x] Menus organizados logicamente com atalhos funcionais
- [x] Interface segue convenções desktop (Windows)
- [x] Estilos básicos aplicados e visualmente consistentes

#### Arquivos Criados
- `main.py`
- `backlog_manager/presentation/__init__.py`
- `backlog_manager/presentation/views/__init__.py`
- `backlog_manager/presentation/views/main_window.py`
- `backlog_manager/presentation/styles/app_styles.qss`
- `backlog_manager/presentation/styles/themes.py`

---

### 4.2 Tabela de Backlog Editável (13 SP)

#### Objetivo
Criar o componente mais crítico da interface: uma tabela editável tipo Excel que permita visualizar e editar histórias inline com validações em tempo real, feedback visual e performance otimizada.

#### Contexto
Esta é a tarefa mais complexa da fase, pois requer implementação de delegates customizados, validações síncronas, sincronização com o banco de dados e experiência de usuário fluida. A tabela será o principal ponto de interação do sistema.

#### Subtarefas

**4.2.1 Criar Widget EditableTableWidget Base**
- [ ] Criar classe `EditableTableWidget` herdando de `QTableWidget`
- [ ] Configurar propriedades da tabela:
  - `setAlternatingRowColors(True)` para melhor legibilidade
  - `setSelectionBehavior(QAbstractItemView.SelectRows)`
  - `setSelectionMode(QAbstractItemView.SingleSelection)`
  - `setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)`
  - `setSortingEnabled(False)` (ordenação manual por prioridade)
- [ ] Configurar cabeçalhos verticais (números de linha)
- [ ] Implementar método `setup_columns()` para definir estrutura

**4.2.2 Definir Estrutura de Colunas**
- [ ] Implementar 11 colunas conforme especificação:

  | # | Coluna | Tipo | Largura | Editável | Descrição |
  |---|--------|------|---------|----------|-----------|
  | 0 | Prioridade | int | 80px | ❌ | Calculada automaticamente |
  | 1 | ID | str | 60px | ❌ | Gerado automaticamente |
  | 2 | Feature | str | 120px | ✅ | Texto livre |
  | 3 | Nome | str | 250px | ✅ | Texto livre |
  | 4 | Status | enum | 100px | ✅ | Dropdown com StatusDelegate |
  | 5 | Desenvolvedor | str | 120px | ✅ | Dropdown com DeveloperDelegate |
  | 6 | Dependências | list | 150px | ✅ | Dialog de seleção múltipla |
  | 7 | Story Point | int | 80px | ✅ | Dropdown (3, 5, 8, 13) |
  | 8 | Início | date | 100px | ❌ | Calculada |
  | 9 | Fim | date | 100px | ❌ | Calculada |
  | 10 | Duração | int | 80px | ❌ | Calculada |

- [ ] Implementar método `populate_from_stories(stories: List[StoryDTO])`
- [ ] Configurar larguras de coluna e política de redimensionamento

**4.2.3 Implementar Delegates Customizados**

**A. StoryPointDelegate**
- [ ] Criar classe `StoryPointDelegate(QStyledItemDelegate)`
- [ ] Implementar `createEditor()` retornando `QComboBox`
- [ ] Popular combobox com valores [3, 5, 8, 13]
- [ ] Implementar `setEditorData()` e `setModelData()`
- [ ] Validar que apenas valores válidos são aceitos

**B. StatusDelegate**
- [ ] Criar classe `StatusDelegate(QStyledItemDelegate)`
- [ ] Implementar combobox com valores de `StoryStatus`
- [ ] Aplicar cores por status:
  - BACKLOG: Azul (#2196F3)
  - EXECUÇÃO: Laranja (#FF9800)
  - TESTES: Roxo (#9C27B0)
  - CONCLUÍDO: Verde (#4CAF50)
  - IMPEDIDO: Vermelho (#F44336)
- [ ] Implementar validação de transição de status (se necessário)

**C. DeveloperDelegate**
- [ ] Criar classe `DeveloperDelegate(QStyledItemDelegate)`
- [ ] Implementar combobox populado dinamicamente de `list_developers_use_case`
- [ ] Adicionar opção "(Nenhum)" para remover desenvolvedor
- [ ] Implementar refresh quando lista de desenvolvedores muda

**D. DependenciesDelegate** (Mais complexo)
- [ ] Criar classe `DependenciesDelegate(QStyledItemDelegate)`
- [ ] Ao editar, abrir `DependenciesDialog` customizado
- [ ] Dialog contém:
  - Lista de histórias disponíveis (exceto atual)
  - Checkboxes para seleção múltipla
  - Validação de ciclos em tempo real usando `CycleDetector`
  - Mensagem de erro se ciclo detectado
- [ ] Exibir dependências como texto: "S1, S2, A3"

**4.2.4 Implementar Edição Inline**
- [ ] Conectar delegates às colunas apropriadas: `setItemDelegateForColumn()`
- [ ] Implementar validação em tempo real no evento `itemChanged`
- [ ] Bloquear edição de colunas calculadas (ID, Prioridade, Datas)
- [ ] Implementar feedback visual durante edição:
  - Célula em edição: borda azul destacada
  - Erro de validação: borda vermelha + tooltip com mensagem
  - Salvamento bem-sucedido: flash verde temporário (200ms)

**4.2.5 Sincronização com Controller**
- [ ] Implementar sinal `story_changed(story_id: str, field: str, new_value: Any)`
- [ ] Conectar sinal ao `StoryController.on_story_field_changed()`
- [ ] Controller chama `UpdateStoryUseCase` para persistir mudança
- [ ] Se mudança requer recálculo (SP, Dev, Dependências):
  - Mostrar indicador de recalculando na status bar
  - Chamar `CalculateScheduleUseCase` assincronamente
  - Atualizar tabela com novos valores calculados

**4.2.6 Feedback Visual e UX**
- [ ] Implementar cores alternadas de linhas (cinza claro/branco)
- [ ] Adicionar highlight de linha selecionada
- [ ] Implementar cores por status na coluna Status
- [ ] Adicionar indicador visual de história com dependências (ícone na coluna)
- [ ] Implementar tooltip em cada célula mostrando valor completo
- [ ] Adicionar ícone de "loading" em células durante recálculo

**4.2.7 Menu de Contexto (Clique Direito)**
- [ ] Implementar `contextMenuEvent()`
- [ ] Criar menu com opções:
  - Editar História
  - Duplicar História
  - Deletar História
  - Separador
  - Mover para Cima
  - Mover para Baixo
  - Separador
  - Ver Dependências
  - Adicionar Dependência
  - Remover Dependência
- [ ] Conectar ações ao controller apropriado

**4.2.8 Performance e Otimizações**
- [ ] Implementar virtual scrolling se > 100 histórias
- [ ] Desabilitar sorting durante edições em massa
- [ ] Usar `blockSignals(True/False)` para evitar updates desnecessários
- [ ] Implementar debouncing de 300ms para recálculo automático
- [ ] Medir tempo de edição: deve ser < 100ms

**4.2.9 Testes de Tabela**
- [ ] Testar população inicial da tabela com 10 histórias
- [ ] Testar edição de cada tipo de coluna (Feature, Nome, Status, etc.)
- [ ] Testar validação de Story Point (apenas 3, 5, 8, 13)
- [ ] Testar validação de dependências (detecção de ciclo)
- [ ] Testar que colunas não-editáveis realmente bloqueiam edição
- [ ] Testar sincronização com banco de dados
- [ ] Testar performance com 100 histórias
- [ ] Testar menu de contexto
- [ ] Testar feedback visual (cores, tooltips)

#### Critérios de Aceitação
- [x] Tabela exibe todas as histórias com 11 colunas
- [x] Edição inline funciona em colunas editáveis
- [x] Validações bloqueiam valores inválidos com mensagens claras
- [x] Mudanças persistem no banco de dados
- [x] Recálculo automático dispara quando necessário
- [x] Feedback visual claro (cores, estados, loading)
- [x] Performance < 100ms para edições
- [x] Menu de contexto funcional
- [x] Interface intuitiva, similar a Excel

#### Arquivos Criados
- `backlog_manager/presentation/views/widgets/editable_table.py`
- `backlog_manager/presentation/views/widgets/story_point_delegate.py`
- `backlog_manager/presentation/views/widgets/status_delegate.py`
- `backlog_manager/presentation/views/widgets/developer_delegate.py`
- `backlog_manager/presentation/views/widgets/dependencies_delegate.py`
- `backlog_manager/presentation/views/widgets/dependencies_dialog.py`
- `tests/unit/presentation/test_editable_table.py`
- `tests/unit/presentation/test_delegates.py`

---

### 4.3 Formulários de CRUD (8 SP)

#### Objetivo
Criar formulários (dialogs) completos para operações CRUD de histórias, desenvolvedores e configurações, com validações, feedback visual e integração com controllers.

#### Subtarefas

**4.3.1 StoryFormDialog - Formulário de História**

**A. Estrutura Base**
- [ ] Criar classe `StoryFormDialog(QDialog)`
- [ ] Implementar dois modos: CREATE e EDIT
- [ ] Definir tamanho: 600x500, modal
- [ ] Implementar título dinâmico: "Nova História" ou "Editar História - {ID}"

**B. Campos do Formulário**
- [ ] Implementar layout com `QFormLayout`:

  ```python
  # Campo ID (apenas em modo EDIT, read-only)
  self.id_label = QLabel()

  # Campo Feature (QLineEdit)
  self.feature_input = QLineEdit()
  self.feature_input.setPlaceholderText("Ex: Login, Dashboard")

  # Campo Nome (QLineEdit)
  self.name_input = QLineEdit()
  self.name_input.setPlaceholderText("Ex: Implementar tela de login")

  # Campo Story Point (QComboBox)
  self.story_point_combo = QComboBox()
  self.story_point_combo.addItems(["3", "5", "8", "13"])

  # Campo Status (QComboBox)
  self.status_combo = QComboBox()
  self.status_combo.addItems([status.value for status in StoryStatus])

  # Campo Desenvolvedor (QComboBox)
  self.developer_combo = QComboBox()
  self.developer_combo.addItem("(Nenhum)", None)
  # Popular com desenvolvedores do use case

  # Campo Prioridade (QSpinBox)
  self.priority_spin = QSpinBox()
  self.priority_spin.setRange(1, 1000)

  # Campo Dependências (Widget customizado)
  self.dependencies_widget = DependenciesListWidget()

  # Campos calculados (read-only, apenas modo EDIT)
  self.start_date_label = QLabel()
  self.end_date_label = QLabel()
  self.duration_label = QLabel()
  ```

**C. Validações em Tempo Real**
- [ ] Implementar validação de Feature (não vazio, sem caracteres especiais)
- [ ] Implementar validação de Nome (não vazio, min 5 caracteres)
- [ ] Desabilitar botão "Salvar" se campos inválidos
- [ ] Mostrar mensagens de erro abaixo de campos inválidos

**D. Integração com Controller**
- [ ] Implementar método `populate_from_story(story: StoryDTO)` para modo EDIT
- [ ] Implementar método `get_form_data() -> dict`
- [ ] Emitir sinais:
  - `story_created(story_data: dict)`
  - `story_updated(story_id: str, story_data: dict)`

**E. Botões de Ação**
- [ ] Implementar botões: "Salvar" e "Cancelar"
- [ ] Atalhos: Enter para salvar, Esc para cancelar
- [ ] Confirmação se houver dados não salvos ao cancelar

**F. Testes de StoryFormDialog**
- [ ] Testar modo CREATE (campos vazios, salvar cria história)
- [ ] Testar modo EDIT (campos populados, salvar atualiza)
- [ ] Testar validações bloqueiam salvamento
- [ ] Testar integração com controller

---

**4.3.2 DeveloperFormDialog - Formulário de Desenvolvedor**

**A. Estrutura Base**
- [ ] Criar classe `DeveloperFormDialog(QDialog)`
- [ ] Modos: CREATE e EDIT
- [ ] Tamanho: 400x200, modal

**B. Campos**
- [ ] Campo ID (read-only em modo EDIT)
- [ ] Campo Nome (QLineEdit)
- [ ] Explicação: "ID será gerado automaticamente" (modo CREATE)

**C. Validações**
- [ ] Nome não vazio (min 2 caracteres)
- [ ] Verificar unicidade de nome via use case
- [ ] Mostrar erro se nome já existe

**D. Integração**
- [ ] Sinais: `developer_created(name: str)`, `developer_updated(id: str, name: str)`
- [ ] Método `get_form_data() -> dict`

**E. Testes**
- [ ] Testar criação de desenvolvedor
- [ ] Testar edição de desenvolvedor
- [ ] Testar validação de unicidade

---

**4.3.3 ConfigurationDialog - Configurações do Sistema**

**A. Estrutura Base**
- [ ] Criar classe `ConfigurationDialog(QDialog)`
- [ ] Tamanho: 500x300, modal
- [ ] Título: "Configurações do Sistema"

**B. Campos**
```python
# Story Points por Sprint
self.sp_per_sprint_spin = QSpinBox()
self.sp_per_sprint_spin.setRange(1, 100)
self.sp_per_sprint_spin.setValue(21)  # Padrão

# Dias Úteis por Sprint
self.workdays_per_sprint_spin = QSpinBox()
self.workdays_per_sprint_spin.setRange(1, 30)
self.workdays_per_sprint_spin.setValue(15)  # Padrão

# Velocidade por Dia (calculada, read-only)
self.velocity_label = QLabel()
self.update_velocity_label()
```

**C. Cálculo Automático de Velocidade**
- [ ] Conectar sinais de mudança nos spinboxes
- [ ] Atualizar label de velocidade: `{sp_per_sprint / workdays_per_sprint:.2f} SP/dia`

**D. Botões**
- [ ] "Salvar" - aplica mudanças via `UpdateConfigurationUseCase`
- [ ] "Cancelar" - fecha sem salvar
- [ ] "Restaurar Padrões" - reseta para valores padrão (21 SP, 15 dias)

**E. Validações**
- [ ] Valores devem ser > 0
- [ ] Mostrar warning se velocidade muito baixa (< 0.5) ou muito alta (> 5)

**F. Testes**
- [ ] Testar carregamento de configurações atuais
- [ ] Testar salvamento de novas configurações
- [ ] Testar cálculo de velocidade
- [ ] Testar restauração de padrões

---

**4.3.4 Dialogs de Confirmação**
- [ ] Criar `ConfirmationDialog` genérico com tipos:
  - DELETE (vermelho, ícone de alerta)
  - WARNING (amarelo, ícone de aviso)
  - INFO (azul, ícone de informação)
- [ ] Implementar método estático `ConfirmationDialog.ask()`
- [ ] Exemplo de uso:
```python
if ConfirmationDialog.ask(
    parent=self,
    title="Deletar História",
    message=f"Tem certeza que deseja deletar a história '{story.name}'?",
    dialog_type=DialogType.DELETE
):
    controller.delete_story(story.id)
```

**4.3.5 Progress Dialog**
- [ ] Criar `ProgressDialog` para operações longas
- [ ] Implementar barra de progresso indeterminada
- [ ] Usar para:
  - Cálculo de cronograma
  - Importação de Excel
  - Exportação de Excel
- [ ] Permitir cancelamento de operações

#### Critérios de Aceitação
- [x] Todos os formulários abrem e renderizam corretamente
- [x] Validações impedem salvamento de dados inválidos
- [x] Feedback visual claro para erros
- [x] Integração com controllers funciona
- [x] Dados persistem corretamente
- [x] Dialogs de confirmação funcionam

#### Arquivos Criados
- `backlog_manager/presentation/views/story_form.py`
- `backlog_manager/presentation/views/developer_form.py`
- `backlog_manager/presentation/views/configuration_dialog.py`
- `backlog_manager/presentation/utils/message_box.py`
- `tests/unit/presentation/test_forms.py`

---

### 4.4 Controllers (5 SP)

#### Objetivo
Implementar a camada de controladores que orquestra a comunicação entre views e use cases, seguindo o padrão MVC e mantendo a separação de responsabilidades.

#### Subtarefas

**4.4.1 MainController - Controlador Principal**

**A. Estrutura e Responsabilidades**
```python
class MainController:
    """
    Controlador principal da aplicação.

    Responsabilidades:
    - Inicializar sub-controllers
    - Coordenar comunicação entre controllers
    - Gerenciar eventos de menu e toolbar
    - Controlar fluxo de navegação
    """

    def __init__(
        self,
        story_controller: StoryController,
        developer_controller: DeveloperController,
        schedule_controller: ScheduleController,
        import_excel_use_case: ImportFromExcelUseCase,
        export_excel_use_case: ExportToExcelUseCase,
    ):
        self._story_controller = story_controller
        self._developer_controller = developer_controller
        self._schedule_controller = schedule_controller
        self._import_use_case = import_excel_use_case
        self._export_use_case = export_excel_use_case
        self._main_window: Optional[MainWindow] = None
```

**B. Métodos Principais**
- [ ] `connect_view(main_window: MainWindow)` - Conecta todos os sinais
- [ ] `on_import_excel()` - Abre file dialog, importa Excel, atualiza tabela
- [ ] `on_export_excel()` - Abre file dialog, exporta backlog
- [ ] `on_calculate_schedule()` - Calcula cronograma, atualiza tabela
- [ ] `on_show_configuration()` - Abre ConfigurationDialog
- [ ] `refresh_backlog()` - Recarrega tabela completa

**C. Conexão de Sinais**
- [ ] Conectar ações de menu aos métodos do controller
- [ ] Conectar botões de toolbar aos métodos do controller
- [ ] Conectar atalhos de teclado

**D. Testes**
- [ ] Testar inicialização de controllers
- [ ] Testar fluxo de importação Excel (mock)
- [ ] Testar fluxo de exportação Excel (mock)
- [ ] Testar chamada de cálculo de cronograma

---

**4.4.2 StoryController - Controlador de Histórias**

**A. Estrutura**
```python
class StoryController:
    """
    Controlador de operações de histórias.

    Responsabilidades:
    - CRUD de histórias
    - Gerenciar recálculo reativo
    - Validar operações antes de executar
    - Comunicar com tabela de backlog
    """

    def __init__(
        self,
        create_story_use_case: CreateStoryUseCase,
        update_story_use_case: UpdateStoryUseCase,
        delete_story_use_case: DeleteStoryUseCase,
        get_story_use_case: GetStoryUseCase,
        list_stories_use_case: ListStoriesUseCase,
        get_backlog_use_case: GetBacklogUseCase,
        duplicate_story_use_case: DuplicateStoryUseCase,
        change_priority_use_case: ChangePriorityUseCase,
        calculate_schedule_use_case: CalculateScheduleUseCase,
    ):
        # Injeção de dependências
```

**B. Métodos Principais**
- [ ] `create_story(form_data: dict)` - Cria história, atualiza tabela
- [ ] `update_story(story_id: str, form_data: dict)` - Atualiza, verifica recálculo
- [ ] `delete_story(story_id: str)` - Confirma, deleta, atualiza tabela
- [ ] `duplicate_story(story_id: str)` - Duplica história, atualiza tabela
- [ ] `on_story_field_changed(story_id, field, value)` - Edição inline, recálculo
- [ ] `move_priority_up(story_id: str)` - Muda prioridade
- [ ] `move_priority_down(story_id: str)` - Muda prioridade
- [ ] `load_backlog() -> List[StoryDTO]` - Carrega backlog ordenado

**C. Lógica de Recálculo Reativo**
```python
FIELDS_REQUIRING_RECALC = ['story_point', 'developer_id', 'dependencies']

def on_story_field_changed(self, story_id: str, field: str, value: Any):
    """Gerencia edição inline com recálculo reativo"""
    try:
        # Atualizar história
        self._update_use_case.execute(story_id, {field: value})

        # Verificar se requer recálculo
        if field in FIELDS_REQUIRING_RECALC:
            self._show_recalculating_indicator()
            self._calculate_schedule_use_case.execute()
            self._hide_recalculating_indicator()
            self._refresh_table()

        self._show_success_message(f"Campo '{field}' atualizado")
    except Exception as e:
        self._show_error_message(str(e))
        self._revert_table_cell()
```

**D. Testes**
- [ ] Testar criação de história
- [ ] Testar edição de história
- [ ] Testar deleção de história
- [ ] Testar duplicação
- [ ] Testar mudança de prioridade
- [ ] Testar recálculo reativo dispara nos campos corretos

---

**4.4.3 DeveloperController - Controlador de Desenvolvedores**

**A. Estrutura**
```python
class DeveloperController:
    """Controlador de operações de desenvolvedores"""

    def __init__(
        self,
        create_developer_use_case: CreateDeveloperUseCase,
        update_developer_use_case: UpdateDeveloperUseCase,
        delete_developer_use_case: DeleteDeveloperUseCase,
        list_developers_use_case: ListDevelopersUseCase,
    ):
        # Injeção de dependências
```

**B. Métodos**
- [ ] `create_developer(name: str)` - Cria desenvolvedor
- [ ] `update_developer(dev_id: str, name: str)` - Atualiza nome
- [ ] `delete_developer(dev_id: str)` - Deleta, remove alocações
- [ ] `list_developers() -> List[DeveloperDTO]` - Lista todos

**C. Testes**
- [ ] Testar criação de desenvolvedor
- [ ] Testar edição de desenvolvedor
- [ ] Testar deleção (verificar remoção de alocações)

---

**4.4.4 ScheduleController - Controlador de Cronograma**

**A. Estrutura**
```python
class ScheduleController:
    """Controlador de operações de cronograma"""

    def __init__(
        self,
        calculate_schedule_use_case: CalculateScheduleUseCase,
        allocate_developers_use_case: AllocateDevelopersUseCase,
    ):
        # Injeção de dependências
```

**B. Métodos**
- [ ] `calculate_schedule()` - Calcula cronograma completo
- [ ] `allocate_developers()` - Aloca desenvolvedores automaticamente
- [ ] `show_schedule_summary()` - Mostra dialog com resumo (opcional)

**C. Testes**
- [ ] Testar cálculo de cronograma
- [ ] Testar alocação automática

---

**4.4.5 Dependency Injection Setup**
- [ ] Criar módulo `presentation/di_container.py` para centralizar injeção
- [ ] Implementar factory methods para criar controllers com dependências
```python
def create_main_controller() -> MainController:
    """Factory para criar MainController com todas as dependências"""
    # Criar repositories
    story_repo = SQLiteStoryRepository()
    developer_repo = SQLiteDeveloperRepository()
    config_repo = SQLiteConfigurationRepository()
    excel_service = OpenpyxlExcelService()

    # Criar serviços de domínio
    cycle_detector = CycleDetector()
    backlog_sorter = BacklogSorter(cycle_detector)
    schedule_calculator = ScheduleCalculator()

    # Criar use cases
    # ... (criar todos os use cases necessários)

    # Criar controllers
    story_controller = StoryController(...)
    developer_controller = DeveloperController(...)
    schedule_controller = ScheduleController(...)

    main_controller = MainController(
        story_controller,
        developer_controller,
        schedule_controller,
        import_excel_use_case,
        export_excel_use_case,
    )

    return main_controller
```

#### Critérios de Aceitação
- [x] Todos os controllers implementados
- [x] Injeção de dependências funcionando
- [x] Comunicação entre controllers e views funciona
- [x] Recálculo reativo dispara corretamente
- [x] Testes unitários passando

#### Arquivos Criados
- `backlog_manager/presentation/controllers/__init__.py`
- `backlog_manager/presentation/controllers/main_controller.py`
- `backlog_manager/presentation/controllers/story_controller.py`
- `backlog_manager/presentation/controllers/developer_controller.py`
- `backlog_manager/presentation/controllers/schedule_controller.py`
- `backlog_manager/presentation/di_container.py`
- `tests/unit/presentation/test_controllers.py`

---

### 4.5 Atalhos de Teclado e Menu de Ajuda (2 SP)

#### Objetivo
Implementar sistema completo de atalhos de teclado para operações frequentes e criar menu de ajuda com lista de atalhos.

#### Subtarefas

**4.5.1 Implementar Atalhos de Teclado**
- [ ] Configurar atalhos na MainWindow usando `QShortcut`:

```python
# Arquivo
QShortcut(QKeySequence("Ctrl+I"), self, self.on_import_excel)
QShortcut(QKeySequence("Ctrl+E"), self, self.on_export_excel)

# História
QShortcut(QKeySequence("Ctrl+N"), self, self.on_new_story)
QShortcut(QKeySequence("Return"), self, self.on_edit_story)  # Na tabela
QShortcut(QKeySequence("Ctrl+D"), self, self.on_duplicate_story)
QShortcut(QKeySequence("Delete"), self, self.on_delete_story)

# Prioridade
QShortcut(QKeySequence("Ctrl+Up"), self, self.on_move_priority_up)
QShortcut(QKeySequence("Ctrl+Down"), self, self.on_move_priority_down)

# Desenvolvedor
QShortcut(QKeySequence("Ctrl+Shift+N"), self, self.on_new_developer)

# Cronograma
QShortcut(QKeySequence("F5"), self, self.on_calculate_schedule)

# Configurações
QShortcut(QKeySequence("Ctrl+,"), self, self.on_show_configuration)

# Ajuda
QShortcut(QKeySequence("F1"), self, self.on_show_shortcuts)
```

**4.5.2 Criar ShortcutsDialog - Diálogo de Atalhos**
- [ ] Criar classe `ShortcutsDialog(QDialog)`
- [ ] Implementar tabela de atalhos com 3 colunas:
  - Ação
  - Atalho
  - Descrição
- [ ] Popular com todos os atalhos:

| Categoria | Ação | Atalho | Descrição |
|-----------|------|--------|-----------|
| **Arquivo** | Importar Excel | Ctrl+I | Importa histórias de arquivo Excel |
| **Arquivo** | Exportar Excel | Ctrl+E | Exporta backlog para Excel |
| **História** | Nova História | Ctrl+N | Cria nova história |
| **História** | Editar História | Enter | Edita história selecionada |
| **História** | Duplicar | Ctrl+D | Duplica história selecionada |
| **História** | Deletar | Delete | Deleta história selecionada |
| **História** | Mover para Cima | Ctrl+Up | Aumenta prioridade |
| **História** | Mover para Baixo | Ctrl+Down | Diminui prioridade |
| **Desenvolvedor** | Novo Desenvolvedor | Ctrl+Shift+N | Cria novo desenvolvedor |
| **Cronograma** | Calcular Cronograma | F5 | Recalcula todo o cronograma |
| **Geral** | Configurações | Ctrl+, | Abre configurações do sistema |
| **Geral** | Ajuda | F1 | Mostra este diálogo |

- [ ] Aplicar formatação visual (cores por categoria)
- [ ] Implementar busca de atalhos (QLineEdit de filtro)

**4.5.3 Menu "Ajuda"**
- [ ] Adicionar item "Atalhos de Teclado" (F1)
- [ ] Adicionar item "Sobre"
- [ ] Criar `AboutDialog` com:
  - Nome da aplicação: "Backlog Manager"
  - Versão: "1.0.0"
  - Descrição: "Sistema de gestão inteligente de backlog"
  - Link para repositório (se aplicável)
  - Licença

**4.5.4 Tooltips nos Botões**
- [ ] Adicionar tooltips descritivos em todos os botões de toolbar
- [ ] Incluir atalho no tooltip: "Nova História (Ctrl+N)"

**4.5.5 Testes**
- [ ] Testar que todos os atalhos disparam ações corretas
- [ ] Testar abertura de ShortcutsDialog
- [ ] Testar busca de atalhos
- [ ] Testar AboutDialog

#### Critérios de Aceitação
- [x] Todos os atalhos funcionam corretamente
- [x] ShortcutsDialog exibe lista completa e organizada
- [x] Busca de atalhos funciona
- [x] Tooltips informativos em botões
- [x] AboutDialog implementado

#### Arquivos Criados
- `backlog_manager/presentation/views/shortcuts_dialog.py`
- `backlog_manager/presentation/views/about_dialog.py`
- `tests/unit/presentation/test_shortcuts.py`

---

### 4.6 Sistema de Mensagens e Dialogs Utilitários (3 SP)

#### Objetivo
Criar sistema centralizado de mensagens, notificações e dialogs utilitários para comunicação consistente com o usuário.

#### Subtarefas

**4.6.1 MessageBox - Sistema de Mensagens**
- [ ] Criar módulo `presentation/utils/message_box.py`
- [ ] Implementar classe `MessageBox` com métodos estáticos:

```python
class MessageBox:
    """Sistema centralizado de mensagens"""

    @staticmethod
    def success(parent: QWidget, title: str, message: str):
        """Exibe mensagem de sucesso (ícone verde, check)"""
        QMessageBox.information(parent, title, message)

    @staticmethod
    def error(parent: QWidget, title: str, message: str):
        """Exibe mensagem de erro (ícone vermelho, X)"""
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def warning(parent: QWidget, title: str, message: str):
        """Exibe aviso (ícone amarelo, !)"""
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def confirm(parent: QWidget, title: str, message: str) -> bool:
        """Exibe confirmação, retorna True se confirmado"""
        result = QMessageBox.question(
            parent, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Padrão
        )
        return result == QMessageBox.Yes

    @staticmethod
    def confirm_delete(parent: QWidget, item_name: str) -> bool:
        """Confirmação específica de deleção"""
        return MessageBox.confirm(
            parent,
            "Confirmar Deleção",
            f"Tem certeza que deseja deletar '{item_name}'?\n\n"
            "Esta ação não pode ser desfeita."
        )
```

**4.6.2 StatusBarManager - Gerenciador de Status Bar**
- [ ] Criar classe `StatusBarManager` para gerenciar mensagens temporárias
```python
class StatusBarManager:
    """Gerencia mensagens na barra de status"""

    def __init__(self, status_bar: QStatusBar):
        self._status_bar = status_bar
        self._default_message = "Pronto"

    def show_message(self, message: str, timeout: int = 3000):
        """Exibe mensagem temporária"""
        self._status_bar.showMessage(message, timeout)

    def show_permanent(self, message: str):
        """Exibe mensagem permanente"""
        self._status_bar.showMessage(message)

    def show_loading(self, message: str = "Carregando..."):
        """Exibe indicador de loading"""
        self._status_bar.showMessage(f"⏳ {message}")

    def clear(self):
        """Limpa status bar"""
        self._status_bar.showMessage(self._default_message)
```

**4.6.3 ProgressDialog - Dialog de Progresso**
- [ ] Criar classe `ProgressDialog` para operações longas
```python
class ProgressDialog(QDialog):
    """Dialog de progresso para operações longas"""

    def __init__(
        self,
        parent: QWidget,
        title: str = "Processando...",
        message: str = "Por favor, aguarde...",
        cancelable: bool = False
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        layout = QVBoxLayout()

        # Label de mensagem
        self._message_label = QLabel(message)
        layout.addWidget(self._message_label)

        # Barra de progresso indeterminada
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # Indeterminado
        layout.addWidget(self._progress_bar)

        # Botão cancelar (opcional)
        if cancelable:
            cancel_button = QPushButton("Cancelar")
            cancel_button.clicked.connect(self.reject)
            layout.addWidget(cancel_button)

        self.setLayout(layout)

    def update_message(self, message: str):
        """Atualiza mensagem"""
        self._message_label.setText(message)
```

**4.6.4 NotificationToast - Notificações Temporárias**
- [ ] Criar widget de notificação estilo "toast" (opcional, recurso avançado)
- [ ] Aparece no canto inferior direito da janela
- [ ] Desaparece automaticamente após 3 segundos
- [ ] Tipos: success (verde), error (vermelho), info (azul)

**4.6.5 InputDialog - Dialogs de Input Simples**
- [ ] Wrapper para `QInputDialog` com validações:
```python
class InputDialog:
    """Dialogs de input simplificados"""

    @staticmethod
    def get_text(
        parent: QWidget,
        title: str,
        label: str,
        default: str = "",
        validator: Optional[Callable[[str], bool]] = None
    ) -> Optional[str]:
        """Solicita texto do usuário com validação opcional"""
        text, ok = QInputDialog.getText(parent, title, label, text=default)
        if ok:
            if validator and not validator(text):
                MessageBox.error(parent, "Erro", "Valor inválido")
                return None
            return text
        return None
```

**4.6.6 Uso Centralizado em Controllers**
- [ ] Atualizar controllers para usar sistema de mensagens:
```python
# Exemplo em StoryController
class StoryController:
    def create_story(self, form_data: dict):
        try:
            story = self._create_use_case.execute(form_data)
            MessageBox.success(
                self._main_window,
                "Sucesso",
                f"História '{story.name}' criada com sucesso!"
            )
            self._refresh_table()
        except Exception as e:
            MessageBox.error(
                self._main_window,
                "Erro ao Criar História",
                str(e)
            )
```

**4.6.7 Testes**
- [ ] Testar MessageBox.success/error/warning/confirm
- [ ] Testar ProgressDialog abertura e fechamento
- [ ] Testar StatusBarManager (mock de QStatusBar)
- [ ] Testar integração com controllers

#### Critérios de Aceitação
- [x] Sistema de mensagens centralizado funciona
- [x] Mensagens consistentes em toda aplicação
- [x] Progress dialog exibe durante operações longas
- [x] Status bar atualiza adequadamente
- [x] Confirmações de ações críticas (deleção)

#### Arquivos Criados
- `backlog_manager/presentation/utils/__init__.py`
- `backlog_manager/presentation/utils/message_box.py`
- `backlog_manager/presentation/utils/status_bar_manager.py`
- `backlog_manager/presentation/utils/progress_dialog.py`
- `backlog_manager/presentation/utils/notification_toast.py` (opcional)
- `tests/unit/presentation/test_message_system.py`

---

## 🧪 ESTRATÉGIA DE TESTES

### Tipos de Testes para Apresentação

**1. Testes Unitários de Controllers**
- Testar lógica de controller isoladamente
- Mock de use cases e views
- Verificar chamadas corretas de métodos

**2. Testes de Integração UI**
- Testar interação entre view e controller
- Mock de use cases
- Verificar que sinais são emitidos/recebidos corretamente

**3. Testes Manuais (Checklist)**
- Navegação completa da interface
- Validações visuais
- Responsividade

### Exemplo de Teste de Controller

```python
# tests/unit/presentation/test_story_controller.py
import pytest
from unittest.mock import Mock, MagicMock
from backlog_manager.presentation.controllers.story_controller import StoryController

class TestStoryController:
    @pytest.fixture
    def mock_use_cases(self):
        return {
            'create': Mock(),
            'update': Mock(),
            'delete': Mock(),
            'list': Mock(),
        }

    @pytest.fixture
    def controller(self, mock_use_cases):
        return StoryController(
            create_story_use_case=mock_use_cases['create'],
            update_story_use_case=mock_use_cases['update'],
            delete_story_use_case=mock_use_cases['delete'],
            list_stories_use_case=mock_use_cases['list'],
            # ... outros use cases mockados
        )

    def test_create_story_calls_use_case(self, controller, mock_use_cases):
        """Deve chamar CreateStoryUseCase ao criar história"""
        form_data = {
            'feature': 'Login',
            'name': 'Implementar autenticação',
            'story_point': 5,
        }

        controller.create_story(form_data)

        mock_use_cases['create'].execute.assert_called_once_with(form_data)

    def test_update_story_triggers_recalc_when_sp_changes(
        self, controller, mock_use_cases
    ):
        """Deve disparar recálculo ao mudar Story Point"""
        story_id = "S1"
        field = "story_point"
        value = 8

        # Mock do CalculateScheduleUseCase
        calculate_mock = Mock()
        controller._calculate_schedule_use_case = calculate_mock

        controller.on_story_field_changed(story_id, field, value)

        # Verifica que recálculo foi chamado
        calculate_mock.execute.assert_called_once()
```

### Exemplo de Teste de View

```python
# tests/unit/presentation/test_editable_table.py
import pytest
from PySide6.QtWidgets import QApplication
from backlog_manager.presentation.views.widgets.editable_table import EditableTableWidget
from backlog_manager.application.dto.story_dto import StoryDTO

@pytest.fixture(scope="module")
def qapp():
    """Fixture do QApplication (necessário para widgets Qt)"""
    app = QApplication.instance() or QApplication([])
    yield app

def test_table_populates_with_stories(qapp):
    """Deve popular tabela com histórias fornecidas"""
    table = EditableTableWidget()

    stories = [
        StoryDTO(
            id="S1",
            feature="Login",
            name="Implementar autenticação",
            story_point=5,
            status="BACKLOG",
            priority=1,
            # ... outros campos
        ),
    ]

    table.populate_from_stories(stories)

    assert table.rowCount() == 1
    assert table.item(0, 1).text() == "S1"  # Coluna ID
    assert table.item(0, 2).text() == "Login"  # Coluna Feature

def test_editable_columns_allow_editing(qapp):
    """Colunas editáveis devem permitir edição"""
    table = EditableTableWidget()

    # Feature (coluna 2) é editável
    item = table.item(0, 2)
    assert item.flags() & Qt.ItemIsEditable

    # ID (coluna 1) NÃO é editável
    item = table.item(0, 1)
    assert not (item.flags() & Qt.ItemIsEditable)
```

### Cobertura de Testes

**Alvo de Cobertura:**
- Controllers: ≥ 90%
- Widgets customizados: ≥ 85%
- ViewModels: ≥ 90%
- Utilities: ≥ 95%
- **Total da camada presentation: ≥ 85%**

---

## ⚠️ RISCOS E MITIGAÇÕES

### Risco 1: Complexidade da Edição Inline
**Probabilidade:** Alta
**Impacto:** Alto
**Mitigação:**
- Estudar exemplos de edição inline em Qt antes de implementar
- Implementar POC (Proof of Concept) com tabela simples
- Considerar delegates customizados para casos complexos
- Se muito complexo, considerar abrir dialog para editar campos complexos (Dependências)

### Risco 2: Performance da Tabela com Muitos Dados
**Probabilidade:** Média
**Impacto:** Médio
**Mitigação:**
- Implementar lazy loading / virtual scrolling desde o início
- Profiling de performance com 100+ histórias
- Desabilitar signals durante operações em massa
- Otimizar refresh parcial (apenas linhas afetadas)

### Risco 3: Sincronização View-Model
**Probabilidade:** Média
**Impacto:** Alto
**Mitigação:**
- Usar sinais Qt corretamente para comunicação
- Implementar debouncing para evitar updates excessivos
- Manter única fonte de verdade (banco de dados)
- Testar cenários de concorrência

### Risco 4: Experiência de Usuário Inconsistente
**Probabilidade:** Baixa
**Impacto:** Médio
**Mitigação:**
- Criar guia de estilo visual (QSS)
- Padronizar mensagens de erro/sucesso
- Solicitar feedback de usuários reais cedo
- Iterar com melhorias de UX

### Risco 5: Falta de Tratamento de Erros
**Probabilidade:** Média
**Impacto:** Alto
**Mitigação:**
- Implementar tratamento de exceções em todos os controllers
- Exibir mensagens de erro claras para o usuário
- Logging de erros para debug
- Testar casos de erro (banco indisponível, arquivo corrompido)

---

## 📝 CHECKLIST DE CONCLUSÃO DA FASE 4

### Funcionalidades Implementadas
- [ ] Aplicação abre sem erros
- [ ] Janela principal com menu, toolbar e status bar
- [ ] Tabela de backlog exibe histórias corretamente
- [ ] Edição inline funciona em todas as colunas editáveis
- [ ] Validações bloqueiam valores inválidos
- [ ] Recálculo automático dispara quando necessário
- [ ] Formulários de CRUD (História, Desenvolvedor, Configurações)
- [ ] Menu de contexto (clique direito) na tabela
- [ ] Atalhos de teclado funcionam
- [ ] Dialogs de confirmação para ações críticas
- [ ] Progress dialog para operações longas
- [ ] Sistema de mensagens (success/error/warning)

### Qualidade de Código
- [ ] Cobertura de testes ≥ 85%
- [ ] Todos os testes passando
- [ ] Código formatado (black, isort)
- [ ] Linting sem erros (flake8)
- [ ] Type hints em funções públicas
- [ ] Docstrings completas

### Integração
- [ ] Controllers conectam views a use cases corretamente
- [ ] Dependency injection funcionando
- [ ] Dados persistem no banco de dados
- [ ] Importação/Exportação Excel integrada

### Performance
- [ ] Edição inline < 100ms
- [ ] Cálculo de cronograma < 2s para 100 histórias
- [ ] Interface responsiva (não trava)

### UX/UI
- [ ] Interface intuitiva e profissional
- [ ] Feedback visual claro (cores, estados)
- [ ] Mensagens de erro descritivas
- [ ] Confirmações antes de ações destrutivas
- [ ] Atalhos documentados (Menu Ajuda)

---

## 🚀 PRÓXIMOS PASSOS (Após Fase 4)

### Fase 5: Features Avançadas
- Visualização Timeline/Roadmap (tipo Gantt)
- Sistema de filtros de backlog
- Otimização de performance
- Melhorias de UX baseadas em feedback

### Fase 6: Finalização
- Testes E2E completos
- Documentação de usuário
- Empacotamento com PyInstaller
- Distribuição do executável standalone

---

## 📚 REFERÊNCIAS E RECURSOS

### Documentação Qt
- [Qt for Python (PySide6) - Official Docs](https://doc.qt.io/qtforpython/)
- [Qt Widgets Examples](https://doc.qt.io/qt-6/qtwidgets-index.html)
- [Qt Style Sheets Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)

### Tutoriais e Exemplos
- [Qt TableWidget Tutorial](https://doc.qt.io/qt-6/qtablewidget.html)
- [Item Delegates](https://doc.qt.io/qt-6/qstyleditemdelegate.html)
- [Signals and Slots](https://doc.qt.io/qt-6/signalsandslots.html)

### Arquitetura
- Clean Architecture (Robert C. Martin)
- MVC Pattern em aplicações desktop
- Dependency Injection em Python

---

## ✅ CONCLUSÃO

A Fase 4 é a mais visível do projeto, onde toda a lógica implementada nas fases anteriores ganha vida através de uma interface gráfica profissional. Com este plano detalhado, você terá:

1. **Interface completa e funcional** conectando todas as funcionalidades do sistema
2. **Experiência de usuário intuitiva** similar a ferramentas profissionais
3. **Arquitetura limpa** com separação clara entre apresentação e lógica de negócio
4. **Código testável e manutenível** seguindo boas práticas

Ao concluir esta fase, o Backlog Manager será uma aplicação desktop completa, pronta para uso real e para ser aprimorada com features avançadas na Fase 5.

**Boa implementação! 🚀**
