#!/usr/bin/env pwsh
# deploy.ps1 - Скрипт для деплоя проекта в Minikube (Windows)

Write-Host "Start deploying in Kubernetes..." -ForegroundColor Green

$minikubeStatus = minikube status --format '{{.Host}}' 2>$null
if ($minikubeStatus -ne "Running") {
    Write-Host "Minikube is not started. Start 'minikube start' before." -ForegroundColor Red
    exit 1
}

Write-Host "Turn on ingress addon..." -ForegroundColor Yellow
minikube addons enable ingress

Write-Host "Apply manifests..." -ForegroundColor Yellow

Write-Host "  - Namespace"
kubectl apply -f k8s/namespace.yaml

Write-Host "  - ConfigMap"
kubectl apply -f k8s/configmap.yaml

Write-Host "  - Secrets"
kubectl apply -f k8s/secrets.yaml

$registryToken = $env:REGISTRY_TOKEN
if (-not $registryToken) {
    $registryToken = Read-Host -Prompt "Enter token for registry.gitlab.akhcheck.ru"
}
Write-Host "  - Registry secret"
kubectl delete secret registrysecret -n hl-project 2>$null
kubectl create secret docker-registry registrysecret `
    --docker-server=registry.gitlab.akhcheck.ru `
    --docker-username=dmitrii.boldyrev `
    --docker-password=$registryToken `
    --docker-email=daboldyrev@edu.hse.ru `
    -n hl-project

Write-Host "  - PVC"
kubectl apply -f k8s/pvc/

Write-Host "  - StatefulSet - PostgreSQL и RabbitMQ"
kubectl apply -f k8s/statefulset/

Write-Host "  - Job - миграции"
kubectl apply -f k8s/job/migrate-job.yaml

Write-Host "  - Deployments"
kubectl apply -f k8s/deployment/

Write-Host "  - Services"
kubectl apply -f k8s/service/

Write-Host "  - Ingress"
kubectl apply -f k8s/ingress.yaml

Write-Host "All manifest were applied!" -ForegroundColor Green
Write-Host ""
Write-Host "Pods status:" -ForegroundColor Cyan
kubectl get pods -n hl-project

Write-Host ""
Write-Host "Launch in other terminal: minikube tunnel" -ForegroundColor Magenta
Write-Host "Application will be accessible at: http://hl-project.test" -ForegroundColor Magenta
