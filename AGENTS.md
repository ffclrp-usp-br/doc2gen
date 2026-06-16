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

## Melhoria Recomendada

Quando uma empresa possuir múltiplos representantes legais, o contrato deve armazenar explicitamente qual representante foi escolhido para aquela contratação.

Dessa forma:

* Alterações futuras no cadastro da empresa não afetam contratos já emitidos.
* O histórico do contrato permanece íntegro.
* É possível reconstruir exatamente o documento gerado em qualquer momento.
