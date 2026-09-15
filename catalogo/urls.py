from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_itens, name='lista_itens'),
    path('itens/novo/', views.criar_item, name='criar_item'),
    path('itens/<int:pk>/', views.detalhe_item, name='detalhe_item'),
    path('itens/<int:pk>/editar/', views.editar_item, name='editar_item'),
    path('itens/<int:pk>/excluir/', views.excluir_item, name='excluir_item'),
    path('imagens/<int:pk>/remover/', views.remover_imagem, name='remover_imagem'),
    path('imagens/<int:pk>/principal/', views.definir_imagem_principal, name='definir_imagem_principal'),
]
