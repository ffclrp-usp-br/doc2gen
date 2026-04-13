# Migrations Consolidada - Estado Final

## Resumo
Todas as migrations foram consolidadas em uma única migration inicial (0001_initial.py) representando o estado final estável dos modelos.

## Models Finais

### Compra
- numero_compra (CharField, unique, max_length=14)
- numero_sei (CharField, blank=True, unique, max_length=20)
- objeto (CharField, blank=True, max_length=255)
- modalidade (CharField, choices, blank=True, max_length=30)
- tipo (CharField, choices, blank=True, max_length=20)
- valor_estimado (DecimalField, blank=True, null=True)
- nome_agente_contratacao (CharField, choices, blank=True, max_length=255)
- pdf_file (FileField, blank=True, null=True)

### Demanda
- numero_demanda (CharField, unique, max_length=14)
- centro_gerencial (CharField, blank=True, max_length=50)
- grupo_orcamentario (CharField, blank=True, max_length=8)
- compra (ForeignKey to Compra)

### Item
- numero_ordem (PositiveIntegerField, db_index=True, editable=False)
- codigo_compras_gov (CharField, blank=True, max_length=14)
- codigo_contabiliza (CharField, blank=True, max_length=14)
- codigo_bem (CharField, blank=True, max_length=14)
- descricao (CharField, blank=True, max_length=255)
- item_despesa (CharField, blank=True, max_length=10)
- valor_medio (DecimalField, blank=True, null=True)
- demanda (ForeignKey to Demanda)

Meta:
- ordering: ['demanda', 'numero_ordem']
- unique_together: ('demanda', 'numero_ordem')

### Pesquisa
- nome_fornecedor (CharField, max_length=255)
- valor_unitario (DecimalField, blank=True, null=True)
- compra (ForeignKey to Compra)
- item (ForeignKey to Item)

## Migrations Removidas
As seguintes migrations foram consolidadas e removidas:
- 0002_compra_pdf_file_alter_compra_nome_agente_contratacao_and_more.py
- 0003_alter_item_centro_gerencial_and_more.py
- 0004_alter_compra_modalidade_and_more.py
- 0005_cotacao.py
- 0006_alter_item_options_remove_compra_valor_and_more.py
- 0007_alter_item_codigo_bem_alter_item_codigo_compras_gov_and_more.py
- 0008_alter_item_codigo_bem_alter_item_codigo_compras_gov_and_more.py

## Backup
As migrations antigas foram preservadas em: `app/compras/migrations/backup/`

## Próximos Passos
1. Executar `python manage.py migrate` para aplicar a nova migration inicial
2. Verificar se todos os dados foram preservados
3. Remover o diretório backup se tudo estiver funcionando