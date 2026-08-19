from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    foto_perfil = models.ImageField(upload_to='perfil/', blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    reputacao_media = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username