from django.conf import settings
from django.db import models


class Categoria(models.Model):
    nome = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = "categorias"


class Item(models.Model):
    class Estado(models.TextChoices):
        NOVO = 'novo', 'Novo'
        SEMINOVO = 'seminovo', 'Seminovo'
        USADO = 'usado', 'Usado'

    class Status(models.TextChoices):
        DISPONIVEL = 'disponivel', 'Disponível'
        EM_NEGOCIACAO = 'em_negociacao', 'Em negociação'
        TROCADO = 'trocado', 'Trocado'

    dono = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='itens')
    titulo = models.CharField(max_length=120)
    descricao = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='itens')
    estado_conservacao = models.CharField(max_length=10, choices=Estado.choices, default=Estado.USADO)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DISPONIVEL)
    aceita_categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='desejado_por_itens')
    aceita_descricao_livre = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo

    @property
    def imagem_principal(self):
        return self.imagens.filter(principal=True).first() or self.imagens.first()


class ItemImagem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='imagens')
    imagem = models.ImageField(upload_to='itens/')
    principal = models.BooleanField(default=False)

    def __str__(self):
        return f"Imagem de {self.item.titulo}"