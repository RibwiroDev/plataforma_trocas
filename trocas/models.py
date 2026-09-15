from django.conf import settings
from django.db import models


class Proposta(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        ACEITA = 'aceita', 'Aceita'
        RECUSADA = 'recusada', 'Recusada'
        CANCELADA = 'cancelada', 'Cancelada'

    item_desejado = models.ForeignKey('catalogo.Item', on_delete=models.CASCADE, related_name='propostas_recebidas')
    item_ofertado = models.ForeignKey('catalogo.Item', on_delete=models.CASCADE, related_name='propostas_enviadas')
    proponente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='propostas_feitas')
    mensagem = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDENTE)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "propostas"
        ordering = ['-criado_em']

    def __str__(self):
        return f"Proposta de {self.proponente} por {self.item_desejado}"
