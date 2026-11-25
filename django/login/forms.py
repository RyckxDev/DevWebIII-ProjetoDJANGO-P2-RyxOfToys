from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CadastroForm(UserCreationForm):

    email = forms.EmailField(label="E-mail", required=True)

    class Meta:
        model = User
        fields = ('username', 'email')  # password1 e password2 já vêm do UserCreationForm

        labels = {
            'username': 'Nome de usuário',
        }
        