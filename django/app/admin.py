from django.contrib import admin
from .models import Categoria, Servico

# Register your models here.
admin.site.register(Categoria)

# admin.site.register(Servico)

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ["nome", "descricao", "preco", "imagem", "categoria", "ativo"]
    list_filter = ["categoria", "ativo"]
    search_fields = ["nome", "descricao"]
    ordering = ["nome", "preco"]
    list_per_page = 25