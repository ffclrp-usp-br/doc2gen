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

# Especificação – Cadastro de Modelos Oficiais para o Kit de Verificação

## Objetivo

Implementar um módulo administrativo que permita cadastrar e manter os documentos oficiais utilizados na composição do Kit de Verificação de uma compra.

Os documentos deverão ser armazenados no sistema de arquivos da aplicação, não sendo mais obtidos diretamente do website da Procuradoria.

O objetivo é permitir que, quando a Procuradoria publicar novas versões dos modelos, o administrador apenas substitua o arquivo correspondente, sem necessidade de alterações no código-fonte do sistema.

---

# Regras de Negócio

## 1. Documentos do Kit

O Kit de Verificação continuará sendo composto por:

* Planilha Excel gerada pelo sistema;
* Documento Word gerado pelo sistema;
* Modelos oficiais cadastrados no sistema.

Os modelos oficiais deverão ser adicionados automaticamente conforme a modalidade e o tipo da compra.

---

## 2. Categorias de documentos

O sistema deverá trabalhar com três categorias de documentos:

* Documento Principal
* Termo de Referência (TR)
* Contrato

O termo **Documento Principal** representa:

* Edital, quando a modalidade da compra for **Pregão**;
* Aviso de Contratação Direta, quando a modalidade da compra for **Dispensa**.

O nome apresentado ao usuário poderá variar conforme a modalidade, porém internamente ambos pertencem à categoria **Documento Principal**.

---

## 3. Associação com a Compra

Cada modelo deverá ser associado aos seguintes atributos da compra:

* Modalidade
* Categoria do documento
* Tipo da compra

A modalidade utilizará os mesmos valores definidos em `Compra.MODALIDADE_CHOICES`.

O tipo utilizará os mesmos valores definidos em `Compra.TIPO_CHOICES`.

Atualmente os tipos utilizados são:

* Fornecimento
* Serviço sem dedicação exclusiva de mão de obra
* Serviço com dedicação exclusiva de mão de obra

---

## 4. Regras de associação

### Documento Principal

Depende apenas da modalidade.

Exemplos:

* Pregão → Edital
* Dispensa → Aviso de Contratação Direta

Neste caso o campo **Tipo** não deverá ser utilizado.

---

### Termo de Referência

Depende da modalidade e do tipo da compra.

Exemplos:

* Pregão + Fornecimento
* Pregão + Serviço sem dedicação
* Pregão + Serviço com dedicação
* Dispensa + Fornecimento
* Dispensa + Serviço sem dedicação
* Dispensa + Serviço com dedicação

---

### Contrato

Segue exatamente a mesma regra do Termo de Referência.

---

# Modelo de Dados

Criar um novo modelo denominado `ModeloDocumento`.

Campos sugeridos:

* modalidade
* categoria
* arquivo
* data_atualização


---

## Categoria

Utilizar um enum semelhante ao abaixo:

* PRINCIPAL
* TR
* CONTRATO

---

## Tipo

O campo Tipo deverá ser obrigatório apenas para:

* TR
* Contrato

Para Documento Principal o campo deverá permanecer vazio.

Essa validação deverá ser implementada no método `clean()` do modelo.

---

## Restrição de unicidade

Deverá existir apenas um modelo vigente para cada combinação.

Criar uma restrição de unicidade composta por:

* modalidade
* categoria
* tipo

Exemplos válidos:

* Pregão + Principal
* Dispensa + Principal
* Pregão + TR + Fornecimento
* Pregão + TR + Serviço sem dedicação
* Pregão + TR + Serviço com dedicação
* Dispensa + Contrato + Serviço com dedicação

Não poderá existir mais de um registro para a mesma combinação.

---

# Arquivos

Os arquivos deverão ser armazenados no sistema de arquivos da aplicação utilizando `FileField`.

Ao substituir um modelo, o arquivo anterior deverá ser removido do disco para evitar arquivos órfãos.

A implementação deverá utilizar um mecanismo seguro para exclusão do arquivo antigo.

---

# Interface Administrativa

Criar uma tela denominada:

**Modelos Oficiais**

A listagem deverá apresentar:

* Modalidade
* Categoria
* Tipo
* Versão
* Nome do arquivo
* Data da última atualização

A tela deverá permitir:

* cadastrar modelo;
* editar modelo;
* substituir arquivo;
* excluir modelo.

Como existe apenas um modelo vigente para cada combinação, a edição do registro deverá atualizar o mesmo cadastro, não criando novas versões.

---

# Utilização pelo Gerador do Kit

Durante a geração do Kit de Verificação, o sistema deverá localizar automaticamente os modelos oficiais correspondentes à compra.

A lógica deverá seguir:

## Documento Principal

Consultar por:

* modalidade
* categoria = PRINCIPAL

---

## Termo de Referência

Consultar por:

* modalidade
* categoria = TR
* tipo

---

## Contrato

Consultar por:

* modalidade
* categoria = CONTRATO
* tipo

Os arquivos encontrados deverão ser incluídos automaticamente no Kit de Verificação juntamente com os documentos já gerados pelo sistema.

---

# Requisitos de Implementação

* Não utilizar caminhos fixos para os arquivos.
* Utilizar `FileField`.
* Utilizar `MEDIA_ROOT`.
* O código do gerador do Kit não deverá conter verificações específicas para Pregão, Dispensa ou outros casos particulares; a seleção dos documentos deverá ser inteiramente baseada nos registros cadastrados em `ModeloDocumento`.
* Todas as regras de validação deverão ficar concentradas no modelo e não na interface.
* O módulo deverá ser facilmente extensível para novas modalidades de contratação, bastando cadastrar novos modelos, sem necessidade de alterações na lógica de geração do Kit.


---

## Melhoria Recomendada

Quando uma empresa possuir múltiplos representantes legais, o contrato deve armazenar explicitamente qual representante foi escolhido para aquela contratação.

Dessa forma:

* Alterações futuras no cadastro da empresa não afetam contratos já emitidos.
* O histórico do contrato permanece íntegro.
* É possível reconstruir exatamente o documento gerado em qualquer momento.
