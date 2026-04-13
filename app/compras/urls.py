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
]