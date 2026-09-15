from django.urls import path
from . import views

urlpatterns = [
    path('itens/<int:item_pk>/propor/', views.propor_troca, name='propor_troca'),
    path('propostas/recebidas/', views.propostas_recebidas, name='propostas_recebidas'),
    path('propostas/enviadas/', views.minhas_propostas, name='minhas_propostas'),
    path('propostas/<int:pk>/aceitar/', views.aceitar_proposta, name='aceitar_proposta'),
    path('propostas/<int:pk>/recusar/', views.recusar_proposta, name='recusar_proposta'),
    path('propostas/<int:pk>/cancelar/', views.cancelar_proposta, name='cancelar_proposta'),
]
