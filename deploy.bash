#!/bin/bash

set -e  # Прерывать скрипт при ошибке

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Начинаем деплой проекта в Kubernetes...${NC}"

# Проверка, запущен ли Minikube
if ! minikube status | grep -q "host: Running"; then
    echo -e "${RED}❌ Minikube не запущен. Запустите 'minikube start' сначала.${NC}"
    exit 1
fi

# Включение ingress
echo -e "${YELLOW}📦 Включаем ingress addon...${NC}"
minikube addons enable ingress

# Применение манифестов по порядку
echo -e "${YELLOW}📁 Применяем манифесты...${NC}"

echo -e "  - Namespace"
kubectl apply -f k8s/namespace.yaml

echo -e "  - ConfigMap"
kubectl apply -f k8s/configmap.yaml

echo -e "  - Secrets"
kubectl apply -f k8s/secrets.yaml

# Создание registry secret
if [ -z "$REGISTRY_TOKEN" ]; then
    echo -e "${YELLOW}🔑 Enter token for registry.gitlab.akhcheck.ru:${NC}"
    read -r registryToken
else
    registryToken="$REGISTRY_TOKEN"
fi

echo -e "  - Registry secret"
kubectl delete secret registrysecret -n hl-project 2>/dev/null || true
kubectl create secret docker-registry registrysecret \
    --docker-server=registry.gitlab.akhcheck.ru \
    --docker-username=dmitrii.boldyrev \
    --docker-password="$registryToken" \
    --docker-email=daboldyrev@edu.hse.ru \
    -n hl-project

echo -e "  - PVC"
kubectl apply -f k8s/pvc/

echo -e "  - StatefulSet (PostgreSQL, RabbitMQ)"
kubectl apply -f k8s/statefulset/

echo -e "  - Job (миграции)"
kubectl apply -f k8s/job/migrate-job.yaml

echo -e "  - Deployments"
kubectl apply -f k8s/deployment/

echo -e "  - Services"
kubectl apply -f k8s/service/

echo -e "  - Ingress"
kubectl apply -f k8s/ingress.yaml

echo -e "${GREEN}✅ Все манифесты применены!${NC}"
echo ""
echo -e "${CYAN}📊 Статус подов:${NC}"
kubectl get pods -n hl-project

echo ""
echo -e "${MAGENTA}🚇 Добавьте в /etc/hosts строку: $(minikube ip) hl-project.test${NC}"
echo -e "${MAGENTA}🌐 После этого приложение будет доступно по адресу: http://hl-project.test${NC}"
