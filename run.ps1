[CmdletBinding()]
param(
    [switch]$Tunnel,
    [int]$Port = 8000,
    [string]$HostIP = "0.0.0.0"
)

<#
.SYNOPSIS
    Script de arranque y orquestacion para el Asistente UniMon (Universidad Simon Bolivar).
.DESCRIPTION
    1. Verifica e inicializa el entorno virtual (.venv).
    2. Comprueba y levanta el servicio local de Ollama e inspecciona el modelo institucional unimon:8b.
    3. Detecta la direccion IP local (LAN) y GPU activa (NVIDIA RTX 2000 Ada / CUDA).
    4. Opcionalmente inicia un tunel publico seguro con Cloudflare (cloudflared).
    5. Ejecuta el servidor ASGI FastAPI con Uvicorn en 0.0.0.0:8000 con recarga en caliente.
    6. Maneja senales de interrupcion (Ctrl+C) limpiando subprocesos asociados.
.PARAMETER Tunnel
    Activa un tunel Cloudflare para generar una URL publica temporal hacia el asistente.
.PARAMETER Port
    Puerto HTTP de escucha del servidor (por defecto 8000).
.PARAMETER HostIP
    Direccion IP de escucha (por defecto 0.0.0.0).
.EXAMPLE
    .\run.ps1
.EXAMPLE
    .\run.ps1 -Tunnel
.EXAMPLE
    .\run.ps1 -Port 8080
#>

$tunnelProcess = $null

try {
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host " [UNIMON] ASISTENTE VIRTUAL DE SOPORTE TECNICO TI N1 (UNISIMON)          " -ForegroundColor Green
    Write-Host "==========================================================================" -ForegroundColor Cyan

    # -------------------------------------------------------------------------
    # 1. VERIFICACION DEL ENTORNO VIRTUAL
    # -------------------------------------------------------------------------
    $venvPath = ".\.venv"
    $venvUvicorn = ".\.venv\Scripts\uvicorn.exe"
    $venvPython = ".\.venv\Scripts\python.exe"

    if (-not (Test-Path $venvUvicorn)) {
        Write-Host "`n[1/5] [ADVERTENCIA] Entorno virtual no encontrado o incompleto en '$venvPath'." -ForegroundColor Yellow
        if (Test-Path "setup.ps1") {
            Write-Host "      Invocando 'setup.ps1' para preparar el entorno virtual y dependencias..." -ForegroundColor Cyan
            & .\setup.ps1
        } else {
            Write-Host "      [ERROR] No se encontro el archivo 'setup.ps1'. Por favor crea el entorno con: python -m venv .venv" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "`n[1/5] [OK] Entorno virtual (.venv) verificado correctamente." -ForegroundColor Green
    }

    # -------------------------------------------------------------------------
    # 2. COMPROBACION DE SERVICIOS E INFRAESTRUCTURA DE IA (GEMINI / OPENAI / OLLAMA)
    # -------------------------------------------------------------------------
    Write-Host "[2/5] Verificando proveedor de IA (LLM)..." -ForegroundColor Cyan
    
    $provider = "gemini"
    $openaiKey = ""
    $openaiModel = "gpt-5.6-luna"
    $geminiKey = ""
    $geminiModel = "gemini-flash-lite-latest"
    if (Test-Path ".env") {
        $envLines = Get-Content ".env"
        foreach ($line in $envLines) {
            if ($line -match '^\s*LLM_PROVIDER\s*=\s*(.+)') { $provider = $matches[1].Trim().ToLower() }
            if ($line -match '^\s*OPENAI_API_KEY\s*=\s*(.+)') { $openaiKey = $matches[1].Trim() }
            if ($line -match '^\s*OPENAI_MODEL\s*=\s*(.+)') { $openaiModel = $matches[1].Trim() }
            if ($line -match '^\s*GEMINI_API_KEY\s*=\s*(.+)') { $geminiKey = $matches[1].Trim() }
            if ($line -match '^\s*GEMINI_MODEL\s*=\s*(.+)') { $geminiModel = $matches[1].Trim() }
        }
    }

    if ($provider -eq "gemini" -and $geminiKey -and ($geminiKey -notmatch "tu_gemini")) {
        Write-Host "      [OK] Proveedor en la nube: Google Gemini ($geminiModel)" -ForegroundColor Green
        Write-Host "           [ESTRICTO] Modelo local (Ollama) DESHABILITADO. Modo 100% Cloud activo." -ForegroundColor Yellow
        Write-Host "           Toda inferencia y generacion se procesa exclusivamente con Gemini." -ForegroundColor DarkGray
    } elseif ($provider -eq "openai" -and $openaiKey -and ($openaiKey -notmatch "tu_openai")) {
        Write-Host "      [OK] Proveedor en la nube: OpenAI ($openaiModel)" -ForegroundColor Green
        Write-Host "           [ESTRICTO] Modelo local (Ollama) DESHABILITADO. Modo 100% Cloud activo." -ForegroundColor Yellow
        Write-Host "           Toda inferencia y generacion se procesa exclusivamente con OpenAI." -ForegroundColor DarkGray
    } else {
        Write-Host "      Proveedor configurado: Ollama Local" -ForegroundColor Cyan
        $ollamaApiUrl = "http://localhost:11434/api/tags"
        $ollamaRunning = $false
        $tagsResponse = $null
        
        try {
            $tagsResponse = Invoke-RestMethod -Uri $ollamaApiUrl -TimeoutSec 2 -ErrorAction Stop
            $ollamaRunning = $true
        } catch {
            $ollamaRunning = $false
        }

        if (-not $ollamaRunning) {
            Write-Host "      Ollama no esta en ejecucion. Intentando iniciar servicio en segundo plano..." -ForegroundColor Yellow
            $ollamaCmd = Get-Command "ollama" -ErrorAction SilentlyContinue
            if ($ollamaCmd) {
                Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
                $retryCount = 0
                while ($retryCount -lt 8 -and -not $ollamaRunning) {
                    Start-Sleep -Seconds 1
                    $retryCount++
                    try {
                        $tagsResponse = Invoke-RestMethod -Uri $ollamaApiUrl -TimeoutSec 2 -ErrorAction Stop
                        $ollamaRunning = $true
                    } catch {
                        $ollamaRunning = $false
                    }
                }
            }
        }

        if ($ollamaRunning) {
            Write-Host "      [OK] Ollama activo y respondiendo en http://localhost:11434" -ForegroundColor Green
            
            $availableModels = @()
            if ($tagsResponse -and $tagsResponse.models) {
                $availableModels = $tagsResponse.models | ForEach-Object { $_.name }
            }
            
            $hasUnimonModel = $availableModels | Where-Object { $_ -like "unimon:8b*" -or $_ -like "unimon:latest*" }
            if ($hasUnimonModel) {
                Write-Host "      [OK] Modelo institucional '$hasUnimonModel' listo en memoria." -ForegroundColor Green
            } else {
                Write-Host "      [ADVERTENCIA] Modelo 'unimon:8b' no detectado en Ollama." -ForegroundColor Yellow
                if (Test-Path "Modelfile") {
                    Write-Host "      Creando modelo 'unimon:8b' a partir de Modelfile..." -ForegroundColor Cyan
                    & ollama create unimon:8b -f ./Modelfile
                } else {
                    Write-Host "      Recuerda crearlo ejecutando: ollama create unimon:8b -f ./Modelfile" -ForegroundColor DarkGray
                }
            }
        } else {
            Write-Host "      [AVISO] No se pudo conectar con Ollama en http://localhost:11434." -ForegroundColor Yellow
            Write-Host "              Asegurate de iniciar Ollama antes de realizar consultas conversacionales." -ForegroundColor DarkGray
        }
    }

    # -------------------------------------------------------------------------
    # 3. DETECCION DE HARDWARE (GPU) Y RED LOCAL (LAN)
    # -------------------------------------------------------------------------
    Write-Host "[3/5] Detectando configuracion de red y hardware de aceleracion..." -ForegroundColor Cyan

    # Deteccion de IP Local LAN
    $localIP = "127.0.0.1"
    try {
        $ipCandidates = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object {
                $_.InterfaceAlias -notmatch 'Loopback|vEthernet|Virtual|WSL|Bluetooth|Tailscale|ZeroTier' -and
                $_.IPAddress -notmatch '^127\.' -and
                $_.IPAddress -notmatch '^169\.254\.'
            }
        if ($ipCandidates) {
            $primaryIP = ($ipCandidates | Sort-Object -Property InterfaceIndex | Select-Object -First 1).IPAddress
            if ($primaryIP) { $localIP = $primaryIP }
        }
    } catch {
        $localIP = "127.0.0.1"
    }

    # Deteccion de GPU NVIDIA
    $gpuName = "CPU (Modo Fallback)"
    try {
        $smiCmd = Get-Command "nvidia-smi" -ErrorAction SilentlyContinue
        if ($smiCmd) {
            $smiOut = & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null
            if ($smiOut) {
                $gpuName = ($smiOut -split "`n")[0].Trim()
            }
        }
    } catch {}

    Write-Host "      [OK] GPU Activa: $gpuName" -ForegroundColor Green
    Write-Host "      [OK] IP Local LAN: $localIP" -ForegroundColor Green

    # -------------------------------------------------------------------------
    # 4. EXPOSICION PUBLICA (CLOUDFLARE TUNNEL - OPCIONAL)
    # -------------------------------------------------------------------------
    if ($Tunnel) {
        Write-Host "`n[4/5] Configurando Tunel Publico Cloudflare (cloudflared)..." -ForegroundColor Cyan
        $cloudflaredCmd = Get-Command "cloudflared" -ErrorAction SilentlyContinue
        if ($cloudflaredCmd) {
            Write-Host "      Iniciando Cloudflare Tunnel en segundo plano hacia http://localhost:$Port..." -ForegroundColor Yellow
            $tunnelProcess = Start-Process -FilePath "cloudflared" -ArgumentList "tunnel --url http://localhost:$Port" -PassThru -WindowStyle Minimized
            Write-Host "      [OK] Tunel iniciado exitosamente (PID: $($tunnelProcess.Id))." -ForegroundColor Green
        } else {
            Write-Host "      [AVISO] 'cloudflared' no esta instalado en el sistema." -ForegroundColor Yellow
            Write-Host "              Para instalarlo ejecuta: winget install --id Cloudflare.cloudflared" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "[4/5] Exposicion publica (Tunel Cloudflare): DESACTIVADA (Usa '.\run.ps1 -Tunnel' para activarlo)" -ForegroundColor DarkGray
    }

    # -------------------------------------------------------------------------
    # 5. BANNER INFORMATIVO Y EJECUCION DEL SERVIDOR ASGI
    # -------------------------------------------------------------------------
    Write-Host "`n==========================================================================" -ForegroundColor Cyan
    Write-Host " SERVIDOR UNIMON LISTO Y ESCUCHANDO EN TIEMPO REAL                         " -ForegroundColor Green
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host " Acceso Local:            " -NoNewline; Write-Host "http://localhost:$Port" -ForegroundColor Green
    Write-Host " Acceso en Red LAN:       " -NoNewline; Write-Host "http://$($localIP):$Port" -ForegroundColor Green
    Write-Host " Documentacion OpenAPI:   " -NoNewline; Write-Host "http://localhost:$Port/docs" -ForegroundColor Cyan
    Write-Host " Motor de Aceleracion:    " -NoNewline; Write-Host "$gpuName" -ForegroundColor Yellow
    if ($tunnelProcess -and -not $tunnelProcess.HasExited) {
        Write-Host " Tunel Cloudflare:        " -NoNewline; Write-Host "Activo (PID: $($tunnelProcess.Id))" -ForegroundColor Magenta
    }
    Write-Host "==========================================================================" -ForegroundColor Cyan
    Write-Host " Presiona [Ctrl + C] para detener el servidor limpiamente.`n" -ForegroundColor DarkGray

    # Iniciar Uvicorn
    & $venvUvicorn app.main:app --host $HostIP --port $Port --reload

} catch {
    Write-Host "`n[ERROR CRITICO] Ocurrio un fallo durante la ejecucion: $_" -ForegroundColor Red
} finally {
    # Limpieza ordenada al presionar Ctrl + C
    if ($tunnelProcess -and -not $tunnelProcess.HasExited) {
        Write-Host "`n[INFO] Cerrando proceso de Cloudflare Tunnel (PID: $($tunnelProcess.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $tunnelProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "`n[INFO] Servidor UniMon detenido satisfactoriamente.`n" -ForegroundColor Green
}
