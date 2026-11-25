from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from .forms import CadastroForm
from .models import Perfil


@login_required
def dashboard(request):
    # superuser criado pelo createsuperuser não tem Perfil: get_or_create evita o erro 500
    perfil, _ = Perfil.objects.get_or_create(
        usuario=request.user,
        defaults={'tipo_usuario': 'administrador' if request.user.is_superuser else 'cliente'},
    )

    if request.user.is_superuser or perfil.tipo_usuario == 'administrador':
        return redirect("/admin/")

    return render(request, "dashboard.html")


@login_required
def perfil(request):
    if request.method == "POST":
        usuario = request.user
        usuario.first_name = request.POST.get("nome", "").strip()
        usuario.last_name = request.POST.get("sobrenome", "").strip()
        usuario.email = request.POST.get("email", "").strip()
        usuario.save()

        messages.success(request, "Seus dados foram atualizados.")
        return redirect("perfil")

    return render(request, "perfil.html")


class AlterarSenhaView(SuccessMessageMixin, PasswordChangeView):
    template_name = "alterar_senha.html"
    success_url = reverse_lazy("perfil")
    success_message = "Sua senha foi alterada com sucesso."


def cadastro(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST)

        if form.is_valid():
            usuario = form.save()
            Perfil.objects.create(usuario=usuario, tipo_usuario='cliente')
            messages.success(request, "Conta criada! Agora é só entrar com seu usuário e senha.")
            return redirect('login')
    else:
        form = CadastroForm()

    return render(request, 'cadastro.html', {'form': form})
