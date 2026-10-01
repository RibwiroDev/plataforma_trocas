from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from .forms import CadastroForm, PerfilForm
from .models import Usuario


def cadastro(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST, request.FILES)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('perfil')
    else:
        form = CadastroForm()
    return render(request, 'contas/cadastro.html', {'form': form})


@login_required
def perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)

    itens = request.user.itens.all()
    return render(request, 'contas/perfil.html', {'form': form, 'itens': itens})

def perfil_publico(request, username):
    perfil_usuario = get_object_or_404(Usuario, username=username)
    avaliacoes = perfil_usuario.avaliacoes_recebidas.select_related('avaliador').all()
    return render(request, 'contas/perfil_publico.html', {
        'perfil_usuario': perfil_usuario,
        'avaliacoes': avaliacoes,
    })
