from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
# form do usuario
from django.contrib.auth.forms import UserCreationForm
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

        usuario.first_name = request.POST.get("nome")
        usuario.last_name = request.POST.get("sobrenome")
        usuario.email = request.POST.get("email")

        usuario.save()

        return redirect("dashboard")

    return render(request, "perfil.html")



def cadastro(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST)

        if form.is_valid():
            usuario = form.save()
            Perfil.objects.create(usuario=usuario, tipo_usuario='cliente')
            return redirect('login')
    else:
        form = CadastroForm()
    
    return render(request, 'cadastro.html', {'form': form})