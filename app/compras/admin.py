from django.contrib import admin

from .models import Compra, Demanda, Item, Pesquisa


class ItemInline(admin.TabularInline):
    model = Item
    extra = 1
    readonly_fields = ('numero_ordem',)


class DemandaInline(admin.TabularInline):
    model = Demanda
    extra = 1


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('numero_compra', 'numero_sei', 'modalidade', 'tipo', 'valor_estimado', 'nome_agente_contratacao')
    search_fields = ('numero_compra', 'numero_sei', 'objeto')
    inlines = [DemandaInline]


@admin.register(Demanda)
class DemandaAdmin(admin.ModelAdmin):
    list_display = ('numero_demanda', 'centro_despesa', 'grupo_orcamentario', 'compra')
    list_filter = ('compra',)
    search_fields = ('numero_demanda', 'centro_despesa')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('demanda', 'numero_ordem', 'codigo_compras_gov', 'codigo_contabiliza', 'codigo_bem', 'descricao', 'item_despesa', 'valor_medio')
    list_filter = ('demanda__compra',)
    search_fields = ('demanda__numero_demanda', 'descricao', 'codigo_compras_gov')


@admin.register(Pesquisa)
class PesquisaAdmin(admin.ModelAdmin):
    list_display = ('item', 'nome_fornecedor', 'valor_unitario')
    list_filter = ('item__demanda__compra',)
    search_fields = ('nome_fornecedor',)
