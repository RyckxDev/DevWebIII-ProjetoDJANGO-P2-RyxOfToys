# Como rodar o projeto

Passo a passo para rodar o projeto em qualquer PC (em casa ou na faculdade).

## Pré-requisitos

- **Python 3.13 ou 3.14** instalado. Para conferir, rode `python --version` ou `py --version`.
- **Git**, se for clonar o repositório.

## 1. Pegar o projeto

```powershell
git clone <url-do-repositorio>
cd DevWebIII-ProjetoP2\django
```

Se o projeto veio por pendrive ou zip, basta entrar na pasta `django`.

## 2. Criar o ambiente virtual

> A pasta `venv/` **não vai para o git** e **não funciona se for copiada de outro PC**.
> Ela guarda o caminho do Python da máquina onde foi criada. Se você copiar a venv
> de outro PC, vai aparecer o erro `did not find executable at ...python.exe`.
> Por isso, crie uma venv nova em cada computador.

```powershell
python -m venv venv
```

Se `python` não for reconhecido, use `py -m venv venv`.

Se já existir uma `venv` copiada de outro PC, apague a pasta `venv` antes de criar a nova.

## 3. Ativar o ambiente virtual

```powershell
.\venv\Scripts\activate
```

Quando a venv estiver ativa, o terminal mostra `(venv)` no começo da linha.

**Se o PowerShell bloquear o script** (erro "a execução de scripts foi desabilitada"), rode este comando e tente de novo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

O comando só vale para o terminal aberto e não precisa de administrador.
Outra opção é usar o **cmd** em vez do PowerShell: `venv\Scripts\activate.bat`

## 4. Instalar as dependências

```powershell
pip install -r requirements.txt
```

## 5. Criar o arquivo `.env`

O `.env` guarda as chaves do Supabase e **não vai para o git**, por segurança.
Crie o arquivo `django\.env` (na mesma pasta do `manage.py`) com este conteúdo:

```
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_KEY=sua-chave-aqui
```

Os valores ficam no painel do Supabase, em **Project Settings → API**.

> Sem o `.env`, o projeto não inicia e mostra o erro `Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env`.

## 6. Preparar o banco de dados

O `db.sqlite3` e a pasta `media/` (imagens dos serviços) também **não vão para o git**.
Em um PC novo, é preciso criar o banco:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

O `createsuperuser` cria o usuário admin. Ao fazer login com ele, você é levado direto para o `/admin/`.

> Se quiser levar os dados que você já cadastrou (serviços, usuários, imagens), copie
> o arquivo `db.sqlite3` e a pasta `media/` por pendrive ou nuvem para dentro da pasta `django`.
> Nesse caso, não precisa rodar o `createsuperuser`.

## 7. Rodar o servidor

```powershell
python manage.py runserver
```

Acesse no navegador: **http://127.0.0.1:8000/**

Para parar o servidor, use `Ctrl + C`.

---

## Resumo rápido (PC novo)

```powershell
cd DevWebIII-ProjetoP2\django
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
# criar o arquivo .env com SUPABASE_URL e SUPABASE_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Resumo rápido (PC onde já rodou antes)

```powershell
cd DevWebIII-ProjetoP2\django
.\venv\Scripts\activate
python manage.py runserver
```

## Problemas comuns

| Erro | Solução |
|---|---|
| `did not find executable at '...python.exe'` | A venv veio de outro PC. Apague a pasta `venv` e repita os passos 2 a 4. |
| `ModuleNotFoundError: No module named 'django'` (ou `supabase`, `dotenv`...) | A venv não está ativada (passo 3) ou faltou o `pip install -r requirements.txt` (passo 4). |
| `Configure SUPABASE_URL e SUPABASE_KEY no arquivo .env` | Falta o arquivo `.env` (passo 5). |
| `no such table: ...` | Faltou rodar `python manage.py migrate` (passo 6). |
| Página Equipe mostra `Could not find the table 'public.integrantes'` | Falta criar a tabela `integrantes` no Supabase, com as colunas `id`, `nome`, `cargo`, `biografia` e `foto_url`. |
| `That port is already in use` | Já existe um servidor rodando. Feche o outro terminal ou use outra porta: `python manage.py runserver 8001`. |
| Imagens dos serviços não aparecem | A pasta `media/` não foi copiada. Cadastre as imagens de novo ou copie a pasta. |
