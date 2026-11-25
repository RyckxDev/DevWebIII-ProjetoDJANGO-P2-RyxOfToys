from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("perfil/", views.perfil, name="perfil"),

    path("alterar-senha/", views.AlterarSenhaView.as_view(), name="alterar_senha"),

    path("cadastro/", views.cadastro, name='cadastro'),

    # Recuperação de senha: mecanismo nativo do Django (templates padrão do admin).
    # Os nomes das rotas precisam ser exatamente estes, pois as views do Django os usam.
    path("senha/recuperar/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("senha/recuperar/enviado/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("senha/redefinir/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("senha/redefinir/concluido/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
