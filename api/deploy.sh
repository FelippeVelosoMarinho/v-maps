#!/bin/bash
# Deploy script para V-Maps Backend
# Uso: ./deploy.sh <version>
# Exemplo: ./deploy.sh 1.0.0

set -e

VERSION=${1:-"latest"}
IMAGE_NAME="v-maps-backend"

echo "=========================================="
echo "🚀 Deploy V-Maps Backend v${VERSION}"
echo "=========================================="

# 1. Pull das últimas alterações
echo "📥 Atualizando repositório..."
git pull origin main

# 2. Build da imagem Docker
echo "🔨 Building Docker image: ${IMAGE_NAME}:${VERSION}..."
docker build -t ${IMAGE_NAME}:${VERSION} .

# 3. Tag como latest também
if [ "$VERSION" != "latest" ]; then
    echo "🏷️  Tagging as latest..."
    docker tag ${IMAGE_NAME}:${VERSION} ${IMAGE_NAME}:latest
fi

echo "=========================================="
echo "✅ Build concluído!"
echo ""
echo "Imagem criada: ${IMAGE_NAME}:${VERSION}"
echo ""
echo "📋 Próximos passos no Portainer:"
echo "   1. Acesse tsportainer.ciano.io"
echo "   2. Abra o container desejado"
echo "   3. Em 'Edit', altere a versão para: ${VERSION}"
echo "   4. Clique em 'Rerun jobs'"
echo "=========================================="
