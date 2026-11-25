from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Min, Max
from django.http import Http404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
import logging
import requests
from decimal import Decimal

from .models import Contato, Servico, Categoria, Pedido
from .forms import FormContato, FormServico
from .supabase_client import supabase
from .serializers import CategoriaSerializer

logger = logging.getLogger(__name__)


# Atalho: exige login e, se a pessoa estiver logada mas sem a permissão, devolve 403
def requer_permissao(perm):
    def decorator(view):
        return login_required(permission_required(perm, raise_exception=True)(view))
    return decorator


# =====================================================================
# Páginas públicas
# =====================================================================

def index(request):
    return render(request, "index.html")


def quem_somos(request):
    integrantes, erro = buscar_integrantes()
    return render(request, "quem-somos.html", {'integrantes': integrantes, 'erro': erro})


HEADERS_API = {
    # alguns serviços atrás do Cloudflare recusam o user-agent padrão "python-requests"
    'User-Agent': 'Mozilla/5.0 (compatible; RyxOfToys/1.0; projeto academico Django)',
    'Accept': 'application/json',
}


def buscar_produtos_parceiros():
    """Busca os produtos das lojas parceiras (API externa).

    Tenta a Fake Store API; se ela falhar (ex.: bloqueio do Cloudflare a servidores
    na nuvem, como o Render), usa a DummyJSON. Os dois formatos são convertidos
    para os mesmos campos usados no template: title, description, price, image.
    """
    try:
        resposta = requests.get('https://fakestoreapi.com/products', headers=HEADERS_API, timeout=10)
        resposta.raise_for_status()
        return resposta.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning("Fake Store API indisponível (%s). Usando DummyJSON.", e)

    try:
        resposta = requests.get('https://dummyjson.com/products/category/sports-accessories', headers=HEADERS_API, timeout=10)
        resposta.raise_for_status()
        return [
            {
                'title': p.get('title'),
                'description': p.get('description'),
                'price': p.get('price'),
                'image': p.get('thumbnail'),
            }
            for p in resposta.json().get('products', [])
        ]
    except (requests.RequestException, ValueError) as e:
        logger.error("DummyJSON também indisponível (%s).", e)
        return []


def produtos(request):
    produtos = Servico.objects.filter(ativo=True).order_by('nome')
    produtos_api = buscar_produtos_parceiros()
    return render(request, "produtos.html", {'servicos': produtos, 'produtos_api': produtos_api})


def add_contato(request):
    form = FormContato(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Mensagem enviada! Obrigado por entrar em contato conosco.")
        return redirect("add_contato")
    return render(request, "add-contato.html", {"form": form})


# =====================================================================
# Pedidos (cliente logado)
# =====================================================================

@login_required
@require_POST
def comprar(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico, ativo=True)
    Pedido.objects.create(
        usuario=request.user,
        servico=servico,
        nome_servico=servico.nome,
        preco=servico.preco,
    )
    messages.success(request, f'"{servico.nome}" foi adicionado aos seus pedidos.')
    return redirect('meus_pedidos')


@login_required
def meus_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user).select_related('servico')
    # O SQLite soma decimais como float (ex.: 299.900000000000), então arredonda para centavos
    total = pedidos.aggregate(total=Sum('preco'))['total'] or Decimal('0')
    total = Decimal(total).quantize(Decimal('0.01'))
    return render(request, "meus-pedidos.html", {'pedidos': pedidos, 'total': total})


# =====================================================================
# Contatos (área restrita)
# =====================================================================

@requer_permissao('app.view_contato')
def contatos(request):
    contatos = Contato.objects.all().order_by('-id')
    return render(request, "contatos.html", {"contatos": contatos})


@requer_permissao('app.delete_contato')
@require_POST
def del_contato(request, id_contato):
    contato = get_object_or_404(Contato, id=id_contato)
    contato.delete()
    messages.success(request, "Contato excluído.")
    return redirect("contatos")


# =====================================================================
# Serviços (área restrita)
# =====================================================================

@requer_permissao('app.view_servico')
def servicos(request):
    todos = Servico.objects.all()

    # Estatísticas sobre todos os serviços cadastrados
    estatisticas = todos.aggregate(menor=Min('preco'), maior=Max('preco'))
    total_servicos = todos.count()
    servicos_ativos = todos.filter(ativo=True).count()

    servicos = todos.select_related('categoria')

    # Busca por nome
    busca = request.GET.get('busca', '').strip()
    if busca:
        servicos = servicos.filter(nome__icontains=busca)

    # Filtro por categoria
    categorias = Categoria.objects.filter(ativo=True)
    categoria = request.GET.get('categoria')
    if categoria:
        servicos = servicos.filter(categoria_id=categoria)

    # Filtro por faixa de preço
    preco = request.GET.get('preco')
    if preco == 'baixo':
        servicos = servicos.filter(preco__lte=500)
    elif preco == 'medio':
        servicos = servicos.filter(preco__gt=500, preco__lte=1500)
    elif preco == 'alto':
        servicos = servicos.filter(preco__gt=1500)

    # Ordenação
    ordem = request.GET.get('ordem')
    if ordem == 'menor':
        servicos = servicos.order_by('preco')
    elif ordem == 'maior':
        servicos = servicos.order_by('-preco')
    else:
        servicos = servicos.order_by('nome')

    contexto = {
        'servicos': servicos,
        'total_servicos': total_servicos,
        'servicos_ativos': servicos_ativos,
        'servicos_inativos': total_servicos - servicos_ativos,
        'menor_preco': estatisticas['menor'],
        'maior_preco': estatisticas['maior'],
        'categorias': categorias,
        'busca': busca,
        'categoria': categoria,
        'preco': preco,
        'ordem': ordem,
    }
    return render(request, "servicos.html", contexto)


@requer_permissao('app.add_servico')
def addServicos(request):
    form = FormServico(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        servico = form.save()
        messages.success(request, f'Serviço "{servico.nome}" cadastrado.')
        return redirect('servicos')

    return render(request, "add-servicos.html", {'form': form})


@requer_permissao('app.change_servico')
def editServicos(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico)
    form = FormServico(request.POST or None, request.FILES or None, instance=servico)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Serviço "{servico.nome}" atualizado.')
        return redirect('servicos')

    return render(request, "edit-servicos.html", {'form': form, 'servico': servico})


@requer_permissao('app.delete_servico')
@require_POST
def delServicos(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico)
    servico.delete()
    messages.success(request, f'Serviço "{servico.nome}" excluído.')
    return redirect('servicos')


# =====================================================================
# Equipe / integrantes no Supabase (área restrita)
# =====================================================================

def buscar_integrantes():
    """Consulta os integrantes no Supabase. Retorna (lista, mensagem_de_erro)."""
    try:
        resposta = supabase.table("integrantes").select("*").order("id").execute()
        return resposta.data, None
    except Exception as e:
        return [], f"Não foi possível consultar os integrantes no Supabase: {e}"


def dados_integrante(request):
    return {
        "nome": request.POST.get("nome", "").strip(),
        "cargo": request.POST.get("cargo", "").strip(),
        "biografia": request.POST.get("biografia", "").strip(),
        "foto_url": request.POST.get("foto", "").strip(),
    }


@requer_permissao('app.gerenciar_equipe')
def integrantes(request):
    integrantes, erro = buscar_integrantes()
    return render(request, "integrantes.html", {'integrantes': integrantes, 'erro': erro})


@requer_permissao('app.gerenciar_equipe')
def addIntegrante(request):
    if request.method == "POST":
        dados = dados_integrante(request)
        supabase.table("integrantes").insert(dados).execute()
        messages.success(request, f'Integrante "{dados["nome"]}" cadastrado.')
        return redirect("integrantes")

    return render(request, "add-integrante.html")


@requer_permissao('app.gerenciar_equipe')
def editIntegrante(request, id_integrante):
    resultado = supabase.table("integrantes").select("*").eq("id", id_integrante).execute().data
    if not resultado:
        raise Http404("Integrante não encontrado.")
    integrante = resultado[0]

    if request.method == "POST":
        dados = dados_integrante(request)
        supabase.table("integrantes").update(dados).eq("id", id_integrante).execute()
        messages.success(request, f'Integrante "{dados["nome"]}" atualizado.')
        return redirect("integrantes")

    return render(request, "edit-integrante.html", {'integrante': integrante})


@requer_permissao('app.gerenciar_equipe')
@require_POST
def delIntegrante(request, id_integrante):
    supabase.table("integrantes").delete().eq("id", id_integrante).execute()
    messages.success(request, "Integrante excluído.")
    return redirect("integrantes")


# =====================================================================
# Relatórios (área restrita)
# =====================================================================

@requer_permissao('app.ver_relatorios')
def relatorios(request):
    servicos = Servico.objects.all()
    total_servicos = servicos.count()
    servicos_ativos = servicos.filter(ativo=True).count()
    servicos_inativos = total_servicos - servicos_ativos

    categorias = servicos.values('categoria__nome').annotate(quantidade=Count('id')).order_by('categoria__nome')

    return render(request, 'relatorio.html', {
        'total_servicos': total_servicos,
        'servicos_ativos': servicos_ativos,
        'servicos_inativos': servicos_inativos,
        'categorias_labels': [item['categoria__nome'] or 'Sem categoria' for item in categorias],
        'categorias_valores': [item['quantidade'] for item in categorias],
    })


# =====================================================================
# API REST de categorias
# =====================================================================

@api_view(['GET', 'POST'])
def categoriasAPI(request):
    if request.method == 'GET':
        categorias = Categoria.objects.all()
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data)

    serializer = CategoriaSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE', 'PUT'])
def categoriaAPI(request, id_categoria):
    categoria = get_object_or_404(Categoria, id=id_categoria)

    if request.method == 'GET':
        serializer = CategoriaSerializer(categoria)
        return Response(serializer.data)

    if request.method == 'DELETE':
        categoria.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = CategoriaSerializer(categoria, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
