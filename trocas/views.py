from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from catalogo.models import Item
from .forms import PropostaForm
from .models import Proposta


@login_required
def propor_troca(request, item_pk):
    item_desejado = get_object_or_404(Item, pk=item_pk, status=Item.Status.DISPONIVEL)

    if item_desejado.dono_id == request.user.id:
        messages.error(request, 'Você não pode propor troca pelo seu próprio item.')
        return redirect('detalhe_item', pk=item_pk)

    if request.method == 'POST':
        form = PropostaForm(request.POST, usuario=request.user)
        if form.is_valid():
            proposta = form.save(commit=False)
            proposta.item_desejado = item_desejado
            proposta.proponente = request.user
            proposta.save()
            messages.success(request, 'Proposta enviada com sucesso.')
            return redirect('minhas_propostas')
    else:
        form = PropostaForm(usuario=request.user)

    if not form.fields['item_ofertado'].queryset.exists():
        messages.warning(request, 'Você precisa ter pelo menos um item disponível para oferecer em troca.')

    return render(request, 'trocas/propor.html', {'form': form, 'item': item_desejado})


@login_required
def propostas_recebidas(request):
    propostas = Proposta.objects.filter(
        item_desejado__dono=request.user
    ).select_related('item_desejado', 'item_ofertado', 'proponente')
    return render(request, 'trocas/recebidas.html', {'propostas': propostas})


@login_required
def minhas_propostas(request):
    propostas = Proposta.objects.filter(
        proponente=request.user
    ).select_related('item_desejado', 'item_ofertado', 'item_desejado__dono')
    return render(request, 'trocas/enviadas.html', {'propostas': propostas})


@login_required
def aceitar_proposta(request, pk):
    proposta = get_object_or_404(
        Proposta, pk=pk, item_desejado__dono=request.user, status=Proposta.Status.PENDENTE
    )
    if request.method == 'POST':
        with transaction.atomic():
            proposta.status = Proposta.Status.ACEITA
            proposta.save()

            Item.objects.filter(pk__in=[proposta.item_desejado_id, proposta.item_ofertado_id]).update(
                status=Item.Status.TROCADO
            )

            Proposta.objects.filter(status=Proposta.Status.PENDENTE).filter(
                Q(item_desejado_id__in=[proposta.item_desejado_id, proposta.item_ofertado_id]) |
                Q(item_ofertado_id__in=[proposta.item_desejado_id, proposta.item_ofertado_id])
            ).exclude(pk=proposta.pk).update(status=Proposta.Status.RECUSADA)

        messages.success(request, 'Proposta aceita! Os dois itens foram marcados como trocados.')
    return redirect('propostas_recebidas')


@login_required
def recusar_proposta(request, pk):
    proposta = get_object_or_404(
        Proposta, pk=pk, item_desejado__dono=request.user, status=Proposta.Status.PENDENTE
    )
    if request.method == 'POST':
        proposta.status = Proposta.Status.RECUSADA
        proposta.save()
        messages.info(request, 'Proposta recusada.')
    return redirect('propostas_recebidas')


@login_required
def cancelar_proposta(request, pk):
    proposta = get_object_or_404(
        Proposta, pk=pk, proponente=request.user, status=Proposta.Status.PENDENTE
    )
    if request.method == 'POST':
        proposta.status = Proposta.Status.CANCELADA
        proposta.save()
        messages.info(request, 'Proposta cancelada.')
    return redirect('minhas_propostas')
