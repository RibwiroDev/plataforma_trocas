from django import forms
from catalogo.models import Item
from .models import Avaliacao, Mensagem, Proposta


class PropostaForm(forms.ModelForm):
    mensagem = forms.CharField(
        max_length=1000, required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Mensagem opcional para o dono do item'}),
    )

    class Meta:
        model = Proposta
        fields = ['item_ofertado', 'mensagem']
        labels = {'item_ofertado': 'Qual dos seus itens você quer oferecer?'}

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        if usuario is not None:
            self.fields['item_ofertado'].queryset = Item.objects.filter(dono=usuario, status=Item.Status.DISPONIVEL)


class AvaliacaoForm(forms.ModelForm):
    comentario = forms.CharField(
        max_length=1000, required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Como foi a troca? (opcional)'}),
    )

    class Meta:
        model = Avaliacao
        fields = ['nota', 'comentario']
        labels = {'nota': 'Nota (1 a 5)'}


class MensagemForm(forms.ModelForm):
    texto = forms.CharField(
        max_length=2000, label='',
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Escreva uma mensagem...', 'maxlength': 2000}),
    )

    class Meta:
        model = Mensagem
        fields = ['texto']
