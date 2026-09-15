from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ItemForm
from .models import Categoria, Item, ItemImagem


def lista_itens(request):
    itens = Item.objects.filter(status=Item.Status.DISPONIVEL).select_related('categoria', 'dono').order_by('-criado_em')

    categoria_id = request.GET.get('categoria')
    if categoria_id:
        itens = itens.filter(categoria_id=categoria_id)

    paginator = Paginator(itens, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'catalogo/lista.html', {
        'page_obj': page_obj,
        'categorias': Categoria.objects.all(),
        'categoria_selecionada': categoria_id,
    })


def detalhe_item(request, pk):
    item = get_object_or_404(Item.objects.select_related('categoria', 'dono', 'aceita_categoria'), pk=pk)
    eh_dono = request.user.is_authenticated and item.dono_id == request.user.id
    return render(request, 'catalogo/detalhe.html', {'item': item, 'eh_dono': eh_dono})


@login_required
def criar_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.dono = request.user
            item.save()
            _salvar_imagens(item, form.cleaned_data.get('imagens') or [])
            messages.success(request, 'Item cadastrado com sucesso.')
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
            item = form.save()
            _salvar_imagens(item, form.cleaned_data.get('imagens') or [])
            messages.success(request, 'Item atualizado.')
            return redirect('detalhe_item', pk=item.pk)
    else:
        form = ItemForm(instance=item)
    return render(request, 'catalogo/form.html', {'form': form, 'item': item, 'titulo_pagina': 'Editar item'})


@login_required
def excluir_item(request, pk):
    item = get_object_or_404(Item, pk=pk, dono=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item excluído.')
        return redirect('lista_itens')
    return render(request, 'catalogo/confirmar_exclusao.html', {'item': item})


@login_required
def remover_imagem(request, pk):
    imagem = get_object_or_404(ItemImagem, pk=pk, item__dono=request.user)
    item_pk = imagem.item_id
    if request.method == 'POST':
        era_principal = imagem.principal
        imagem.delete()
        if era_principal:
            proxima = ItemImagem.objects.filter(item_id=item_pk).first()
            if proxima:
                proxima.principal = True
                proxima.save()
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
            imagem=arquivo,
            principal=(not ja_tem_principal and i == 0),
        )
