```markdown
# Documento de Alteração — Evolução do Backlog Manager com Features e Ondas

## 1. Objetivo

Este documento descreve **todas as alterações funcionais, regras de negócio e impactos técnicos** necessários para evoluir o **Backlog Manager**, introduzindo o conceito de **Feature** e **Onda**, e ajustando os comportamentos de **priorização**, **dependências**, **cálculo de cronograma** e **alocação automática de desenvolvedores**.

O objetivo principal é garantir **entrega incremental previsível**, respeitando dependências, prioridades e agrupamento lógico de histórias por ondas de entrega.

---

## 1.1 Decisões Arquiteturais Tomadas

Antes da implementação, as seguintes decisões arquiteturais foram definidas:

### DA-001: Campo Onda em Story
**Decisão:** Campo derivado/calculado (`@property`), **NÃO** denormalizado  
**Justificativa:**
- Evita inconsistências de dados (single source of truth)
- Simplifica manutenção (sem triggers de sincronização)
- Trade-off aceitável: queries que filtram por onda requerem JOIN

### DA-002: Valores de Onda
**Decisão:** Inteiros positivos (> 0), **NÃO sequenciais**, gaps permitidos  
**Justificativa:**
- Flexibilidade para inserir ondas futuras (ex: onda 10, 20, 30)
- Não requer renumeração ao deletar
- Usuário controla valores manualmente

### DA-003: Modelo de Prioridade
**Decisão:** Prioridade global contínua com agrupamento por onda  
**Justificativa:**
- Mantém compatibilidade com algoritmo atual
- Histórias da mesma onda têm priorities sequenciais agrupadas
- ChangePriorityUseCase valida movimento dentro da onda

### DA-004: Algoritmo de Ordenação (BacklogSorter)
**Decisão:** Prioridade composta `(wave * 10000) + priority`  
**Justificativa:**
- Menor impacto no algoritmo topológico existente (Kahn)
- Garante ondas anteriores sempre vêm primeiro
- Suporta até 9999 histórias por onda (suficiente)

### DA-005: Alocação em Deadlock
**Decisão:** Prosseguir para próxima onda com warning  
**Justificativa:**
- Preferir progressão parcial a bloqueio total
- Usuário pode intervir manualmente
- Emitir warnings claros de histórias não alocadas

### DA-006: Deleção de Feature
**Decisão:** Bloquear se possui histórias (ON DELETE RESTRICT)  
**Justificativa:**
- Mais seguro (evita perda acidental de dados)
- Força usuário a decidir conscientemente
- Mensagem clara: "Reatribua ou delete histórias antes"

### DA-007: Migração de Dados
**Decisão:** Automática via SQL migration  
**Justificativa:**
- Consistente com padrão atual do projeto
- Reproduzível e testável
- Feature padrão "Backlog Inicial" (onda 1) para histórias existentes

---

## 1.2 Glossário Técnico

**Terminologia Consistente:**

| Termo em Português (UI) | Termo em Código (Inglês) | Descrição |
|-------------------------|--------------------------|-----------||
| Onda | wave | Número inteiro que define ordem de entrega da feature |
| Feature | feature | Agrupador lógico de histórias (entidade) |
| História | story | User story individual |
| Prioridade | priority | Ordem de execução (inteiro global contínuo) |
| Desenvolvedor | developer | Pessoa que pode ser alocada a histórias |

**Regras de Nomenclatura:**
- **Código, logs, documentação técnica:** Inglês (`wave`, `feature`, `story`, `priority`)
- **Interface, mensagens ao usuário, dialogs:** Português ("Onda", "Feature", "História", "Prioridade")
- **Exceções:** Mensagens em português, nomes de classes em inglês

**Exemplos:**
```python
# Código
class Feature:
    wave: int  # Inglês

# Log
logger.info(f"Processing stories for wave {wave}")  # Inglês

# Mensagem ao usuário
MessageBox.error("Não é possível deletar a feature porque possui histórias.")  # Português
```

---

## 2. Nova Entidade: Feature

### 2.1 Definição

A entidade **Feature** representa um agrupador lógico de histórias que serão entregues juntas dentro de uma **onda** (wave/release increment).

Uma **onda** é um número inteiro que define a sequência de entrega. Quanto menor o valor, mais cedo a feature será entregue.

#### Atributos
- **id**: TEXT (UUID ou padrão similar a Developer.id)
  - Gerado automaticamente no CreateFeatureUseCase
  - Consistente com `developers.id` (TEXT)
- **nome**: string, obrigatório, único
- **onda**: inteiro obrigatório, único
  - Define a ordem de entrega da feature
  - Quanto menor o valor, mais cedo a entrega
  - Valores permitidos: inteiros positivos (> 0)
  - **Gaps são permitidos**: Ex: onda 1, 3, 5 é válido

### 2.2 Regras de Negócio

1. **Unicidade de Onda**
   - Não podem existir duas features com o mesmo valor de **onda**
   - Constraint UNIQUE no banco de dados: `features.onda`
   - Validação obrigatória em CreateFeature e UpdateFeature

2. **Imutabilidade e Gaps**
   - Ondas NÃO são renumeradas automaticamente ao deletar feature
   - Gaps são permitidos e esperados
   - Usuário define valores manualmente ao criar/editar feature
   - Não é necessário que ondas sejam sequenciais (1, 2, 3...)

3. **Impacto em Histórias**
   - A alteração da onda de uma feature impacta automaticamente todas as histórias associadas
   - Histórias herdam a onda da feature (campo derivado, veja seção 3.1)

### 2.3 Funcionalidades

- CRUD completo de Feature
  - **Criar**: gerar ID único (UUID v4 ou padrão similar a `Developer`)
    * Exemplo: `feature_001`, `feature_002`, ou UUID
    * Consistente com padrão de geração de IDs do projeto
  - **Editar**: permitir alterar nome e onda (com validações)
  - **Listar**: ordenado por onda ASC
  - **Remover**: bloquear se possui histórias (ON DELETE RESTRICT)

### 2.4 Impactos Técnicos

- **Domain**
  - Nova entidade `Feature`
  - Validação de unicidade da onda
  
- **Application**
  - Casos de uso de CRUD
  - DTOs e validações
  
  **Transações (UnitOfWork):**
  
  Os seguintes use cases **devem usar UnitOfWork** para garantir atomicidade:
  
  - `UpdateFeatureUseCase`: validação de dependências + update
    ```python
    def execute(self, feature_id: str, data: dict) -> FeatureDTO:
        with self.uow:
            # 1. Buscar feature
            feature = self.uow.features.find_by_id(feature_id)
            
            # 2. Se wave mudou, validar dependências
            if data['wave'] != feature.wave:
                self._validate_wave_change(feature, data['wave'])
            
            # 3. Atualizar
            feature.wave = data['wave']
            feature.name = data['name']
            self.uow.features.save(feature)
            
            # 4. Commit
            self.uow.commit()
            
            return feature_to_dto(feature)
    ```
  
  - `CalculateScheduleUseCase`: já usa UnitOfWork (manter)
  - `AllocateDevelopersUseCase`: já usa UnitOfWork (manter)
  
  **Rollback Automático:**
  - Se exceção durante `with self.uow`: rollback automático
  - Comportamento consistente com UnitOfWork atual do projeto
  
- **Infrastructure**
  - Nova tabela `features`
  - Constraint de unicidade para `onda`
  
- **Presentation**
  - Tela de gerenciamento de Features

---

## 3. Alterações na Entidade Story (História)

### 3.1 Novos Campos

- **feature_id**: inteiro obrigatório (FK → features.id)
  - Referência à Feature à qual a história pertence
  - NOT NULL constraint
  - FOREIGN KEY com ON DELETE RESTRICT (não permitir deletar feature com histórias)

- **onda**: campo **DERIVADO/CALCULADO** (não armazenado no banco)
  - Implementado como `@property` em Python
  - Obtido via relacionamento: `story.feature.onda`
  - **NÃO criar coluna `onda` na tabela `stories`**
  - Read-only na UI

**Decisão Arquitetural:**
Opta-se por campo derivado (não denormalizado) para:
- Evitar inconsistências de dados
- Simplificar manutenção (single source of truth)
- Eliminar necessidade de triggers de sincronização
- Trade-off: queries que filtram por onda requerem JOIN com `features`

### 3.2 Regras de Negócio

1. **Associação Obrigatória**
   - Toda história deve obrigatoriamente pertencer a uma Feature
   - Validação em CreateStory e UpdateStory

2. **Consistência Automática**
   - A onda da história é sempre igual à onda da sua Feature
   - Atualização automática via relacionamento (campo derivado)
   - Sem necessidade de sincronização manual

3. **Integridade Referencial**
   - Não é permitido deletar Feature que possui histórias associadas
   - Validação via FOREIGN KEY constraint (ON DELETE RESTRICT)

### 3.3 Impactos Técnicos

- **Domain**
  - Atualizar `Story` entity:
    ```python
    @dataclass
    class Story:
        feature_id: int  # Novo campo obrigatório
        
        @property
        def wave(self) -> int:
            """Onda derivada da feature (campo calculado)."""
            return self.feature.wave
    ```
  - Adicionar relacionamento: `story.feature: Feature`

- **Application**
  - `CreateStoryUseCase`:
    * Adicionar parâmetro `feature_id` obrigatório
    * Validar que feature existe
  
  - `UpdateStoryUseCase`:
    * Permitir alterar `feature_id`
    * Validar regra de dependência × onda (seção 5.3)
  
  - `StoryDTO`:
    * Adicionar campos: `feature_id: int`, `feature_name: str`, `wave: int`
    * Incluir onda em todas respostas

- **Infrastructure**
  - Adicionar coluna `feature_id TEXT NOT NULL` em `stories`
  - Constraint: `FOREIGN KEY (feature_id) REFERENCES features(id) ON DELETE RESTRICT`
  - **NÃO** criar coluna `wave` (campo derivado)
  - Migration para associar histórias existentes (veja seção 9)
  
  **Carregamento do Relacionamento:**
  
  - `SQLiteStoryRepository` deve carregar feature automaticamente (eager loading)
  - Implementar método privado `_load_features(stories: list[Story]) -> list[Story]`
  
  ```python
  def find_all(self) -> list[Story]:
      # 1. Buscar stories
      stories = self._fetch_stories_from_db()
      
      # 2. Buscar features em bulk (evitar N+1 queries)
      feature_ids = {s.feature_id for s in stories}
      features = self._fetch_features_by_ids(feature_ids)
      feature_map = {f.id: f for f in features}
      
      # 3. Associar features às stories
      for story in stories:
          if story.feature_id in feature_map:
              story.feature = feature_map[story.feature_id]
          else:
              # Não deve ocorrer devido a FK constraint
              raise DataIntegrityException(
                  f"Story '{story.id}' referencia feature inexistente '{story.feature_id}'"
              )
      
      return stories
  ```
  
  **Performance:**
  - 1 query para buscar stories
  - 1 query para buscar features (usando `WHERE id IN (...)` ou JOIN)
  - Complexidade: O(n) ao invés de O(n²) com lazy loading
  - Evita N+1 queries problem
  
  **Validação:**
  - Se `feature_id` não encontrar feature: lançar `DataIntegrityException`
  - Adicionar teste de integração para validar carregamento

- **Presentation**
  - Formulários de criação/edição:
    * Campo `Feature`: ComboBox com features cadastradas
    * Campo `Onda`: Label read-only (atualiza ao selecionar feature)
  
  - Tabela de Backlog:
    * Adicionar colunas: `Feature` e `Onda` (após ID)
    * Onda: não editável (display only)

---

## 4. Interface do Usuário (UI)

### 4.1 Gerenciamento de Features

#### 4.1.1 Menu
- Localização: **Ferramentas > Gerenciar Features**
- Atalho: `Ctrl+Shift+F`
- Ação: Abre `FeatureManagerDialog` (modal)

#### 4.1.2 FeatureManagerDialog

**Componentes:**
- Título: "Gerenciar Features"
- Tabela com colunas:
  * ID (oculto ou read-only)
  * Nome
  * Onda
  * Qtd Histórias (calculado)
- Botões:
  * **Novo** (Ctrl+N): abre FeatureForm em modo criação
  * **Editar** (Enter): abre FeatureForm em modo edição
  * **Deletar** (Delete): tenta deletar feature selecionada
  * **Fechar** (Esc)
- Ordenação padrão: Onda ASC

**Comportamento de Deleção:**
```
AO CLICAR EM DELETAR:

1. Buscar histórias da feature:
   count = story_repo.count_by_feature(feature_id)

2. SE count > 0:
   - Exibir MessageBox (erro):
     Título: "Não é possível deletar"
     Mensagem: "A feature '{nome}' possui {count} história(s) associada(s).
                Reatribua ou delete as histórias antes de deletar a feature."
   - Cancelar operação

3. SENÃO:
   - Exibir confirmação:
     "Tem certeza que deseja deletar a feature '{nome}' (Onda {onda})?"
   - Se confirmado: deletar
```

#### 4.1.3 FeatureForm (Dialog)

**Modo Criação:**
- Título: "Nova Feature"
- Campos:
  * Nome: TextField (obrigatório, max 100 chars)
  * Onda: SpinBox (min=1, max=9999, obrigatório)
- Botões: Salvar, Cancelar
- Validação:
  * Nome não vazio
  * Onda única (validar no banco antes de salvar)
  * Erro: "Já existe uma feature com onda {X}"

**Modo Edição:**
- Título: "Editar Feature"
- Campos: mesmos do modo criação (preenchidos)
- Validação adicional ao mudar onda:
  * Verificar se viola regra de dependência × onda (seção 5.3)
  * Se violação: erro detalhado com histórias problemáticas

### 4.2 Tabela de Backlog (MainWindow)

#### 4.2.1 Novas Colunas

**Posição:** Após coluna "ID", antes de "Component"

**Colunas adicionadas:**
1. **Feature** (editável)
   - Tipo: ComboBox delegate
   - Opções: lista de features cadastradas (exibir: Nome)
   - Validação: obrigatório
   - Ao alterar: validar regra de dependência × onda

2. **Onda** (read-only)
   - Tipo: Label/Display (não editável)
   - Valor: derivado da feature selecionada
   - Estilo: texto cinza (indicar read-only)
   - Atualização: automática ao mudar feature

**Ordem final das colunas:**
```
[ID] [Feature] [Onda] [Component] [Name] [Story Points] [Status] [Priority] [...]
```

#### 4.2.2 Ordenação

- Padrão: Priority ASC (comportamento atual)
- Permitir ordenação por Onda (clicar no header)
- Ao ordenar por Onda:
  * Critério primário: Onda ASC
  * Critério secundário: Priority ASC

### 4.3 Formulários de Histórias

#### 4.3.1 StoryForm - Criar/Editar

**Campo Feature (novo):**
- Label: "Feature *"
- Tipo: ComboBox
- Opções: features ordenadas por (Onda, Nome)
- Exibição: "{Nome} (Onda {X})"
- Obrigatório: sim
- Posição: Após "Component", antes de "Name"

**Campo Onda (novo, informativo):**
- Label: "Onda"
- Tipo: Label (read-only)
- Valor: atualiza ao selecionar feature
- Estilo: cinza, itálico
- Texto quando vazio: "Selecione uma feature"
- Posição: Abaixo do campo Feature

**Validação ao Salvar:**
- Verificar regra de dependência × onda
- Se violação: MessageBox com erro detalhado
- Não permitir salvar até corrigir

### 4.4 Import/Export Excel

#### 4.4.1 Exportação

**Colunas adicionadas ao Excel:**
- Feature (nome da feature)
- Onda (valor numérico)

**Posição:** Após "ID", antes de "Component"

**Formato:**
```
| ID    | Feature        | Onda | Component | Name       | ...
|-------|----------------|------|-----------|------------|
| S1    | MVP Core       | 1    | Sistema   | Login      | ...
| S2    | MVP Core       | 1    | Sistema   | Dashboard  | ...
| S3    | Relatórios   | 2    | BI        | Relat KPI  | ...
```

#### 4.4.2 Importação

**Colunas reconhecidas:**
- "Feature" ou "feature": nome da feature
- "Onda" ou "Wave": ignorado (campo derivado)

**Comportamento:**
1. Ao importar, buscar feature por nome
2. Se não encontrar: erro na linha
   - Mensagem: "Feature '{nome}' não encontrada na linha {X}"
3. Se coluna "Onda" presente no Excel: ignorar (warning)
   - Warning: "Coluna 'Onda' ignorada (valor derivado da Feature)"

**Validação:**
- Após importar, validar regra de dependência × onda
- Se violação: exibir relatório de erros
- Não persistir até corrigir

---

## 5. Regra de Dependência × Onda

### 5.1 Regra Fundamental

**Uma história só pode depender de histórias em ondas IGUAIS ou ANTERIORES.**

**Formalmente:**
- Se História H (onda W_h) depende de História D (onda W_d):
  - ✅ **VÁLIDO**: W_d ≤ W_h (dependência de onda anterior ou igual)
  - ❌ **INVÁLIDO**: W_d > W_h (dependência de onda futura)

**Justificativa:**
Histórias de ondas anteriores são entregues primeiro. Uma história não pode depender de algo que será entregue depois.

### 5.2 Exemplos

**Cenários Válidos:**
- História A (Onda 2) depende de História B (Onda 1) → ✅ OK
- História A (Onda 2) depende de História C (Onda 2) → ✅ OK
- História A (Onda 5) depende de História D (Onda 1) → ✅ OK

**Cenários Inválidos:**
- História A (Onda 1) depende de História B (Onda 2) → ❌ ERRO
- História A (Onda 3) depende de História C (Onda 5) → ❌ ERRO

**Mensagem de Erro:**
```
Não é possível [ação] porque criaria dependência de onda posterior.
História 'A' (onda 1) depende de 'B' (onda 2).
Dependências devem estar em ondas iguais ou anteriores.
```

### 5.3 Momentos de Validação

A regra deve ser validada em **3 momentos distintos**:

1. **AddDependencyUseCase**: ao adicionar nova dependência
   - Buscar onda de ambas histórias (via feature)
   - Validar: `onda_dependencia <= onda_historia`
   - Lançar `InvalidWaveDependencyException` se inválido

2. **UpdateStoryUseCase**: ao mudar feature de uma história
   - Validar todas dependências existentes contra nova onda
   - Validar todas histórias que dependem desta contra nova onda
   - Bloquear se criar dependência inválida

3. **UpdateFeatureUseCase**: ao mudar onda de uma feature
   
   **Validação Obrigatória ao Alterar Wave:**
   
   Para cada história H da feature sendo atualizada:
   
   a) **Validar dependências DE H** (histórias das quais H depende):
      - Para cada dependência D de H:
        * Verificar: `wave(D) <= wave_nova_da_feature`
        * Se FALSO: **bloquear** (H ficará dependendo de onda futura - inválido)
   
   b) **Validar histórias que DEPENDEM de H**:
      - Para cada história Y que tem H como dependência:
        * Verificar: `wave_nova_da_feature <= wave(Y)`
        * Se FALSO: **bloquear** (Y ficará dependendo de onda futura - inválido)
   
   **Exemplo Prático:**
   ```
   Feature A (wave=2) possui Story H
   Story H depende de Story D (Feature B, wave=1)
   Story Y (Feature C, wave=3) depende de H
   
   Tentar mudar Feature A de wave=2 para wave=3:
   - Validar (a): wave(D)=1 <= 3 → ✅ OK
   - Validar (b): 3 <= wave(Y)=3 → ✅ OK
   - Resultado: PERMITIR
   
   Tentar mudar Feature A de wave=2 para wave=1:
   - Validar (a): wave(D)=1 <= 1 → ✅ OK
   - Validar (b): 1 <= wave(Y)=3 → ✅ OK
   - Resultado: PERMITIR
   
   Tentar mudar Feature A de wave=2 para wave=4:
   - Validar (a): wave(D)=1 <= 4 → ✅ OK
   - Validar (b): 4 <= wave(Y)=3 → ❌ ERRO
   - Resultado: BLOQUEAR
   ```
   
   **Mensagem de Erro:**
   ```
   Não é possível alterar onda da feature de {wave_atual} para {wave_nova}.
   
   Violações encontradas:
   - História 'Y' (onda 3) depende de 'H' (ficaria em onda 4)
   - Dependendo de história de onda posterior é inválido
   
   Sugestões:
   - Altere a onda da Feature C para ≥ 4, ou
   - Remova a dependência entre Y e H
   ```

### 5.4 Impactos Técnicos

- **Domain**
  - Nova exceção: `InvalidWaveDependencyException`
  - Novo serviço: `WaveDependencyValidator` (opcional)
  - Regra de validação: `validate_wave_dependencies(story, new_feature)`

- **Application**
  - Ajuste em `AddDependencyUseCase.execute()`
  - Ajuste em `UpdateStoryUseCase.execute()`
  - Novo `UpdateFeatureUseCase.execute()`

- **Presentation**
  - Mensagem de erro clara e específica
  - Bloqueio visual ao tentar ação inválida
  - Highlight de histórias/dependências problemáticas

---

## 6. Regra de Prioridade por Onda

### 6.1 Definição

A prioridade de uma história é **local à sua onda** e define a ordem de execução dentro daquela onda.

**Modelo:** Prioridade Global Contínua com Agrupamento por Onda

- O campo `priority` é um inteiro global contínuo (0, 1, 2, 3, ...)
- Histórias da mesma onda possuem priorities sequenciais e agrupadas
- O range de priority de cada onda é dinâmico e calculado automaticamente

### 6.2 Estruturação

**Exemplo de Estrutura:**
```
Onda 1 (3 histórias): priorities 0, 1, 2
Onda 2 (2 histórias): priorities 3, 4
Onda 3 (1 história):  priority 5
Onda 5 (2 histórias): priorities 6, 7  (note: gap na onda 4)
```

**Cálculo do Range por Onda:**
- Buscar todas histórias da onda ordenadas por priority
- `min_priority` = menor priority da onda
- `max_priority` = maior priority da onda
- Range = [min_priority, max_priority]

### 6.3 Regras de Negócio

1. **Movimento Restrito à Onda**
   - História só pode mover prioridade dentro do range da sua onda
   - Não é permitido "pular" para outra onda via mudança de prioridade

2. **Troca de Posições**
   - `ChangePriorityUseCase` troca priorities entre histórias adjacentes
   - Validação: ambas histórias devem estar na mesma onda
   - Se tentar mover para fora da onda: erro claro

3. **Recalculo Automático**
   - `CalculateScheduleUseCase` renumera priorities globalmente
   - Ordem: (onda ASC, priority ASC)
   - Resultado: priorities contínuas 0, 1, 2, 3, ...

### 6.4 Exemplo de Movimento

**Estado Inicial:**
```
Onda 1: A (priority=0), B (priority=1), C (priority=2)
Onda 2: D (priority=3), E (priority=4)
```

**Operação: Mover D para cima (UP)**
- D está na posição 0 da onda 2 (primeira posição)
- ❌ **ERRO**: "História já está no topo da onda"

**Operação: Mover E para cima (UP)**
- Troca com D (mesma onda)
- Resultado: D (priority=4), E (priority=3)
- ✅ **OK**

### 6.5 Impactos Técnicos

- **Domain**
  - Serviço: `PriorityRangeCalculator.get_wave_range(wave: int) -> (min, max)`
  - Validação: `validate_priority_within_wave(story, new_priority)`

- **Application**
  - `ChangePriorityUseCase`:
    * Validar que histórias adjacentes estão na mesma onda
    * Bloquear se tentar mover para fora da onda
    * Mensagem: "Não é possível mover história para fora da onda {X}"
  
  - `CalculateScheduleUseCase`:
    * Renumerar priorities globalmente após ordenar por (onda, priority)
    * Garantir continuidade: 0, 1, 2, 3, ...

- **Presentation**
  - Bloqueio visual: desabilitar botões UP/DOWN se no limite da onda
  - Feedback: "Primeira/Última história da onda {X}"

---

## 7. Alteração no Cálculo de Cronograma

### 7.1 Nova Ordem do Algoritmo BacklogSorter

O algoritmo de ordenação passa a considerar **ondas** como critério de agrupamento.

**Estratégia Escolhida:** Prioridade Composta (menor impacto no algoritmo existente)

**Algoritmo:**

```
1. ENTRADA: lista de histórias

2. CRIAR priority_composta para cada história:
   priority_composta = (wave * 10000) + priority
   
   Justificativa:
   - wave * 10000: garante que ondas anteriores sempre vêm primeiro
   - + priority: desempate dentro da mesma onda
   - Suporta até 9999 histórias por onda

3. APLICAR ordenação topológica (Kahn's Algorithm):
   - Detectar ciclos (lançar exceção se houver)
   - Processar histórias respeitando dependências
   - DESEMPATE: usar priority_composta (crescente)
     * Histórias sem dependências pendentes são ordenadas por priority_composta
     * Isso garante: (wave ASC, priority ASC)

4. SAÍDA: lista ordenada
```

**Exemplo:**
```
Entrada:
- H1 (wave=2, priority=0) depende de H2
- H2 (wave=1, priority=0)
- H3 (wave=1, priority=1)
- H4 (wave=2, priority=1)

Priority_composta:
- H1: 20000
- H2: 10000
- H3: 10001
- H4: 20001

Ordenação topológica:
1. H2 (10000) - sem dependências
2. H3 (10001) - sem dependências
3. H1 (20000) - depende de H2 (já processada)
4. H4 (20001) - sem dependências

Saída: [H2, H3, H1, H4]
```

### 7.2 Ajuste Automático de Prioridade

**Quando Ocorre:**
- Durante `CalculateScheduleUseCase`, **após** ordenação topológica
- **NÃO** ocorre durante operações manuais de CRUD

**Regra:**
Se uma história H aparece **antes** de uma dependência D na lista ordenada (violação lógica), ajustar priority.

**Algoritmo:**

```
1. Obter lista ordenada topologicamente

2. Para cada história H na lista:
   a. Encontrar posição de H: index(H)
   b. Para cada dependência D de H:
      - Encontrar posição de D: index(D)
      - Se index(H) < index(D):  # Violação (nunca deve ocorrer após Kahn)
        * ERRO LÓGICO (algoritmo topológico falhou)
   
   c. Ajustar priority baseado na posição:
      - new_priority = index na lista ordenada
      - Isso garante que priorities refletem ordem topológica

3. Renumerar priorities globalmente:
   - Para cada história na posição i:
     * story.priority = i
   - Resultado: priorities contínuas 0, 1, 2, 3, ...

4. COMUNICAR ajustes:
   - Log warning para cada priority alterada
   - "Prioridade de '{story_id}' ajustada de {old} para {new} devido à ordenação topológica"
```

**Nota Importante:**
O algoritmo de Kahn **já garante** que dependências vêm antes. O "ajuste" é apenas a renumeração de priorities para refletir a ordem calculada.

### 7.3 Impactos Técnicos

- **Domain**
  - `BacklogSorter.sort()`:
    ```python
    def sort(self, stories: list[Story]) -> list[Story]:
        # Criar priority_composta
        for story in stories:
            story._sort_key = (story.feature.wave * 10000) + story.priority
        
        # Aplicar Kahn's algorithm usando _sort_key para desempate
        # (algoritmo existente, apenas mudar critério de desempate)
        ...
    ```
  
  - Nenhuma mudança estrutural no algoritmo topológico
  - Apenas alteração do critério de desempate

- **Application**
  - `CalculateScheduleUseCase.execute()`:
    ```python
    def execute(self, start_date):
        # 1. Buscar dados
        stories = self.story_repo.find_all()
        config = self.config_repo.get()
        
        # 2. Ordenar (com nova lógica de wave)
        sorted_stories = self.backlog_sorter.sort(stories)
        
        # 3. Calcular cronograma
        scheduled = self.schedule_calculator.calculate(
            sorted_stories, config, start_date
        )
        
        # 4. Renumerar priorities (ajuste automático)
        for index, story in enumerate(scheduled):
            if story.priority != index:
                old_priority = story.priority
                story.priority = index
                logger.warning(
                    f"Prioridade de '{story.id}' ajustada: "
                    f"{old_priority} → {index}"
                )
            story.schedule_order = index
            self.story_repo.save(story)
        
        # 5. Retornar BacklogDTO
        ...
    ```

- **Infrastructure**
  - Nenhuma mudança no schema
  - Stories precisam ter `feature_id` preenchido para calcular wave

- **Presentation**
  - Exibir warnings de ajuste de prioridade ao usuário
  - Dialog: "X histórias tiveram prioridade ajustada automaticamente"

---

## 8. Alteração na Alocação Automática de Desenvolvedores

### 8.1 Nova Regra: Alocação Onda por Onda

A alocação deve processar **sequencialmente por onda**: Onda 1 → Onda 2 → Onda 3 → ...

**Princípio:**
Uma onda só é iniciada quando a onda anterior estiver **completamente alocada** ou quando for impossível progredir.

### 8.2 Algoritmo Detalhado

```
FUNÇÃO: AllocateDevelopersUseCase.execute()

0. SINCRONIZAR schedule_order com priority atual da tabela

1. VALIDAÇÕES INICIAIS:
   - Buscar desenvolvedores
   - Se lista vazia: lançar NoDevelopersAvailableException
   - Buscar configuração

2. PREPARAR CONTEXTO:
   - all_stories = buscar todas histórias
   - waves = obter lista de ondas distintas ordenadas (ASC)
   - adjusted_stories = set() vazio  # Flag de ajuste único
   - total_allocated = 0
   - warnings = lista vazia

3. PARA CADA ONDA em waves:
   
   3.1. FILTRAR histórias da onda:
        wave_stories = [s for s in all_stories if s.feature.wave == onda_atual]
        wave_stories.sort(key=lambda s: s.priority)
   
   3.2. LOOP DE ALOCAÇÃO DA ONDA (máx 1000 iterações):
        
        a) Listar não alocadas da onda:
           unallocated = [s for s in wave_stories if s.developer_id is None and s.start_date]
        
        b) Se lista vazia: BREAK (onda completa)
        
        c) allocated_this_iteration = False
        
        d) Para cada história H em unallocated:
           
           i. Buscar desenvolvedores disponíveis:
              available_devs = get_available_developers(
                  H.start_date, H.end_date, all_stories
              )
           
           ii. SE há desenvolvedores disponíveis:
               - Selecionar: dev com menor carga (desempate aleatório)
               - Alocar: H.developer_id = dev.id
               - Persistir: story_repo.save(H)
               - total_allocated += 1
               - allocated_this_iteration = True
               - BREAK (reiniciar lista)
           
           iii. SENÃO (nenhum dev disponível):
                
                - SE H.id NOT IN adjusted_stories:
                  * Ajustar start_date:
                    - old_start = H.start_date
                    - H.start_date = schedule_calculator.add_workdays(old_start, 1)
                  
                  * Recalcular end_date (mantendo duration):
                    - H.end_date = schedule_calculator.add_workdays(H.start_date, H.duration - 1)
                    - IMPORTANTE: H.duration NÃO muda (permanece constante)
                  
                  * Marcar: adjusted_stories.add(H.id)
                  * Persistir: story_repo.save(H)
                  * Log: "Data de '{H.id}' ajustada: {old_start} → {H.start_date} (+1 dia útil)"
                
                - SENÃO:
                  * PULAR (já foi ajustada, não ajustar novamente)
        
        e) SE allocated_this_iteration == False:
           # Nenhuma alocação nesta iteração (deadlock na onda)
           
           - Contar não alocadas: count = len(unallocated)
           - Adicionar warning:
             warnings.append(
                 f"Onda {onda_atual}: {count} histórias não puderam ser alocadas"
             )
           - BREAK (pular para próxima onda)
   
   3.3. FIM DO LOOP DA ONDA

4. DETECTAR OCIOSIDADE:
   - idleness_warnings = idleness_detector.detect(all_stories, developers)
   - warnings.extend(idleness_warnings)

5. RETORNAR: (total_allocated, warnings)
```

### 8.3 Regras Mantidas do Algoritmo Atual

- Balanceamento de carga (menor número de histórias)
- Desempate aleatório (quando cargas iguais)
- Ajuste de data +1 dia útil (máximo 1x por história)
- Detecção de conflitos de alocação
- Detecção de períodos ociosos

### 8.4 Comportamento em Deadlock

**Cenário:**
Onda 2 possui 10 histórias, mas apenas 8 puderam ser alocadas (2 ficaram pendentes).

**Ação:**
- Emitir warning: "Onda 2: 2 histórias não puderam ser alocadas"
- **Prosseguir** para Onda 3 (não bloquear processo)
- Histórias não alocadas ficam visíveis na tabela (developer_id = NULL)
- Usuário pode alocar manualmente ou ajustar datas

**Justificativa:**
Preferir progressão parcial a bloqueio total. Permitir intervenção manual.

### 8.5 Impactos Técnicos

- **Domain**
  - `DeveloperLoadBalancer`: manter lógica atual (menor carga + desempate aleatório)
  - `IdlenessDetector`: nenhuma mudança
  - `AllocationValidator`: nenhuma mudança

- **Application**
  - `AllocateDevelopersUseCase.execute()`:
    ```python
    def execute(self):
        # 0. Sincronizar schedule_order
        self._update_schedule_order_from_table()
        
        # 1. Validar desenvolvedores
        developers = self.dev_repo.find_all()
        if not developers:
            raise NoDevelopersAvailableException(...)
        
        # 2. Preparar
        all_stories = self.story_repo.find_all()
        waves = sorted(set(s.feature.wave for s in all_stories))
        adjusted = set()
        total = 0
        warnings = []
        
        # 3. Processar onda por onda
        for wave in waves:
            wave_stories = [s for s in all_stories if s.feature.wave == wave]
            wave_stories.sort(key=lambda s: s.priority)
            
            allocated, wave_warnings = self._allocate_wave(
                wave, wave_stories, developers, all_stories, adjusted
            )
            total += allocated
            warnings.extend(wave_warnings)
        
        # 4. Detectar ociosidade
        idle_warnings = self.idleness_detector.detect(...)
        warnings.extend(idle_warnings)
        
        return (total, warnings)
    ```
  
  - Novo método privado: `_allocate_wave(wave, wave_stories, ...)`

- **Infrastructure**
  - Nenhuma mudança no schema
  - Queries precisam considerar `feature.wave` (JOIN com features)

- **Presentation**
  - `AllocationWorker` (QThread):
    * Emitir progresso por onda: "Alocando onda {X}..."
    * Exibir warnings por onda
  
  - `ProgressDialog`:
    * Mostrar onda atual sendo processada
    * Detalhar warnings de deadlock

---

## 9. Migração e Compatibilidade

### 9.1 Estratégia de Migração

**Abordagem:** Migration automática via script SQL + validação pós-migration

### 9.2 Migration SQL Detalhada

**Arquivo:** `backlog_manager/infrastructure/database/migrations/00X_add_features.py`

```sql
-- ============================================
-- MIGRATION 00X: Adicionar Features e Ondas
-- ============================================

BEGIN TRANSACTION;

-- PASSO 1: Criar tabela features
CREATE TABLE IF NOT EXISTS features (
    id TEXT PRIMARY KEY,  -- Consistente com developers.id
    name TEXT NOT NULL UNIQUE,
    wave INTEGER NOT NULL UNIQUE CHECK (wave > 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- PASSO 2: Criar índices
CREATE INDEX IF NOT EXISTS idx_features_wave ON features(wave);

-- PASSO 3: Criar trigger de updated_at
CREATE TRIGGER IF NOT EXISTS update_features_timestamp
AFTER UPDATE ON features
FOR EACH ROW
BEGIN
    UPDATE features SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- PASSO 4: Inserir feature padrão (para histórias existentes)
INSERT INTO features (id, name, wave)
VALUES ('feature_default', 'Backlog Inicial', 1);

-- PASSO 5: Adicionar coluna feature_id em stories (NULLABLE temporariamente)
ALTER TABLE stories ADD COLUMN feature_id TEXT;

-- PASSO 6: Associar todas histórias existentes à feature padrão
UPDATE stories SET feature_id = 'feature_default' WHERE feature_id IS NULL;

-- PASSO 7: Validar que todas histórias foram associadas
-- (Se falhar, ROLLBACK automático)
SELECT CASE 
    WHEN EXISTS (SELECT 1 FROM stories WHERE feature_id IS NULL) 
    THEN RAISE(ABORT, 'Migration falhou: histórias sem feature_id')
END;

-- PASSO 8: Tornar feature_id obrigatório
-- SQLite não suporta ALTER COLUMN, então recrear tabela:

-- 8.1. Criar tabela temporária com novo schema
CREATE TABLE stories_new (
    id TEXT PRIMARY KEY,
    component TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('BACKLOG', 'EXECUÇÃO', 'TESTES', 'CONCLUÍDO', 'IMPEDIDO')),
    priority INTEGER NOT NULL DEFAULT 0,
    feature_id TEXT NOT NULL,  -- AGORA NOT NULL e TEXT
    developer_id TEXT,
    dependencies TEXT DEFAULT '[]',
    story_point INTEGER NOT NULL CHECK (story_point IN (3, 5, 8, 13)),
    start_date TEXT,
    end_date TEXT,
    duration INTEGER,
    schedule_order INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (feature_id) REFERENCES features(id) ON DELETE RESTRICT,
    FOREIGN KEY (developer_id) REFERENCES developers(id) ON DELETE SET NULL
);

-- 8.2. Copiar dados
INSERT INTO stories_new SELECT * FROM stories;

-- 8.3. Dropar tabela antiga
DROP TABLE stories;

-- 8.4. Renomear tabela nova
ALTER TABLE stories_new RENAME TO stories;

-- 8.5. Recriar índices
CREATE INDEX IF NOT EXISTS idx_stories_priority ON stories(priority);
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);
CREATE INDEX IF NOT EXISTS idx_stories_developer ON stories(developer_id);
CREATE INDEX IF NOT EXISTS idx_stories_component ON stories(component);
CREATE INDEX IF NOT EXISTS idx_stories_feature ON stories(feature_id);  -- NOVO

-- 8.6. Recriar trigger
CREATE TRIGGER IF NOT EXISTS update_stories_timestamp
AFTER UPDATE ON stories
FOR EACH ROW
BEGIN
    UPDATE stories SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- PASSO 9: Validar integridade referencial
SELECT CASE 
    WHEN EXISTS (
        SELECT 1 FROM stories s 
        LEFT JOIN features f ON s.feature_id = f.id 
        WHERE f.id IS NULL
    )
    THEN RAISE(ABORT, 'Migration falhou: referências inválidas')
END;

COMMIT;
```

### 9.3 Rollback Plan

**Arquivo:** `backlog_manager/infrastructure/database/migrations/00X_add_features_rollback.sql`

```sql
BEGIN TRANSACTION;

-- 1. Recriar tabela stories sem feature_id
CREATE TABLE stories_old (
    id TEXT PRIMARY KEY,
    component TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    developer_id TEXT,
    dependencies TEXT DEFAULT '[]',
    story_point INTEGER NOT NULL,
    start_date TEXT,
    end_date TEXT,
    duration INTEGER,
    schedule_order INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (developer_id) REFERENCES developers(id) ON DELETE SET NULL
);

-- 2. Copiar dados (excluindo feature_id)
INSERT INTO stories_old 
SELECT id, component, name, status, priority, developer_id, 
       dependencies, story_point, start_date, end_date, duration, 
       schedule_order, created_at, updated_at
FROM stories;

-- 3. Dropar tabela atual
DROP TABLE stories;

-- 4. Renomear
ALTER TABLE stories_old RENAME TO stories;

-- 5. Dropar tabela features
DROP TABLE features;

-- 6. Recriar índices e triggers (schema original)
-- ...

COMMIT;
```

### 9.4 Validação Pós-Migration

**Script Python:** `validate_migration.py`

```python
def validate_migration():
    """Valida que migration foi executada corretamente."""
    
    # 1. Verificar tabela features existe
    assert table_exists('features'), "Tabela features não encontrada"
    
    # 2. Verificar feature padrão
    assert feature_exists(id=1), "Feature padrão não encontrada"
    
    # 3. Verificar todas histórias têm feature_id
    count = count_stories_without_feature()
    assert count == 0, f"{count} histórias sem feature_id"
    
    # 4. Verificar constraint de unicidade
    assert constraint_exists('features', 'wave', 'UNIQUE'), \
        "Constraint UNIQUE em wave não encontrado"
    
    # 5. Verificar FK
    assert foreign_key_exists('stories', 'feature_id', 'features'), \
        "Foreign key feature_id não encontrada"
    
    print("✅ Migration validada com sucesso")
```

### 9.5 Dados Existentes

**Comportamento Padrão:**
- Todas histórias existentes são associadas à feature "Backlog Inicial" (onda 1)
- Usuário pode:
  1. Criar novas features (ondas 2, 3, 4, ...)
  2. Reatribuir histórias manualmente para outras features
  3. Ou manter todas na feature padrão

**Recomendação ao Usuário:**
- Após migration, exibir dialog informativo:
  ```
  Título: "Features Implementadas"
  
  Mensagem:
  "O sistema agora suporta Features e Ondas!
  
  Todas as suas {N} histórias existentes foram associadas à feature 
  'Backlog Inicial' (Onda 1).
  
  Você pode:
  - Criar novas features em Ferramentas > Gerenciar Features
  - Reatribuir histórias para outras features
  - Ou continuar usando a feature padrão
  
  [OK]
  ```

---

## 10. Estratégia de Testes

### 10.1 Princípios

- **Cobertura mínima:** Manter 90%+ em todas as camadas (meta atual do projeto)
- **Testes de regressão:** Atualizar testes existentes para incluir features/ondas
- **Novos testes:** 100% de cobertura em use cases de Feature
- **Integração:** Validar fluxos completos (criação → cronograma → alocação)

### 10.2 Testes a Atualizar (Regressão)

#### 10.2.1 tests/unit/domain/test_backlog_sorter.py

**Cenários a adicionar:**
```python
def test_sort_with_waves_respects_wave_order():
    """Histórias de ondas anteriores vêm primeiro."""
    # Arrange
    feature1 = Feature(id=1, name="Feature 1", wave=1)
    feature2 = Feature(id=2, name="Feature 2", wave=2)
    
    story_wave2 = Story(id="S1", feature=feature2, priority=0, ...)  # Onda 2
    story_wave1 = Story(id="S2", feature=feature1, priority=1, ...)  # Onda 1
    
    # Act
    sorted_stories = sorter.sort([story_wave2, story_wave1])
    
    # Assert
    assert sorted_stories[0].id == "S2"  # Onda 1 vem primeiro
    assert sorted_stories[1].id == "S1"

def test_sort_with_same_wave_respects_priority():
    """Dentro da mesma onda, ordena por prioridade."""
    # ...

def test_sort_with_dependencies_across_waves():
    """Dependências entre ondas são respeitadas."""
    # Story onda 2 depende de story onda 1
    # ...
```

#### 10.2.2 tests/unit/domain/test_schedule_calculator.py

**Cenários a adicionar:**
```python
def test_calculate_schedule_with_multiple_waves():
    """Cronograma respeita ordenação por ondas."""
    # ...

def test_priorities_renumbered_after_calculation():
    """Priorities são renumeradas após ordenação topológica."""
    # ...
```

#### 10.2.3 tests/unit/application/test_change_priority.py

**Cenários a adicionar:**
```python
def test_cannot_move_story_outside_wave():
    """Erro ao tentar mover história para fora da onda."""
    # Story1 é última da onda 1
    # Tentar mover DOWN (para onda 2)
    # Assert: ValueError

def test_move_within_wave_succeeds():
    """Movimento dentro da mesma onda funciona."""
    # ...
```

### 10.3 Novos Testes a Criar

#### 10.3.1 tests/unit/domain/test_feature.py

```python
import pytest
from backlog_manager.domain.entities.feature import Feature

class TestFeature:
    def test_create_feature_valid():
        """Feature válida é criada com sucesso."""
        feature = Feature(id=1, name="MVP", wave=1)
        assert feature.name == "MVP"
        assert feature.wave == 1
    
    def test_create_feature_invalid_wave_zero():
        """Erro ao criar feature com wave = 0."""
        with pytest.raises(ValueError, match="wave deve ser > 0"):
            Feature(id=1, name="MVP", wave=0)
    
    def test_create_feature_invalid_wave_negative():
        """Erro ao criar feature com wave negativa."""
        with pytest.raises(ValueError, match="wave deve ser > 0"):
            Feature(id=1, name="MVP", wave=-1)
    
    def test_create_feature_empty_name():
        """Erro ao criar feature com nome vazio."""
        with pytest.raises(ValueError, match="nome não pode ser vazio"):
            Feature(id=1, name="", wave=1)
```

#### 10.3.2 tests/unit/application/test_feature_use_cases.py

```python
class TestCreateFeatureUseCase:
    def test_create_feature_success():
        """Feature é criada e persistida."""
        # ...
    
    def test_create_feature_duplicate_wave():
        """Erro ao criar feature com wave duplicada."""
        # Já existe feature com wave=1
        # Tentar criar outra com wave=1
        # Assert: DuplicateWaveException

class TestUpdateFeatureUseCase:
    def test_update_wave_validates_dependencies():
        """Ao mudar wave, valida dependências das histórias."""
        # Feature 1 (wave=1) tem Story A
        # Story A depende de Story B (wave=1)
        # Tentar mudar Feature 1 para wave=2
        # Assert: OK (dependência ainda válida)
        
        # Tentar mudar Feature 1 para wave=0.5 (< 1)
        # Assert: InvalidWaveDependencyException

class TestDeleteFeatureUseCase:
    def test_cannot_delete_feature_with_stories():
        """Erro ao deletar feature com histórias."""
        # ...
    
    def test_delete_feature_without_stories():
        """Feature sem histórias é deletada."""
        # ...
```

#### 10.3.3 tests/unit/application/test_story_wave_validation.py

```python
class TestWaveDependencyValidation:
    def test_add_dependency_valid_same_wave():
        """Pode adicionar dependência na mesma onda."""
        # ...
    
    def test_add_dependency_valid_previous_wave():
        """Pode adicionar dependência de onda anterior."""
        # ...
    
    def test_add_dependency_invalid_future_wave():
        """Erro ao adicionar dependência de onda futura."""
        # Story A (wave=1) tenta depender de Story B (wave=2)
        # Assert: InvalidWaveDependencyException
    
    def test_update_story_feature_validates_dependencies():
        """Ao mudar feature, valida dependências."""
        # ...
```

#### 10.3.4 tests/integration/test_feature_wave_flow.py

```python
class TestFeatureWaveIntegration:
    def test_complete_flow_create_feature_and_stories():
        """Fluxo completo: criar feature → criar histórias → calcular cronograma."""
        # 1. Criar features (wave 1, 2, 3)
        # 2. Criar histórias em cada feature
        # 3. Adicionar dependências
        # 4. Calcular cronograma
        # 5. Validar ordenação: wave 1 → 2 → 3
        # 6. Validar priorities renumeradas
    
    def test_allocate_developers_wave_by_wave():
        """Alocação processa onda por onda."""
        # 1. Criar 2 features (wave 1, 2)
        # 2. Criar histórias em cada
        # 3. Calcular cronograma
        # 4. Alocar desenvolvedores
        # 5. Validar: todas de wave 1 alocadas antes de iniciar wave 2
    
    def test_migration_associates_existing_stories_to_default_feature():
        """Histórias existentes são associadas à feature padrão."""
        # Simular banco com histórias sem feature_id
        # Executar migration
        # Validar: todas histórias com feature_id=1
```

### 10.4 Testes de Validação de Regras de Negócio

**Checklist de cenários obrigatórios:**

- [ ] Feature com wave duplicada → erro
- [ ] Feature com wave ≤ 0 → erro
- [ ] Story sem feature_id → erro
- [ ] Dependência de onda futura → erro
- [ ] Dependência de onda anterior → OK
- [ ] Dependência mesma onda → OK
- [ ] Mudar feature de story valida dependências → OK/erro
- [ ] Mudar wave de feature valida todas histórias → OK/erro
- [ ] Deletar feature com histórias → erro
- [ ] Deletar feature sem histórias → OK
- [ ] Mover priority para fora da onda → erro
- [ ] Mover priority dentro da onda → OK
- [ ] BacklogSorter respeita (dependências, wave, priority) → OK
- [ ] CalculateSchedule renumera priorities → OK
- [ ] AllocateDevelopers processa onda por onda → OK
- [ ] AllocateDevelopers em deadlock prossegue com warning → OK

### 10.5 Cobertura de Código

**Metas:**
- Domain: 95%+ (entidades, serviços)
- Application: 90%+ (use cases)
- Infrastructure: 80%+ (repositories, migrations)
- Presentation: 70%+ (controllers, views — UI mais difícil de testar)

**Comandos:**
```bash
# Rodar todos os testes com cobertura
pytest --cov=backlog_manager --cov-report=html --cov-report=term

# Rodar apenas novos testes de feature
pytest tests/unit/domain/test_feature.py -v
pytest tests/unit/application/test_feature_use_cases.py -v
pytest tests/integration/test_feature_wave_flow.py -v

# Verificar cobertura
open htmlcov/index.html
```

## 11. Riscos e Mitigações

### 11.1 Riscos Técnicos

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|---------------|
| Complexidade maior em BacklogSorter | Médio | Baixa | Usar priority_composta (menor impacto) + testes extensivos |
| Performance em queries com JOIN | Baixo | Média | Adicionar índice em feature_id + medir performance |
| Migration falha em produção | Alto | Baixa | Testar migration em cópia do banco + rollback plan |
| Inconsistência entre dependências e waves | Alto | Média | Validações em 3 pontos (seção 5.3) + constraint no banco |
| Deadlock em alocação onda por onda | Médio | Média | Prosseguir com warning + permitir alocação manual |

### 11.2 Riscos de UX

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|---------------|
| Usuários confusos com conceito de "Onda" | Médio | Alta | Dialog explicativo + documentação + tooltips |
| Dificuldade em entender erros de dependência × onda | Médio | Média | Mensagens detalhadas com exemplos + highlight visual |
| Frustração ao não poder deletar feature | Baixo | Média | Mensagem clara com instruções ("Reatribua histórias...") |

### 11.3 Pontos de Atenção

1. **Consistência de Dados**
   - Garantir que campo derivado `wave` sempre reflita `feature.wave`
   - Testes automatizados para validar consistência

2. **Performance**
   - Monitorar queries com JOIN em `features`
   - Considerar cache de waves se performance degradar

3. **Mensagens ao Usuário**
   - Todas validações devem ter mensagens claras e específicas
   - Evitar erros genéricos ("Operação inválida")

4. **Compatibilidade com Excel**
   - Garantir import/export funciona com features
   - Documentar formato esperado

5. **Testes de Regressão**
   - Executar suite completa antes de lançar
   - Validar que funcionalidades existentes não quebraram

### 11.4 Cenários Edge e Tratamentos

Comportamentos esperados para situações limite:

| Cenário | Comportamento Esperado | Use Case Responsável |
|---------|------------------------|------------------------|
| Criar história sem features cadastradas | Erro: "Nenhuma feature cadastrada. Crie uma feature em 'Ferramentas > Gerenciar Features' antes de adicionar histórias." | CreateStoryUseCase |
| Calcular cronograma sem features | Não deve ocorrer (todas histórias têm feature obrigatória) | CalculateScheduleUseCase |
| Calcular cronograma sem histórias | Retornar BacklogDTO vazio (count=0, sem erro) | CalculateScheduleUseCase |
| Importar Excel com feature inexistente | Erro na linha X: "Feature '{nome}' não encontrada. Crie a feature antes de importar ou corrija o nome no Excel." | ImportFromExcelUseCase |
| Deletar única feature restante (com histórias) | Erro: "Não é possível deletar a única feature. Reatribua as {count} histórias para outra feature ou crie uma nova feature primeiro." | DeleteFeatureUseCase |
| Feature com wave=999999 | Permitido (dentro do limite de INTEGER SQLite: -2^63 a 2^63-1) | CreateFeatureUseCase |
| Feature com wave negativa | Erro: "Onda deve ser um número positivo (> 0)." (CHECK constraint) | CreateFeatureUseCase |
| Mudar feature de 100+ histórias simultaneamente | Mostrar progresso: "Validando dependências... X/100" + timeout de 30s | UpdateFeatureUseCase |
| Story sem start_date/end_date ao alocar | Pular história (não alocar), adicionar warning: "História '{id}' sem datas calculadas (execute 'Calcular Cronograma' primeiro)" | AllocateDevelopersUseCase |
| Todas features deletadas (banco vazio) | Permitir deletar última feature se não tiver histórias. UI exibe mensagem: "Nenhuma feature cadastrada" | FeatureManagerDialog |
| Importar Excel com coluna "Onda" | Ignorar coluna com warning: "Coluna 'Onda' ignorada (valor é derivado da Feature selecionada)." | ImportFromExcelUseCase |
| Ciclo de dependências entre ondas | Detectado pelo CycleDetector existente (antes de validar ondas) | AddDependencyUseCase |
| Feature referenciada não existe (corrupção de dados) | Lançar DataIntegrityException ao carregar stories | SQLiteStoryRepository |

**Validações Adicionais:**

1. **CreateStoryUseCase**: verificar se existe pelo menos 1 feature antes de criar
2. **DeleteFeatureUseCase**: verificar count de histórias antes de deletar
3. **ImportFromExcelUseCase**: validar existência de features por nome (case-insensitive)
4. **AllocateDevelopersUseCase**: filtrar histórias sem datas antes de tentar alocar

---

## 12. Ordem Recomendada de Implementação

### Fase 1: Fundação (Domain + Infrastructure)
1. **Criar entidade Feature** (domain/entities/feature.py)
   - Atributos: id, name, wave
   - Validações: wave > 0, name não vazio
   - Testes: tests/unit/domain/test_feature.py

2. **Criar repositório e migration**
   - FeatureRepository interface (application/interfaces/)
   - SQLiteFeatureRepository (infrastructure/database/repositories/)
   - Migration SQL (infrastructure/database/migrations/00X_add_features.py)
   - Testes: tests/integration/infrastructure/test_feature_repository.py

3. **Alterar Story para incluir feature_id**
   - Adicionar campo feature_id
   - Adicionar @property wave
   - Atualizar validações
   - Executar migration

### Fase 2: Use Cases de Feature
4. **Implementar CRUD de Feature**
   - CreateFeatureUseCase
   - UpdateFeatureUseCase (com validação de wave dependencies)
   - DeleteFeatureUseCase (bloqueio se possui histórias)
   - ListFeaturesUseCase, GetFeatureUseCase
   - Testes: tests/unit/application/test_feature_use_cases.py

5. **Implementar validação de dependência × onda**
   - WaveDependencyValidator (domain/services/)
   - Integrar em AddDependencyUseCase
   - Integrar em UpdateStoryUseCase
   - InvalidWaveDependencyException
   - Testes: tests/unit/application/test_story_wave_validation.py

### Fase 3: Algoritmos
6. **Ajustar BacklogSorter**
   - Implementar priority_composta = (wave * 10000) + priority
   - Usar como critério de desempate em Kahn's algorithm
   - Testes: atualizar tests/unit/domain/test_backlog_sorter.py

7. **Ajustar CalculateScheduleUseCase**
   - Renumeração de priorities após ordenação
   - Logs de ajustes automáticos
   - Testes: atualizar tests/unit/application/test_calculate_schedule.py

8. **Ajustar AllocateDevelopersUseCase**
   - Implementar loop onda por onda
   - Método privado _allocate_wave()
   - Comportamento em deadlock (prosseguir com warning)
   - Testes: atualizar tests/unit/application/test_allocate_developers.py

### Fase 4: Presentation
9. **Implementar gerenciamento de Features (UI)**
   - FeatureManagerDialog (presentation/views/)
   - FeatureForm (presentation/views/)
   - FeatureController (presentation/controllers/)
   - Menu e atalho (Ctrl+Shift+F)

10. **Ajustar tabela de Backlog**
    - Adicionar colunas Feature e Onda
    - FeatureDelegate (ComboBox)
    - Onda read-only (cinza)
    - Ordenação por onda

11. **Ajustar formulários de Story**
    - Campo Feature (ComboBox obrigatório)
    - Campo Onda (Label read-only)
    - Validação ao salvar

12. **Ajustar ChangePriorityUseCase**
    - Validar movimento dentro da onda
    - Mensagens de erro específicas

### Fase 5: Import/Export e Validação
13. **Ajustar import/export Excel**
    - Adicionar coluna Feature na exportação
    - Reconhecer coluna Feature na importação
    - Validações de feature existente

14. **Testes de integração**
    - tests/integration/test_feature_wave_flow.py
    - Fluxo completo: criar feature → criar stories → calcular → alocar
    - Validar migration

15. **Executar migração em ambiente de teste**
    - Copiar banco de produção
    - Executar migration
    - Validar consistência
    - Testar rollback

### Checklist de Conclusão
- [ ] Todos os testes passando (90%+ cobertura)
- [ ] Migration testada com dados reais
- [ ] Documentação atualizada (README, claude.md)
- [ ] Validações de regras de negócio implementadas
- [ ] Mensagens de erro claras e específicas
- [ ] UI intuitiva e responsiva
- [ ] Performance aceitável (queries com JOIN)
- [ ] Rollback plan testado

---

## 13. Resultado Esperado

Após implementação completa, o sistema deverá apresentar:

### Funcionalidades
- ✅ Backlog organizado por **features e ondas**
- ✅ Entregas previsíveis e incrementalmente seguras
- ✅ Ordenação que respeita: dependências → onda → prioridade
- ✅ Alocação automática onda por onda
- ✅ Validações de dependência × onda em 3 pontos

### Qualidade Técnica
- ✅ Algoritmos alinhados à estratégia de entrega
- ✅ Regras de negócio explícitas, testáveis e consistentes
- ✅ 90%+ cobertura de testes
- ✅ Migrations reproduzíveis com rollback
- ✅ Mensagens de erro claras e acionáveis

### Experiência do Usuário
- ✅ Interface intuitiva para gerenciar features
- ✅ Feedback visual claro (ondas, validações)
- ✅ Warnings informativos (deadlock, ajustes)
- ✅ Import/export Excel mantém compatibilidade

### Decisões Documentadas
- ✅ Todas decisões arquiteturais registradas (seção 1.1)
- ✅ Trade-offs explicitados e justificados
- ✅ Plano de migration e rollback detalhado
```
