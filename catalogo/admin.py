from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Categoria, Item, ItemImagem


class RevisaoForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'

    def clean(self):
        dados = super().clean()
        if dados.get('moderacao') == Item.Moderacao.REPROVADO and not dados.get('motivo_moderacao'):
            self.add_error('motivo_moderacao', 'Informe o motivo da reprovação.')
        return dados


class FotoInline(admin.TabularInline):
    model = ItemImagem
    fields = ('preview', 'principal')
    readonly_fields = fields
    extra = 0
    can_delete = False

    def get_queryset(self, request):
        return super().get_queryset(request).defer('conteudo_privado')

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Foto')
    def preview(self, foto):
        return format_html('<img src="{}" width="120" alt="Foto do anúncio">', reverse('foto_item', args=[foto.pk]))


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    form = RevisaoForm
    list_display = ('titulo', 'dono', 'moderacao', 'criado_em')
    list_filter = ('moderacao',)
    search_fields = ('titulo', 'dono__username')
    list_select_related = ('dono',)
    inlines = (FotoInline,)
    actions = ('aprovar_anuncios',)

    @admin.action(description='Aprovar anúncios pendentes selecionados', permissions=['change'])
    def aprovar_anuncios(self, request, queryset):
        total = queryset.filter(moderacao=Item.Moderacao.PENDENTE).update(
            moderacao=Item.Moderacao.APROVADO, motivo_moderacao=''
        )
        self.message_user(request, f'{total} anúncio(s) aprovado(s).')


admin.site.register(Categoria)
