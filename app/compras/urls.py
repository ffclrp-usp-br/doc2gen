from django.urls import path
from . import views

urlpatterns = [
    path('', views.CompraListView.as_view(), name='compra_list'),
    path('nova/', views.CompraCreateView.as_view(), name='compra_create'),
    path('importar/compra/', views.CompraImportPDFView.as_view(), name='compra_import_pdf'),
    path('<int:pk>/editar/', views.CompraUpdateView.as_view(), name='compra_update'),
    path('<int:pk>/importar/demanda/', views.DemandaImportPDFView.as_view(), name='demanda_import_pdf'),
    path('<int:pk>/deletar/', views.CompraDeleteView.as_view(), name='compra_delete'),
    path('<int:compra_id>/itens/', views.ItemListView.as_view(), name='item_list'),
    path('<int:compra_id>/itens/novo/', views.ItemCreateView.as_view(), name='item_create'),
    path('item/<int:pk>/editar/', views.ItemUpdateView.as_view(), name='item_update'),
    path('item/<int:pk>/deletar/', views.ItemDeleteView.as_view(), name='item_delete'),
    path('<int:compra_id>/pesquisas/', views.PesquisaListView.as_view(), name='pesquisa_list'),
    path('pesquisa/<int:pk>/editar/', views.PesquisaUpdateView.as_view(), name='pesquisa_update'),
    path('pesquisa/<int:pk>/deletar/', views.PesquisaDeleteView.as_view(), name='pesquisa_delete'),
    path('<int:pk>/kit_conferencia/', views.KitConferenciaView.as_view(), name='kit_conferencia'),

    # Organizações
    path('organizacoes/', views.OrganizacaoListView.as_view(), name='organizacao_list'),
    path('organizacoes/nova/', views.OrganizacaoCreateView.as_view(), name='organizacao_create'),
    path('organizacoes/<int:pk>/editar/', views.OrganizacaoUpdateView.as_view(), name='organizacao_update'),
    path('api/organizacao/buscar/', views.buscar_organizacao_cnpj, name='buscar_organizacao_cnpj'),
    path('api/organizacao/<int:org_id>/vinculos/', views.gerenciar_vinculos_ajax, name='gerenciar_vinculos_ajax'),

    # Pessoas
    path('pessoas/', views.PessoaFisicaListView.as_view(), name='pessoa_list'),
    path('pessoas/nova/', views.PessoaFisicaCreateView.as_view(), name='pessoa_create'),
    path('pessoas/<int:pk>/editar/', views.PessoaFisicaUpdateView.as_view(), name='pessoa_update'),

    # Contratos
    path('contratos/', views.ContratoListView.as_view(), name='contrato_list'),
    path('contratos/novo/', views.ContratoCreateView.as_view(), name='contrato_create'),
    path('contratos/<int:pk>/editar/', views.ContratoUpdateView.as_view(), name='contrato_update'),
    path('contratos/<int:pk>/deletar/', views.ContratoDeleteView.as_view(), name='contrato_delete'),
]
