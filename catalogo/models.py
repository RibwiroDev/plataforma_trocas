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

    class Moderacao(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        APROVADO = 'aprovado', 'Aprovado'
        REPROVADO = 'reprovado', 'Reprovado'

    moderacao = models.CharField(max_length=10, choices=Moderacao.choices, default=Moderacao.PENDENTE, db_index=True)
    motivo_moderacao = models.TextField(blank=True)
    dono = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='itens')
    titulo = models.CharField(max_length=120)
    descricao = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='itens')
    estado_conservacao = models.CharField(max_length=10, choices=Estado.choices, default=Estado.USADO)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DISPONIVEL)
    aceita_categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='desejado_por_itens')
    aceita_descricao_livre = models.CharField(max_length=200, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo

    class Meta:
        permissions = [('moderar_item', 'Pode moderar anúncios')]

    @property
    def revisao_moderacao(self):
        return self.atualizado_em.isoformat()

    @property
    def titulo_publico(self):
        return self.titulo if self.moderacao == self.Moderacao.APROVADO else 'Anúncio indisponível'

    @property
    def imagem_principal(self):
        imagens = sorted(self.imagens.all(), key=lambda i: i.pk)  # .all() reaproveita o prefetch
        return next((i for i in imagens if i.principal), imagens[0] if imagens else None)

    def liberar_se_sem_propostas(self):
        """Volta para 'disponivel' se nenhuma proposta pendente restou para este item."""
        if self.status != self.Status.EM_NEGOCIACAO:
            return
        if not self.propostas_recebidas.filter(status='pendente').exists():
            self.status = self.Status.DISPONIVEL
            self.save(update_fields=['status'])


class ItemImagem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='imagens')
    imagem = models.ImageField(upload_to='itens/')
    principal = models.BooleanField(default=False)
    conteudo_privado = models.BinaryField(null=True, editable=False)
    tipo_imagem = models.CharField(max_length=20, blank=True, editable=False)

    def __str__(self):
        return f"Imagem de {self.item.titulo}"
