import hashlib
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from contas.models import Usuario

from .models import AssinaturaPush

logger = logging.getLogger(__name__)
worker = Path(__file__).resolve().parent.parent / 'static' / 'js' / 'swap-push-worker.js'


@require_GET
@never_cache
def push_worker(request):
    return HttpResponse(worker.read_bytes(), content_type='text/javascript; charset=utf-8')


@require_GET
@never_cache
def chave_push(request):
    if not request.user.is_authenticated:
        return JsonResponse({}, status=401)
    return JsonResponse({'chave': os.environ.get('SWAP_VAPID_PUBLIC', '')})


def endpoint_valido(endpoint):
    if not isinstance(endpoint, str) or not 1 <= len(endpoint) <= 2048:
        return False
    try:
        url = urlsplit(endpoint)
        host = url.hostname or ''
        return (
            url.scheme == 'https' and url.port in (None, 443)
            and not (url.username or url.password or url.fragment)
            and (
                host in {'fcm.googleapis.com', 'updates.push.services.mozilla.com'}
                or host.endswith(('.push.apple.com', '.notify.windows.com'))
            )
            and url.path.startswith('/')
        )
    except ValueError:
        return False


@require_POST
@never_cache
def registrar_push(request):
    if not request.user.is_authenticated:
        return JsonResponse({}, status=401)
    if len(request.body) > 4096:
        return JsonResponse({'erro': 'Assinatura inválida.'}, status=400)
    try:
        dados = json.loads(request.body)
        endpoint, chaves = dados['endpoint'], dados['keys']
        if not endpoint_valido(endpoint):
            raise ValueError
        for chave, minimo, maximo in (('p256dh', 86, 88), ('auth', 21, 24)):
            if not re.fullmatch(r'[A-Za-z0-9_-]+={0,2}', chaves[chave]) or not minimo <= len(chaves[chave]) <= maximo:
                raise ValueError
    except (KeyError, TypeError, ValueError):
        return JsonResponse({'erro': 'Assinatura inválida.'}, status=400)
    identificador = hashlib.sha256(endpoint.encode()).hexdigest()
    if dados.get('desativar') is True:
        AssinaturaPush.objects.filter(identificador=identificador, usuario=request.user).delete()
    else:
        if not os.environ.get('SWAP_VAPID_PRIVATE'):
            return JsonResponse({'erro': 'Push indisponível.'}, status=503)
        AssinaturaPush.objects.update_or_create(identificador=identificador, defaults={
            'usuario': request.user, 'sessao': request.session.session_key,
            'assinatura': {'endpoint': endpoint, 'keys': {k: chaves[k] for k in ('p256dh', 'auth')}},
        })
    return JsonResponse({'ok': True})


def notificar(destinatarios, titulo, texto, url):
    chave = os.environ.get('SWAP_VAPID_PRIVATE')
    if not chave:
        return

    def entregar():
        from requests import Session as RequestsSession
        from pywebpush import WebPushException, webpush

        class SemRedirecionamento(RequestsSession):
            def request(self, *args, **kwargs):
                kwargs['allow_redirects'] = False
                return super().request(*args, **kwargs)

        sessoes = Session.objects.filter(session_key=OuterRef('sessao'), expire_date__gt=timezone.now())
        assinaturas = list(AssinaturaPush.objects.filter(
            usuario__in=destinatarios,
        ).filter(Exists(sessoes)).values_list('pk', 'assinatura'))
        carga = json.dumps({'title': titulo, 'body': texto, 'url': url})
        expirada = []

        def enviar(entrada):
            pk, assinatura = entrada
            if not endpoint_valido(assinatura.get('endpoint')):
                return pk
            try:
                with SemRedirecionamento() as session:
                    webpush(
                        subscription_info=assinatura, data=carga, vapid_private_key=chave,
                        vapid_claims={'sub': 'https://plataforma-trocas.vercel.app'},
                        ttl=1800, timeout=4, requests_session=session,
                    )
            except WebPushException as error:
                if error.response is not None and error.response.status_code in (404, 410):
                    return pk
                logger.warning('Um serviço de Web Push recusou a entrega.')
            except Exception:
                logger.warning('Não foi possível entregar um Web Push.')
            return None

        if assinaturas:
            with ThreadPoolExecutor(max_workers=8) as pool:
                expirada = [pk for pk in pool.map(enviar, assinaturas) if pk is not None]
        if expirada:
            AssinaturaPush.objects.filter(pk__in=expirada).delete()

    transaction.on_commit(entregar, robust=True)


def avisar_item_aprovado(item):
    estado = item.estado or item.dono.estado
    cidade = item.cidade or item.dono.cidade
    if not estado or not cidade:
        return
    usuarios = Usuario.objects.filter(
        Q(estado__iexact=estado, cidade__iexact=cidade), is_active=True,
    ).exclude(pk=item.dono_id)
    notificar(usuarios, 'Novo anúncio por perto', 'Um item foi publicado na sua cidade.', f'/itens/{item.pk}/')
