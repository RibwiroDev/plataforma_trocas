from django.urls import path
from . import moderacao, views
from .descricao import sugerir_descricao

urlpatterns = [
    path('administracao/anuncios/', moderacao.fila_moderacao, name='fila_moderacao'),
    path('administracao/anuncios/<int:pk>/decidir/', moderacao.decidir_moderacao, name='decidir_moderacao'),
    path('itens/sugerir-descricao/', sugerir_descricao, name='sugerir_descricao'),
    path('', views.lista_itens, name='lista_itens'),
    path('itens/novo/', views.criar_item, name='criar_item'),
    path('itens/<int:pk>/', views.detalhe_item, name='detalhe_item'),
    path('itens/<int:pk>/editar/', views.editar_item, name='editar_item'),
    path('itens/<int:pk>/excluir/', views.excluir_item, name='excluir_item'),
    path('imagens/<int:pk>/foto/', views.foto_item, name='foto_item'),
    path('imagens/<int:pk>/remover/', views.remover_imagem, name='remover_imagem'),
    path('imagens/<int:pk>/principal/', views.definir_imagem_principal, name='definir_imagem_principal'),
]
