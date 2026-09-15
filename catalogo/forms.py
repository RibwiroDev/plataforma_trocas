from django import forms
from .models import Item


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Permite selecionar várias fotos de uma vez no mesmo campo."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class ItemForm(forms.ModelForm):
    imagens = MultipleFileField(required=False, label='Fotos do item')

    class Meta:
        model = Item
        fields = ['titulo', 'descricao', 'categoria', 'estado_conservacao', 'aceita_categoria', 'aceita_descricao_livre']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
            'aceita_descricao_livre': forms.TextInput(attrs={'placeholder': 'Ex: aceito qualquer instrumento musical'}),
        }
        labels = {
            'aceita_categoria': 'Categoria que eu aceito em troca',
            'aceita_descricao_livre': 'Ou descreva livremente o que aceita',
        }
