from datetime import timedelta
from hashlib import sha256

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from catalogo.models import Item
from .models import Mensagem, Proposta


def conversas_do(usuario):
    ultima = Mensagem.objects.filter(proposta_id=OuterRef('pk')).order_by('-criado_em', '-pk')
    return Proposta.objects.filter(
        Q(proponente=usuario) | Q(item_desejado__dono=usuario)
    ).select_related('proponente', 'item_desejado__dono', 'item_ofertado').annotate(
        ultima_em=Subquery(ultima.values('criado_em')[:1]),
        ultimo_texto=Subquery(ultima.values('texto')[:1]),
        nao_lidas=Count('mensagens', filter=Q(mensagens__lida=False) & ~Q(mensagens__remetente=usuario)),
    ).order_by('-ultima_em', '-criado_em')


def avisos_do(usuario):
    desde = timezone.now() - timedelta(days=7)
    propostas = Proposta.objects.filter(
        item_desejado__dono=usuario, criado_em__gte=desde,
    ).select_related('proponente', 'item_desejado')
    proximos = Item.objects.none()
    if usuario.estado and usuario.cidade:
        regiao = Q(estado__iexact=usuario.estado, cidade__iexact=usuario.cidade) | Q(
            estado='', dono__estado__iexact=usuario.estado, dono__cidade__iexact=usuario.cidade,
        )
        proximos = Item.objects.filter(
            regiao, moderacao=Item.Moderacao.APROVADO, status=Item.Status.DISPONIVEL,
            atualizado_em__gte=desde,
        ).exclude(dono=usuario).order_by('-atualizado_em', '-pk')
    return propostas, proximos, desde


@login_required
def caixa_mensagens(request):
    pagina = Paginator(conversas_do(request.user), 20).get_page(request.GET.get('page'))
    return render(request, 'trocas/mensagens.html', {'pagina': pagina})


@login_required
@never_cache
def central_avisos(request):
    propostas, proximos, _ = avisos_do(request.user)
    conversas = conversas_do(request.user).filter(nao_lidas__gt=0)
    return render(request, 'trocas/notificacoes.html', {
        'conversas': conversas[:12], 'propostas': propostas[:12], 'proximos': proximos[:12],
        'chave_dispositivo': sha256(request.session.session_key.encode()).hexdigest(),
    })


@login_required
@require_POST
def marcar_avisos(request):
    request.session['avisos_vistos_em'] = timezone.now().isoformat()
    return redirect('central_avisos')


@never_cache
def resumo_avisos(request):
    if not request.user.is_authenticated:
        return JsonResponse({'mensagens': 0, 'avisos': 0}, status=401)

    propostas, proximos, desde = avisos_do(request.user)
    visto = parse_datetime(request.session.get('avisos_vistos_em', '')) or desde
    mensagens = Mensagem.objects.filter(
        Q(proposta__proponente=request.user) | Q(proposta__item_desejado__dono=request.user),
        lida=False,
    ).exclude(remetente=request.user).count()
    novos = propostas.filter(criado_em__gt=visto).count() + proximos.filter(atualizado_em__gt=visto).count()
    return JsonResponse({'mensagens': mensagens, 'avisos': mensagens + novos})
