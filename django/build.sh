#!/usr/bin/env bash
# Script de build executado pelo Render a cada deploy.
set -o errexit

pip install -r requirements.txt

# junta o CSS e os arquivos do admin em staticfiles/ (servidos pelo WhiteNoise)
python manage.py collectstatic --no-input

# cria/atualiza as tabelas no PostgreSQL do Supabase
python manage.py migrate

# o disco do Render é temporário: copia as imagens dos brinquedos para media/
mkdir -p media
cp -r seed_media/. media/
