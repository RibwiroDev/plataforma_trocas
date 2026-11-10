from functools import lru_cache
import json
from pathlib import Path

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.templatetags.static import static

from .models import Usuario


@lru_cache(maxsize=1)
def localidades():
    arquivo = Path(__file__).parent / 'static' / 'contas' / 'localidades.json'
    with arquivo.open(encoding='utf-8') as dados:
        return json.load(dados)


class LocalidadeFormMixin:
    class Media:
        js = ('contas/localidades.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localidade_anterior = (self.instance.estado, self.instance.cidade) if self.instance.pk else ('', '')
        estados = localidades()
        uf = self['estado'].value() or ''
        uf_anterior, cidade_anterior = self.localidade_anterior
        opcoes_uf = [('', 'Selecione o estado')]
        opcoes_uf.extend((sigla, dados['nome']) for sigla, dados in estados.items())
        if uf_anterior and uf_anterior not in estados:
            opcoes_uf.append((uf_anterior, uf_anterior))
        municipios = estados.get(uf, {}).get('municipios', [])
        opcoes_cidade = [('', 'Selecione o município')]
        opcoes_cidade.extend((nome, nome) for nome in municipios)
        if uf == uf_anterior and cidade_anterior and cidade_anterior not in municipios:
            opcoes_cidade.append((cidade_anterior, cidade_anterior))
        self.fields['estado'].widget = forms.Select(choices=opcoes_uf, attrs={
            'data-localidades': static('contas/localidades.json'),
        })
        self.fields['cidade'].label = 'Município'
        self.fields['cidade'].widget = forms.Select(choices=opcoes_cidade)

    def clean(self):
        dados = super().clean()
        uf = dados.get('estado', '')
        cidade = dados.get('cidade', '')
        if (uf, cidade) in (('', ''), self.localidade_anterior):
            return dados
        estados = localidades()
        if uf not in estados:
            self.add_error('estado', 'Selecione um estado válido.')
        elif cidade not in estados[uf]['municipios']:
            self.add_error('cidade', 'Selecione um município do estado informado.')
        return dados


class CadastroForm(LocalidadeFormMixin, UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'foto_perfil', 'telefone', 'estado', 'cidade']

    def clean_email(self):
        email = self.cleaned_data['email']
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail.')
        return email


class PerfilForm(LocalidadeFormMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'foto_perfil', 'telefone', 'estado', 'cidade']
