from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from trocas.webpush import avisar_item_aprovado

from .models import Item, ItemImagem


def pode_moderar(usuario):
    return usuario.is_staff and usuario.has_perm('catalogo.moderar_item')


@login_required
def fila_moderacao(request):
    if not pode_moderar(request.user):
        raise PermissionDenied

    estado = request.GET.get('estado', Item.Moderacao.PENDENTE)
    if estado not in Item.Moderacao.values:
        estado = Item.Moderacao.PENDENTE
    itens = Item.objects.filter(moderacao=estado).select_related('dono', 'categoria').prefetch_related(
        Prefetch('imagens', queryset=ItemImagem.objects.defer('conteudo_privado'))
    ).order_by('-atualizado_em', '-pk')
    pagina = Paginator(itens, 12).get_page(request.GET.get('page'))
    return render(request, 'catalogo/moderacao.html', {
        'pagina': pagina, 'estados': Item.Moderacao.choices, 'estado': estado,
    })


@login_required
@require_POST
def decidir_moderacao(request, pk):
    if not pode_moderar(request.user):
        raise PermissionDenied

    decisao = request.POST.get('decisao')
    motivo = request.POST.get('motivo', '').strip()
    if decisao not in (Item.Moderacao.APROVADO, Item.Moderacao.REPROVADO):
        messages.error(request, 'Selecione uma decisão válida.')
    elif decisao == Item.Moderacao.REPROVADO and not 1 <= len(motivo) <= 500:
        messages.error(request, 'Informe um motivo de até 500 caracteres.')
    else:
        with transaction.atomic():
            item = get_object_or_404(Item.objects.select_for_update(), pk=pk)
            if item.moderacao != Item.Moderacao.PENDENTE or request.POST.get('revisao') != item.revisao_moderacao:
                messages.error(request, 'O anúncio mudou. Confira a versão atual antes de decidir.')
            else:
                item.moderacao = decisao
                item.motivo_moderacao = motivo if decisao == Item.Moderacao.REPROVADO else ''
                item.save(update_fields=['moderacao', 'motivo_moderacao', 'atualizado_em'])
                if decisao == Item.Moderacao.APROVADO:
                    avisar_item_aprovado(item)
                messages.success(request, f'Anúncio {item.get_moderacao_display().lower()}.')
    return redirect('fila_moderacao')
