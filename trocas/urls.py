from django.urls import path
from . import notificacoes, views

urlpatterns = [
    path('mensagens/', notificacoes.caixa_mensagens, name='caixa_mensagens'),
    path('notificacoes/', notificacoes.central_avisos, name='central_avisos'),
    path('notificacoes/resumo/', notificacoes.resumo_avisos, name='resumo_avisos'),
    path('notificacoes/vistas/', notificacoes.marcar_avisos, name='marcar_avisos'),
    path('itens/<int:item_pk>/propor/', views.propor_troca, name='propor_troca'),
    path('propostas/recebidas/', views.propostas_recebidas, name='propostas_recebidas'),
    path('propostas/enviadas/', views.minhas_propostas, name='minhas_propostas'),
    path('propostas/<int:pk>/aceitar/', views.aceitar_proposta, name='aceitar_proposta'),
    path('propostas/<int:pk>/recusar/', views.recusar_proposta, name='recusar_proposta'),
    path('propostas/<int:pk>/cancelar/', views.cancelar_proposta, name='cancelar_proposta'),
    path('propostas/<int:pk>/avaliar/', views.avaliar_troca, name='avaliar_troca'),
    path('propostas/<int:pk>/mensagens/', views.conversa, name='conversa'),
    path('propostas/<int:pk>/mensagens/novas/', views.mensagens_novas, name='mensagens_novas'),
]
