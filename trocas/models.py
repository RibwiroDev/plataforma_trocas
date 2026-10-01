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


class Avaliacao(models.Model):
    proposta = models.ForeignKey(Proposta, on_delete=models.CASCADE, related_name='avaliacoes')
    avaliador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='avaliacoes_feitas')
    avaliado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='avaliacoes_recebidas')
    nota = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comentario = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "avaliações"
        ordering = ['-criado_em']
        constraints = [
            models.UniqueConstraint(fields=['proposta', 'avaliador'], name='uma_avaliacao_por_pessoa_por_troca')
        ]

    def __str__(self):
        return f"{self.avaliador} avaliou {self.avaliado} com nota {self.nota}"
