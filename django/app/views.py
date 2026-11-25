from django.shortcuts import get_object_or_404, render, redirect
from .models import Contato, Servico, Categoria
from .forms import FormContato, FormServico
from .supabase_client import supabase
from .serializers import CategoriaSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.db.models import Sum, Count
import requests

# Create your views here.

def relatorios(request):
    servicos = Servico.objects.all()
    servicos_ativos = servicos.filter(ativo=True).count()
    servicos_inativos = servicos.filter(ativo=False).count()

    categorias = (servicos.values('categoria__nome').annotate(quantidade=Count('id')))

    return render(request, 'relatorio.html', {
        'servicos_ativos': servicos_ativos,
        'servicos_inativos': servicos_inativos,
        'categorias_labels' : [
            item['categoria__nome'] or 'Sem categoria'
            for item in categorias
        ],
        'categorias_valores': [
            item['quantidade']
            for item in categorias
        ],
    })


def buscar_integrantes():
    """Consulta os integrantes no Supabase. Retorna (lista, mensagem_de_erro)."""
    try:
        resposta = supabase.table("integrantes").select("*").order("id").execute()
        return resposta.data, None
    except Exception as e:
        return [], f"Não foi possível consultar os integrantes no Supabase: {e}"


def quem_somos(request):
    integrantes, erro = buscar_integrantes()
    return render(request, "quem-somos.html", {'integrantes': integrantes, 'erro': erro})


def integrantes(request):
    integrantes, erro = buscar_integrantes()
    return render(request, "integrantes.html", {'integrantes': integrantes, 'erro': erro})

def addIntegrante(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        cargo = request.POST.get("cargo")
        biografia = request.POST.get("biografia")
        foto = request.POST.get("foto")

        supabase.table("integrantes").insert({"nome": nome, "cargo": cargo, "biografia": biografia, "foto_url": foto}).execute()
        return redirect("integrantes")

    return render(request, "add-integrante.html")

def delIntegrante(request, id_integrante):
        supabase.table("integrantes").delete().eq("id", id_integrante).execute()
        return redirect("integrantes")

def index(request):
    return render(request, "index.html")

def servicos(request):
    # servicos = Servico.objects.all()

    servicos = Servico.objects.filter(ativo=True)
    servicos = servicos.exclude(preco=0)

    total_servicos = servicos.count()
    tem_servicos = servicos.exists()

    mais_barato = servicos.order_by('preco').first()
    mais_caro = servicos.order_by('-preco').first()

    # recupera o valor do form
    busca = request.GET.get('busca')

    if busca:
        servicos= servicos.filter(nome__icontains=busca)

    # recupera todas as categorias ativas
    categorias = Categoria.objects.filter(ativo=True)

    # recupera o valor do form ele cria a variavel categoria
    categoria = request.GET.get('categoria')

    # se uma categoria foi selecionada
    if categoria:
            # atualiza a lista de serviços de acordo com a categoria
            servicos = servicos.filter(categoria_id=categoria)


    preco = request.GET.get('preco')

    if preco == 'baixo' :
        servicos = servicos.filter(preco__lte=500)
    elif preco == 'medio':
        servicos = servicos.filter(
            preco__gte=500,
            preco__lte=1500
        )
    elif preco == 'alto':
        servicos = servicos.filter(preco__gt=1500)

    # recupera o valor da url
    ordem = request.GET.get('ordem')

    if ordem =='menor':
        servicos = servicos.order_by('preco') # ordena por preço (crescente)
    elif ordem == 'maior':
        servicos = servicos.order_by('-preco') # ordena por preço (descrescente)
    elif ordem == 'nome':
        servicos = servicos.order_by('nome') # ordena por nome (A-Z)
    else:
        servicos = servicos.order_by('nome')

    
    contexto = {
        'servicos': servicos,
        'total_servicos': total_servicos,
        'tem_servicos': tem_servicos,
        'mais_barato': mais_barato,
        'mais_caro': mais_caro,
        'categorias': categorias,
        'categoria': categoria,
        'preco': preco,
        'ordem': ordem

    }

    return render(request, "servicos.html", contexto)

def produtos(request):
    produtos = Servico.objects.filter(ativo=True)

    #servicos = Servico.object.all()
    #Requisição da API
    try:
        resposta = requests.get('https://fakestoreapi.com/products', timeout=10)
        resposta.raise_for_status()
        produtos_api = resposta.json()
    except (requests.RequestException, ValueError):
        produtos_api = []

    
    return render(request, "produtos.html", {'servicos': produtos, 'produtos_api': produtos_api})

def addServicos(request):
    form = FormServico(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('servicos')
    
    return render(request, "add-servicos.html", {'form': form})

def delServicos(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico)
    servico.delete()
    return redirect('servicos')

def editServicos(request, id_servico):
    servico = get_object_or_404(Servico, id=id_servico)
    form = FormServico(request.POST or None, request.FILES or None, instance=servico)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('servicos')
    
    return render(request, "edit-servicos.html", {'form': form})

def add_contato(request):
    form = FormContato(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("contatos")
    return render(request, "add-contato.html", {"form": form})

def contatos(request):
    return render(request, "contatos.html", {"contatos": Contato.objects.all()})

def del_contato(request, id_contato):
    contato = get_object_or_404(Contato, id=id_contato)
    contato.delete()
    return redirect("contatos")

@api_view(['GET', 'POST'])
def categoriasAPI(request):
    if request.method == 'GET' :
        categorias = Categoria.objects.all()
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CategoriaSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET', 'DELETE', 'PUT'])
def categoriaAPI(request, id_categoria):
    categoria = get_object_or_404(Categoria, id=id_categoria)
    if request.method == 'GET' :
        serializer = CategoriaSerializer(categoria)
        return Response(serializer.data)
    elif request.method == 'DELETE':
        categoria.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    elif request.method == 'PUT':
        serializer = CategoriaSerializer(categoria, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   