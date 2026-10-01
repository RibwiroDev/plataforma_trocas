from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from catalogo.models import Item
from .forms import AvaliacaoForm, MensagemForm, PropostaForm
from .models import Avaliacao, Mensagem, Proposta


@login_required
def propor_troca(request, item_pk):
    item_desejado = get_object_or_404(
        Item, pk=item_pk, status__in=[Item.Status.DISPONIVEL, Item.Status.EM_NEGOCIACAO]
    )

    if item_desejado.dono_id == request.user.id:
        messages.error(request, 'Você não pode propor troca pelo seu próprio item.')
        return redirect('detalhe_item', pk=item_pk)

    if request.method == 'POST':
        form = PropostaForm(request.POST, usuario=request.user)
        if form.is_valid():
            with transaction.atomic():
                proposta = form.save(commit=False)
                proposta.item_desejado = item_desejado
                proposta.proponente = request.user
                proposta.save()

                if item_desejado.status == Item.Status.DISPONIVEL:
                    item_desejado.status = Item.Status.EM_NEGOCIACAO
                    item_desejado.save(update_fields=['status'])

            messages.success(request, 'Proposta enviada com sucesso.')
            return redirect('minhas_propostas')
    else:
        form = PropostaForm(usuario=request.user)

    if not form.fields['item_ofertado'].queryset.exists():
        messages.warning(request, 'Você precisa ter pelo menos um item disponível para oferecer em troca.')

    return render(request, 'trocas/propor.html', {'form': form, 'item': item_desejado})


@login_required
def propostas_recebidas(request):
    avaliacao_existente = Avaliacao.objects.filter(proposta=OuterRef('pk'), avaliador=request.user)
    propostas = Proposta.objects.filter(
        item_desejado__dono=request.user
    ).select_related('item_desejado', 'item_ofertado', 'proponente').annotate(
        ja_avaliado=Exists(avaliacao_existente),
        nao_lidas=Count(
            'mensagens', filter=Q(mensagens__lida=False) & ~Q(mensagens__remetente=request.user), distinct=True
        ),
    )
    return render(request, 'trocas/recebidas.html', {'propostas': propostas})


@login_required
def minhas_propostas(request):
    avaliacao_existente = Avaliacao.objects.filter(proposta=OuterRef('pk'), avaliador=request.user)
    propostas = Proposta.objects.filter(
        proponente=request.user
    ).select_related('item_desejado', 'item_ofertado', 'item_desejado__dono').annotate(
        ja_avaliado=Exists(avaliacao_existente),
        nao_lidas=Count(
            'mensagens', filter=Q(mensagens__lida=False) & ~Q(mensagens__remetente=request.user), distinct=True
        ),
    )
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
        with transaction.atomic():
            proposta.status = Proposta.Status.RECUSADA
            proposta.save()
            _revalidar_status_item(proposta.item_desejado)
        messages.info(request, 'Proposta recusada.')
    return redirect('propostas_recebidas')


@login_required
def cancelar_proposta(request, pk):
    proposta = get_object_or_404(
        Proposta, pk=pk, proponente=request.user, status=Proposta.Status.PENDENTE
    )
    if request.method == 'POST':
        with transaction.atomic():
            proposta.status = Proposta.Status.CANCELADA
            proposta.save()
            _revalidar_status_item(proposta.item_desejado)
        messages.info(request, 'Proposta cancelada.')
    return redirect('minhas_propostas')


@login_required
def avaliar_troca(request, pk):
    proposta = get_object_or_404(
        Proposta.objects.select_related('item_desejado__dono', 'proponente'),
        Q(pk=pk),
        Q(status=Proposta.Status.ACEITA),
        Q(item_desejado__dono=request.user) | Q(proponente=request.user),
    )

    dono = proposta.item_desejado.dono
    eh_dono = request.user.id == dono.id
    avaliado = proposta.proponente if eh_dono else dono
    destino = 'propostas_recebidas' if eh_dono else 'minhas_propostas'

    if Avaliacao.objects.filter(proposta=proposta, avaliador=request.user).exists():
        messages.info(request, 'Você já avaliou essa troca.')
        return redirect(destino)

    if request.method == 'POST':
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                avaliacao = form.save(commit=False)
                avaliacao.proposta = proposta
                avaliacao.avaliador = request.user
                avaliacao.avaliado = avaliado
                avaliacao.save()
                _recalcular_reputacao(avaliado)
            messages.success(request, f'Avaliação enviada para {avaliado.username}.')
            return redirect(destino)
    else:
        form = AvaliacaoForm()

    return render(request, 'trocas/avaliar.html', {'form': form, 'proposta': proposta, 'avaliado': avaliado})


def _revalidar_status_item(item):
    """Volta o item pra 'disponivel' se não sobrou nenhuma proposta pendente pra ele."""
    if item.status != Item.Status.EM_NEGOCIACAO:
        return
    ainda_tem_pendente = item.propostas_recebidas.filter(status=Proposta.Status.PENDENTE).exists()
    if not ainda_tem_pendente:
        item.status = Item.Status.DISPONIVEL
        item.save(update_fields=['status'])


def _recalcular_reputacao(usuario):
    from django.db.models import Avg
    media = usuario.avaliacoes_recebidas.aggregate(media=Avg('nota'))['media'] or 0
    usuario.reputacao_media = round(media, 2)
    usuario.save(update_fields=['reputacao_media'])


def _participante_da_proposta(request, pk):
    return get_object_or_404(
        Proposta.objects.select_related('item_desejado__dono', 'proponente', 'item_ofertado'),
        Q(pk=pk),
        Q(item_desejado__dono=request.user) | Q(proponente=request.user),
    )


@login_required
def conversa(request, pk):
    proposta = _participante_da_proposta(request, pk)

    if request.method == 'POST':
        form = MensagemForm(request.POST)
        if form.is_valid():
            Mensagem.objects.create(proposta=proposta, remetente=request.user, texto=form.cleaned_data['texto'])
            return redirect('conversa', pk=proposta.pk)
    else:
        form = MensagemForm()

    mensagens = list(proposta.mensagens.select_related('remetente'))
    proposta.mensagens.filter(lida=False).exclude(remetente=request.user).update(lida=True)

    dono = proposta.item_desejado.dono
    outro_usuario = proposta.proponente if request.user.id == dono.id else dono

    return render(request, 'trocas/conversa.html', {
        'proposta': proposta,
        'mensagens': mensagens,
        'form': form,
        'outro_usuario': outro_usuario,
        'ultima_mensagem_id': mensagens[-1].pk if mensagens else 0,
    })


@login_required
def mensagens_novas(request, pk):
    proposta = _participante_da_proposta(request, pk)
    desde_id = request.GET.get('desde') or 0

    novas = proposta.mensagens.filter(pk__gt=desde_id).select_related('remetente')
    novas.filter(lida=False).exclude(remetente=request.user).update(lida=True)

    dados = [
        {
            'id': m.pk,
            'texto': m.texto,
            'remetente': m.remetente.username,
            'eh_minha': m.remetente_id == request.user.id,
            'criado_em': m.criado_em.strftime('%d/%m %H:%M'),
        }
        for m in novas
    ]
    return JsonResponse({'mensagens': dados})
