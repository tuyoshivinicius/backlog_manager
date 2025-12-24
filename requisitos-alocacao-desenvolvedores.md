```
---
config:
  layout: dagre
---
flowchart TB
    A["FUNCIONALIDADE: ALOCAR DESENVOLVEDORES"] --> B["INÍCIO DO PROCESSO"]
    B --> C["LISTAR HISTÓRIAS SEM DESENVOLVEDOR ALOCADO<br>• Se existirem histórias, iniciar processamento<br>• Se não existirem, encerrar processo"]
    C --> D["ITERAR SOBRE CADA HISTÓRIA DA LISTA"]
    D --> E{"EXISTEM DESENVOLVEDORES DISPONÍVEIS?"}
    E -- SIM --> F["CRITÉRIO DE ALOCAÇÃO:<br>• Priorizar o desenvolvedor com menor número de histórias alocadas<br>• Em caso de empate, selecionar aleatoriamente entre os empatados"]
    F --> G["RETORNAR AO INÍCIO DO PROCESSO"]
    G --> C
    E -- NÃO --> H{"A DATA DE INÍCIO DESTA HISTÓRIA<br>JÁ FOI AJUSTADA ANTERIORMENTE?<br>(FLAG: INÍCIO ALTERADO)"}
    H -- NÃO --> K["ADICIONAR +1 DIA À DATA DE INÍCIO<br>E MARCAR FLAG: INÍCIO ALTERADO E INICIO ALTERADO NA ULTIMA INTERAÇÃO"]
    I["AVANÇAR PARA A PRÓXIMA HISTÓRIA<br>SEM MODIFICAR A DATA DE INÍCIO"] --> J{"CHEGOU AO FINAL DA LISTA<br>DE HISTÓRIAS?"}
    K --> J
    J -- NÃO --> D
    J -- SIM --> C
    H -- sim --> n1["ESSA HISTORIA TEVE +1 DIA INCREMENTADO NA ULTIMA INTERAÇÃO?"]
    n1 -- SIM --> I
    n1 -- NÃO --> K

    n1@{ shape: diam}
```

```markdown
# 📄 Documento de Requisitos — Alocação Automática de Desenvolvedores

## 1. Visão Geral

Este documento descreve os requisitos funcionais da **Funcionalidade de Alocação Automática de Desenvolvedores**, responsável por atribuir desenvolvedores às histórias que ainda não possuem alocação, respeitando regras de disponibilidade, balanceamento de carga e ajustes progressivos de data de início.

O comportamento descrito neste documento foi derivado diretamente do fluxo operacional definido no diagrama de processo fornecido.

---

## 2. Objetivo da Funcionalidade

Garantir que histórias sem desenvolvedor sejam alocadas de forma automática, previsível e equilibrada, ajustando o cronograma apenas quando não houver desenvolvedores disponíveis, evitando ajustes repetidos ou loops infinitos.

---

## 3. Escopo

Esta funcionalidade contempla:
- Identificação de histórias sem desenvolvedor
- Alocação automática baseada em critérios objetivos
- Controle de iteração sobre o backlog
- Ajuste controlado da data de início das histórias
- Uso de flags internas para controle de estado entre interações

---

## 4. Requisitos Funcionais

### RF-ALOC-001 — Iniciar Processo de Alocação

O sistema deve permitir iniciar o processo de alocação automática de desenvolvedores sob demanda.

---

### RF-ALOC-002 — Listar Histórias Elegíveis

O sistema deve listar todas as histórias que **não possuem desenvolvedor alocado**.

- Caso **não existam histórias elegíveis**, o processo deve ser encerrado imediatamente.
- Caso existam, o sistema deve iniciar o processamento.

---

### RF-ALOC-003 — Iterar sobre Histórias

O sistema deve iterar sequencialmente sobre cada história da lista de histórias elegíveis.

---

### RF-ALOC-004 — Verificar Disponibilidade de Desenvolvedores

Para cada história em processamento, o sistema deve verificar se existem desenvolvedores disponíveis para alocação.

---

### RF-ALOC-005 — Alocar Desenvolvedor Quando Disponível

Quando existirem desenvolvedores disponíveis, o sistema deve alocar um desenvolvedor à história conforme os critérios abaixo:

#### RF-ALOC-005.1 — Critério de Balanceamento
1. Priorizar o desenvolvedor com **menor número de histórias alocadas**.
2. Em caso de empate, selecionar **aleatoriamente** um dos desenvolvedores empatados.

Após a alocação:
- O sistema deve persistir a alteração.
- O sistema deve **retornar ao início do processo**, relistando as histórias sem desenvolvedor.

---

### RF-ALOC-006 — Tratar Ausência de Desenvolvedores Disponíveis

Quando **não existirem desenvolvedores disponíveis** para a história atual, o sistema deve avaliar o estado da data de início da história.

---

### RF-ALOC-007 — Controle de Ajuste da Data de Início

O sistema deve utilizar dois indicadores internos associados à história:

- **Flag “início alterado”**
- **Flag “início alterado na última interação”**

Esses indicadores devem controlar se a data de início pode ser ajustada.

---

### RF-ALOC-008 — Incrementar Data de Início

O sistema deve **incrementar a data de início da história em +1 dia** quando todas as condições abaixo forem verdadeiras:

- Não existem desenvolvedores disponíveis;
- A flag **“início alterado”** estiver **desmarcada**, **OU**
- A flag “início alterado” estiver marcada, mas **não** na última interação.

Após o incremento:
- O sistema deve marcar as flags **“início alterado”** e **“início alterado na última interação”**.

---

### RF-ALOC-009 — Não Incrementar Data de Início

O sistema **não deve alterar a data de início** quando:

- A flag “início alterado” estiver marcada **e**
- A flag “início alterado na última interação” indicar que a história já teve +1 dia incrementado na interação imediatamente anterior.

Nesse caso, o sistema deve avançar para a próxima história.

---

### RF-ALOC-010 — Avançar Iteração

Após processar uma história, o sistema deve verificar se chegou ao final da lista:

- Se **não chegou**, deve continuar a iteração com a próxima história.
- Se **chegou**, deve retornar à listagem inicial de histórias sem desenvolvedor e reiniciar o ciclo.