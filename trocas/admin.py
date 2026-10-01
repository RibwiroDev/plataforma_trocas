from django.contrib import admin
from .models import Avaliacao, Mensagem, Proposta

admin.site.register(Proposta)
admin.site.register(Avaliacao)
admin.site.register(Mensagem)
