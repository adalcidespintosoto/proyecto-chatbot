# Script de ejecución del servidor FastAPI para UniMon Backend (USB)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Iniciando Servidor UniMon Backend - Universidad Simón Bolívar" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$venvUvicorn = ".\.venv\Scripts\uvicorn.exe"

if (-not (Test-Path $venvUvicorn)) {
    Write-Host "[ADVERTENCIA] No se encontró el entorno virtual. Intentando ejecutar con uvicorn global o ejecutando setup..." -ForegroundColor Yellow
    if (Test-Path "setup.ps1") {
        Write-Host "[INFO] Ejecutando setup.ps1 primero..." -ForegroundColor Yellow
        .\setup.ps1
    }
}

Write-Host "[INFO] Levantando servidor Uvicorn en http://localhost:8000 (Docs: http://localhost:8000/docs)..." -ForegroundColor Cyan
& $venvUvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
