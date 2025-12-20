# Debug: Problema de Criação de História

## Problema Relatado
A aplicação fecha sem erro quando se tenta criar uma história, e aparentemente a história não é salva.

## Debugging Adicionado

Foram adicionados logs extensivos em **5 pontos críticos** do fluxo de criação de história:

### 1. main.py
- Hook global de exceções não tratadas
- Logging detalhado da inicialização
- Captura qualquer exceção não tratada no sistema

### 2. StoryFormDialog._on_save()
```
DEBUG: StoryFormDialog._on_save() INICIADO
1. Coletando dados do formulário...
2. Emitindo sinal story_saved...
3. Fechando dialog (accept)...
```

### 3. MainController._on_new_story()
```
DEBUG: MainController._on_new_story() INICIADO
1. Obtendo lista de desenvolvedores...
2. Criando StoryFormDialog...
3. Conectando sinal story_saved ao controller...
4. Executando dialog (bloqueante)...
```

### 4. StoryController.create_story()
```
DEBUG: StoryController.create_story() INICIADO
1. Executando CreateStoryUseCase...
2. Exibindo MessageBox.success...
3. Chamando _refresh_view...
```

### 5. MainController.refresh_backlog()
```
DEBUG: refresh_backlog() iniciado
1. Obtendo lista de histórias...
2. Populando tabela...
3. Atualizando status bar...
```

## Como Testar

1. Execute a aplicação:
   ```bash
   python main.py
   ```

2. Observe o console - deve mostrar:
   ```
   ================================================================================
   BACKLOG MANAGER - INICIANDO
   ================================================================================

   1. Criando aplicação Qt...
   [OK] Aplicação Qt criada
   ...
   APLICAÇÃO INICIADA COM SUCESSO - Aguardando interação do usuário
   ```

3. Clique em "Nova História" ou pressione Ctrl+N

4. Preencha o formulário:
   - Feature: Login
   - Nome: Implementar tela de login
   - Story Point: 5
   - Status: BACKLOG
   - Desenvolvedor: (Nenhum)
   - Prioridade: 1

5. Clique em "Salvar"

6. **OBSERVE O CONSOLE** - você verá a sequência completa de logs mostrando:
   - Onde o fluxo para
   - Que erros ocorrem
   - Que valores são passados entre os componentes

## O Que Esperar Ver no Console

### Cenário 1: Sucesso (esperado)
```
DEBUG: MainController._on_new_story() INICIADO
...
DEBUG: StoryFormDialog._on_save() INICIADO
...
DEBUG: StoryController.create_story() INICIADO
1. Executando CreateStoryUseCase...
[OK] História criada: US-001 - Implementar tela de login
2. Exibindo MessageBox.success...
[OK] MessageBox exibido
3. Chamando _refresh_view...
DEBUG: refresh_backlog() iniciado
...
DEBUG: StoryController.create_story() CONCLUÍDO COM SUCESSO
```

### Cenário 2: Exceção Capturada
```
DEBUG: StoryController.create_story() INICIADO
...
DEBUG: EXCEÇÃO CAPTURADA!
Tipo: ValueError
Mensagem: ...
Stack trace: ...
```

### Cenário 3: Exceção Não Tratada (crash)
```
EXCEÇÃO NÃO TRATADA CAPTURADA PELO HOOK GLOBAL!
Tipo: ...
Mensagem: ...
Stack trace: ...
```

## Análise de Resultados

### Se a aplicação fecha SEM nenhum log após "Salvar"
- O problema está na conexão do sinal Qt
- O método `create_story()` não está sendo chamado
- Possível problema na linha: `dialog.story_saved.connect(self._story_controller.create_story)`

### Se aparece log até "Executando CreateStoryUseCase" e para
- O problema está no use case de criação
- Provavelmente uma exceção não está sendo capturada corretamente
- Verificar banco de dados e schema

### Se aparece log até "Exibindo MessageBox.success" e para
- O problema está no MessageBox
- Pode ser um problema com o parent widget
- Pode ser um deadlock do Qt

### Se aparece log até "Chamando _refresh_view" e para
- O problema está na atualização da tabela
- Verificar o método `populate_from_stories()`
- Pode ser um problema com os delegates

## Teste Independente (CLI)

Para verificar se o use case funciona isoladamente:

```bash
python test_create_story.py
```

Este teste deve mostrar:
```
TESTE DE CRIAÇÃO DE HISTÓRIA
...
[OK] Historia criada com sucesso!
  ID: US-001
  Feature: Login
  Nome: Implementar tela de login
```

Se este teste passar, o problema é **definitivamente** na camada de apresentação (UI).

## Próximos Passos

Após executar e observar os logs, compartilhe a saída completa do console para análise detalhada.

## Possíveis Causas Identificadas

1. **Sinal Qt não conectado corretamente** - improvável, sintaxe está correta
2. **MessageBox causando deadlock** - possível se parent_widget for inválido
3. **Problema no refresh da tabela** - possível se delegates tiverem bugs
4. **Exceção silenciosa no Qt event loop** - o hook global deve capturar
5. **Problema com banco de dados** - improvável, teste CLI funciona

## Bugs de Lógica Identificados (não causam crash)

### CreateStoryUseCase ignora campos do formulário
O use case **ignora** os seguintes campos enviados pelo formulário:
- `status` - sempre cria com `BACKLOG` (linha 60)
- `priority` - sempre calcula automaticamente (linha 52)
- `developer_id` - não é passado para a entidade Story

Isso não causa crash, mas pode ser confuso para o usuário que seleciona valores diferentes.

**Correção necessária:**
- Modificar `CreateStoryUseCase` para aceitar esses campos opcionais
- Ou remover esses campos do formulário de criação (deixar apenas para edição)
