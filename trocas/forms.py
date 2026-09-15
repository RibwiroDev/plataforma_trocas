from django import forms
from catalogo.models import Item
from .models import Proposta


class PropostaForm(forms.ModelForm):
    class Meta:
        model = Proposta
        fields = ['item_ofertado', 'mensagem']
        widgets = {'mensagem': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Mensagem opcional para o dono do item'})}
        labels = {'item_ofertado': 'Qual dos seus itens você quer oferecer?'}

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        if usuario is not None:
            self.fields['item_ofertado'].queryset = Item.objects.filter(dono=usuario, status=Item.Status.DISPONIVEL)
