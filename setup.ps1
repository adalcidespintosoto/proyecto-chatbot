# Script de configuración y preparación del entorno para UniMon Backend (USB)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Configuración del Entorno - Asistente UniMon Backend (USB)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verificar si Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python detectado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python no está instalado o no se encuentra en el PATH." -ForegroundColor Red
    exit 1
}

# 2. Crear entorno virtual si no existe
if (-not (Test-Path ".venv")) {
    Write-Host "[INFO] Creando entorno virtual en .venv..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "[OK] Entorno virtual creado exitosamente." -ForegroundColor Green
} else {
    Write-Host "[INFO] El entorno virtual .venv ya existe." -ForegroundColor DarkGray
}

# 3. Determinar ruta del ejecutable de Python en el venv
$venvPython = ".\.venv\Scripts\python.exe"
$venvPip = ".\.venv\Scripts\pip.exe"

# 4. Actualizar pip e instalar requerimientos
Write-Host "[INFO] Instalando y actualizando dependencias desde requirements.txt..." -ForegroundColor Yellow
& $venvPip install --upgrade pip
& $venvPip install -r requirements.txt

# 5. Asegurar archivo .env
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "[INFO] Creando .env a partir de .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "[OK] Archivo .env creado." -ForegroundColor Green
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " [ÉXITO] Entorno configurado correctamente." -ForegroundColor Green
Write-Host " Para iniciar el servidor, ejecuta: .\run.ps1" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
