from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from contas.forms import localidades

from .forms import ItemForm
from .models import Categoria, Item, ItemImagem
from .moderacao import pode_moderar


def lista_itens(request):
    itens = Item.objects.filter(
        moderacao=Item.Moderacao.APROVADO,
        status__in=[Item.Status.DISPONIVEL, Item.Status.EM_NEGOCIACAO]
    ).select_related('categoria', 'dono').prefetch_related(Prefetch('imagens', queryset=ItemImagem.objects.defer('conteudo_privado'))).order_by('-criado_em')

    categoria_id = request.GET.get('categoria', '')
    if categoria_id.isdecimal():
        itens = itens.filter(categoria_id=categoria_id)
    else:
        categoria_id = None

    estados = localidades()
    estado = request.GET.get('estado', '').upper()
    if estado in estados:
        itens = itens.filter(Q(estado__iexact=estado) | Q(estado='', dono__estado__iexact=estado))
    else:
        estado = ''

    paginator = Paginator(itens, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'catalogo/lista.html', {
        'page_obj': page_obj,
        'categorias': Categoria.objects.all(),
        'categoria_selecionada': categoria_id,
        'estados': estados,
        'estado_selecionado': estado,
    })


def detalhe_item(request, pk):
    item = get_object_or_404(Item.objects.select_related('categoria', 'dono', 'aceita_categoria').prefetch_related(Prefetch('imagens', queryset=ItemImagem.objects.defer('conteudo_privado'))), pk=pk)
    eh_dono = request.user.is_authenticated and item.dono_id == request.user.id
    if item.moderacao != Item.Moderacao.APROVADO and not (eh_dono or (pode_moderar(request.user) or (request.user.is_staff and request.user.has_perm('catalogo.change_item')))):
        raise Http404
    return render(request, 'catalogo/detalhe.html', {'item': item, 'eh_dono': eh_dono})


@login_required
def criar_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.dono = request.user
            with transaction.atomic():
                item.save()
                _salvar_imagens(item, form.cleaned_data.get('imagens') or [])
            messages.success(request, 'Anúncio enviado para revisão.')
            return redirect('detalhe_item', pk=item.pk)
    else:
        form = ItemForm()
    return render(request, 'catalogo/form.html', {'form': form, 'titulo_pagina': 'Novo item'})


@login_required
def editar_item(request, pk):
    item = get_object_or_404(Item, pk=pk, dono=request.user)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            with transaction.atomic():
                item = form.save(commit=False)
                item.moderacao = Item.Moderacao.PENDENTE
                item.motivo_moderacao = ''
                item.save()
                _salvar_imagens(item, form.cleaned_data.get('imagens') or [])
            messages.success(request, 'Anúncio atualizado e enviado para revisão.')
            return redirect('detalhe_item', pk=item.pk)
    else:
        form = ItemForm(instance=item)
    return render(request, 'catalogo/form.html', {'form': form, 'item': item, 'titulo_pagina': 'Editar item'})


@login_required
def excluir_item(request, pk):
    item = get_object_or_404(Item, pk=pk, dono=request.user)
    if request.method == 'POST':
        with transaction.atomic():
            disputados = list(Item.objects.filter(
                propostas_recebidas__item_ofertado=item, propostas_recebidas__status='pendente'
            ).distinct())
            item.delete()
            for outro in disputados:
                outro.liberar_se_sem_propostas()
        messages.success(request, 'Item excluído.')
        return redirect('lista_itens')
    return render(request, 'catalogo/confirmar_exclusao.html', {'item': item})


@login_required
def remover_imagem(request, pk):
    imagem = get_object_or_404(ItemImagem, pk=pk, item__dono=request.user)
    item_pk = imagem.item_id
    if request.method == 'POST':
        with transaction.atomic():
            era_principal = imagem.principal
            imagem.delete()
            if era_principal:
                proxima = ItemImagem.objects.filter(item_id=item_pk).first()
                if proxima:
                    proxima.principal = True
                    proxima.save(update_fields=['principal'])
        messages.success(request, 'Foto excluída do anúncio.')
        return redirect(f"{reverse('editar_item', args=[item_pk])}#fotos-enviadas")
    return redirect('editar_item', pk=item_pk)


@login_required
def definir_imagem_principal(request, pk):
    imagem = get_object_or_404(ItemImagem, pk=pk, item__dono=request.user)
    if request.method == 'POST':
        ItemImagem.objects.filter(item_id=imagem.item_id).update(principal=False)
        imagem.principal = True
        imagem.save()
    return redirect('editar_item', pk=imagem.item_id)


def _salvar_imagens(item, arquivos):
    ja_tem_principal = item.imagens.filter(principal=True).exists()
    for i, arquivo in enumerate(arquivos):
        ItemImagem.objects.create(
            item=item,
            conteudo_privado=arquivo.read(),
            tipo_imagem=arquivo.content_type if arquivo.content_type in ('image/jpeg', 'image/png', 'image/webp', 'image/gif') else 'application/octet-stream',
            principal=(not ja_tem_principal and i == 0),
        )


def foto_item(request, pk):
    foto = get_object_or_404(ItemImagem.objects.select_related('item'), pk=pk)
    item = foto.item
    if item.moderacao != Item.Moderacao.APROVADO and not (
        request.user.pk == item.dono_id or (pode_moderar(request.user) or (request.user.is_staff and request.user.has_perm('catalogo.change_item')))
    ):
        raise Http404
    if foto.conteudo_privado is None:
        if not foto.imagem:
            raise Http404
        return redirect(foto.imagem.url)
    resposta = HttpResponse(bytes(foto.conteudo_privado), content_type=foto.tipo_imagem)
    resposta['Cache-Control'] = 'private, no-store'
    resposta['X-Content-Type-Options'] = 'nosniff'
    return resposta
