# Fluxo de Cadastro de Contratos

## Problema Atual

O processo atual de cadastro de contratos permite que o operador conclua o cadastro e gere o documento mesmo quando a empresa fornecedora não possui representantes legais cadastrados.

Como consequência, o contrato pode ser gerado sem informações obrigatórias de representação legal da contratada, produzindo documentos incompletos e juridicamente inadequados.

---

## Objetivo

Garantir que nenhum contrato seja gerado sem que exista pelo menos um representante legal válido associado à empresa fornecedora.

---

## Regras de Negócio

### RN001 - Empresa fornecedora

A empresa fornecedora é identificada a partir dos dados extraídos do documento de empenho.

### RN002 - Representante legal obrigatório

Toda empresa fornecedora utilizada em contratos deve possuir ao menos um representante legal ativo cadastrado.

### RN003 - Bloqueio da geração

O sistema não deve permitir a geração do contrato quando não existir representante legal cadastrado para a empresa fornecedora.

### RN004 - Cadastro durante o fluxo

Caso a empresa não possua representantes legais cadastrados, o sistema deve oferecer ao operador a possibilidade de cadastrá-los imediatamente, sem necessidade de abandonar o processo.

### RN005 - Validação antes da geração

Antes da geração do contrato, o sistema deve validar novamente a existência de representantes legais válidos para evitar inconsistências decorrentes de alterações simultâneas.

---

## Fluxo Proposto

### Etapa 1 - Seleção da compra

O operador seleciona a compra que originará o contrato.

Informações disponíveis:

* Processo
* Material ou serviço
* Valores
* Demais dados da contratação

### Etapa 2 - Upload do empenho

O operador realiza o envio do documento de empenho.

O sistema:

* Extrai os dados da empresa fornecedora.
* Identifica o CNPJ da empresa.
* Localiza ou cria o cadastro da empresa fornecedora.

### Etapa 3 - Verificação de representantes legais

Após identificar a empresa, o sistema verifica a existência de representantes legais cadastrados.

#### Cenário A - Representantes encontrados

O fluxo segue normalmente.

O sistema exibe:

* Nome dos representantes cadastrados.
* Opção para incluir novos representantes.
* Opção para editar representantes existentes.

#### Cenário B - Nenhum representante encontrado

O sistema exibe aviso de pendência:

"Esta empresa não possui representantes legais cadastrados. É necessário cadastrar pelo menos um representante para prosseguir com a geração do contrato."

O sistema disponibiliza:

* Botão "Cadastrar representante legal".
* Formulário de cadastro em modal ou etapa dedicada.

Enquanto não houver representante cadastrado:

* A geração do contrato permanece bloqueada.

### Etapa 4 - Cadastro do representante legal

Dados mínimos sugeridos:

* Nome completo
* CPF
* Cargo/Função

Após salvar:

* O representante passa a ser associado à empresa.
* O fluxo retorna ao cadastro do contrato.

### Etapa 5 - Revisão do contrato

O sistema apresenta:

* Compra selecionada
* Empresa fornecedora
* Representante(s) legal(is)
* Demais informações do contrato

### Etapa 6 - Geração do contrato

Antes da geração, executar validações:

* Compra válida
* Empresa identificada
* Pelo menos um representante legal ativo

Caso alguma validação falhe:

* Impedir geração.
* Exibir mensagem detalhada ao operador.

---

## Requisitos Funcionais

### RF001

Verificar automaticamente a existência de representantes legais após a identificação da empresa fornecedora.

### RF002

Permitir cadastro de representantes legais diretamente no fluxo de criação do contrato.

### RF003

Impedir geração de contratos sem representante legal cadastrado.

### RF004

Permitir seleção do representante que deverá constar no contrato quando houver mais de um cadastrado.

### RF005

Exibir claramente as pendências que impedem a geração do documento.

### RF006

Executar validação final imediatamente antes da geração do contrato.

---


# Implementação da classe PreenchedorTermoCienciaNotificacaoService

## Objetivo

Implementar uma nova classe denominada `PreenchedorTermoCienciaNotificacaoService`, tomando como base a implementação já existente e funcional da classe `PreenchedorContratoService`.

A nova classe deverá seguir os mesmos padrões arquiteturais, convenções, estratégias de leitura e escrita de arquivos DOCX, tratamento de exceções, estrutura de métodos, injeção de dependências e fluxo geral de processamento utilizados pela classe existente.

O objetivo é preencher automaticamente o documento "Termo de Ciência e Notificação" a partir dos dados do contrato.

---

## Requisitos Arquiteturais

### Reutilização

A implementação deve reutilizar ao máximo a lógica existente em `PreenchedorContratoService`.

A nova classe deve:

* Possuir estrutura semelhante.
* Utilizar os mesmos serviços auxiliares já existentes.
* Utilizar os mesmos modelos de domínio.
* Utilizar a mesma estratégia de geração de arquivos.
* Utilizar os mesmos mecanismos de localização e gravação de documentos.

Não devem ser criadas soluções paralelas quando já existir funcionalidade equivalente no preenchedor de contrato.

---

## Diferença Principal

O documento de Termo de Ciência e Notificação não utiliza placeholders delimitados por `<< >>`.

Os campos são apresentados no documento apenas na forma:

```text
CONTRATANTE:
CONTRATADO:
CONTRATO Nº (DE ORIGEM):
OBJETO:
LOCAL e DATA:
Nome:
Cargo:
CPF:
```

seguido de espaço em branco para preenchimento.

Portanto, a lógica de preenchimento deverá localizar os rótulos existentes e inserir o valor correspondente ao lado do texto já existente.

Exemplo:

Antes:

```text
CONTRATANTE:
```

Depois:

```text
CONTRATANTE: Prefeitura Municipal de Exemplo
```

---

## Ajuste Obrigatório de Título

Caso o documento contenha:

```text
ANEXO VI – TERMO DE CIÊNCIA E NOTIFICAÇÃO
```

deve ser substituído por:

```text
TERMO DE CIÊNCIA E NOTIFICAÇÃO
```

A remoção deve preservar a formatação original do parágrafo tanto quanto possível.

---

# Campos a preencher

## CONTRATANTE

Origem:

```python
organizacao_contratante = contrato.contratante
```

Critério:

Utilizar a organização marcada como:

```python
is_propria_instituicao=True
```

Resultado:

```text
CONTRATANTE: <nome da organização contratante>
```

---

## CONTRATADO

Origem:

Fornecedor associado ao contrato.

Resultado:

```text
CONTRATADO: <nome da organização contratada>
```

---

## CONTRATO Nº (DE ORIGEM)

Origem:

```python
contrato.numero
```

Resultado:

```text
CONTRATO Nº (DE ORIGEM): <numero do contrato>
```

---

## OBJETO

Origem:

```python
contrato.compra.objeto
```

Resultado:

```text
OBJETO: <objeto da compra>
```

---

## LOCAL e DATA

Formato:

```text
LOCAL e DATA: <cidade da contratante>, <data por extenso>
```

Exemplo:

```text
LOCAL e DATA: Ribeirão Preto, vinte e quatro de junho de dois mil e vinte e seis
```

Reutilizar, se existir, a mesma lógica de data por extenso utilizada no preenchimento do contrato.

Origem da cidade:

Endereço da organização contratante.

---

# Responsáveis

## Origem dos dados

Utilizar os representantes legais já cadastrados no sistema.

Caso existam múltiplos representantes, utilizar a mesma regra já adotada por `PreenchedorContratoService`.

---

# RESPONSÁVEIS PELA HOMOLOGAÇÃO DO CERTAME OU RATIFICAÇÃO DA DISPENSA/INEXIGIBILIDADE DE LICITAÇÃO

Preencher:

```text
Nome:
Cargo:
CPF:
```

com os dados do representante da organização contratante.

---

# RESPONSÁVEIS QUE ASSINARAM O AJUSTE

## Pela CONTRATANTE

Preencher:

```text
Nome:
Cargo:
CPF:
```

com os dados do representante da organização contratante.

---

## Pela CONTRATADA

Preencher:

```text
Nome:
Cargo:
CPF:
```

com os dados do representante da organização contratada.

---

# ORDENADOR DE DESPESAS DA CONTRATANTE

Preencher:

```text
Nome:
Cargo:
CPF:
```

com os dados do representante da organização contratante.

---

# Regras de CPF

Utilizar o mesmo formato empregado atualmente em `PreenchedorContratoService`.

Exemplo:

```text
123.456.789-00
```

---

# Estratégia de Busca dos Campos

A implementação deve localizar os textos:

```text
CONTRATANTE:
CONTRATADO:
CONTRATO Nº (DE ORIGEM):
OBJETO:
LOCAL e DATA:
```

e complementar a mesma linha.

Para os blocos de responsáveis, a implementação deve localizar o contexto do bloco e preencher os campos subsequentes:

```text
Nome:
Cargo:
CPF:
```

sem alterar outros blocos semelhantes existentes no documento.

---

# Resultado Esperado

A execução deverá gerar um DOCX final contendo todos os campos preenchidos, preservando a formatação original do modelo e removendo o prefixo:

ANEXO VI –

````

de forma que o título final seja apenas:

```text
TERMO DE CIÊNCIA E NOTIFICAÇÃO
````


---

## Melhoria Recomendada

Quando uma empresa possuir múltiplos representantes legais, o contrato deve armazenar explicitamente qual representante foi escolhido para aquela contratação.

Dessa forma:

* Alterações futuras no cadastro da empresa não afetam contratos já emitidos.
* O histórico do contrato permanece íntegro.
* É possível reconstruir exatamente o documento gerado em qualquer momento.
