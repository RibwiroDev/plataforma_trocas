from django import forms
from contas.forms import LocalidadeFormMixin

from .models import Item


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.ImageField):
    """Permite selecionar várias fotos de uma vez no mesmo campo."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput(attrs={"accept": "image/*"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        for arquivo in data if isinstance(data, (list, tuple)) else [data]:
            if arquivo and arquivo.size > 4_000_000:
                raise forms.ValidationError('Cada foto deve ter até 4 MB.')
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class ItemForm(LocalidadeFormMixin, forms.ModelForm):
    imagens = MultipleFileField(required=False, label='Fotos do item')

    class Meta:
        model = Item
        fields = ['titulo', 'descricao', 'categoria', 'estado_conservacao', 'estado', 'cidade', 'aceita_categoria', 'aceita_descricao_livre']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'aceita_descricao_livre': forms.TextInput(attrs={'placeholder': 'Ex: aceito qualquer instrumento musical'}),
        }
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
            'estado_conservacao': 'Estado de conservação',
            'aceita_categoria': 'Categoria que eu aceito em troca',
            'aceita_descricao_livre': 'Ou descreva livremente o que aceita',
        }
