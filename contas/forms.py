from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario


class CadastroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'foto_perfil', 'telefone', 'cidade', 'estado']

    def clean_email(self):
        email = self.cleaned_data['email']
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail.')
        return email


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'foto_perfil', 'telefone', 'cidade', 'estado']