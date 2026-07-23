# Requires -RunAsAdministrator

# Configurar la salida de consola para evitar problemas de encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Clear-Host
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  ASISTENTE DE CONFIGURACION AUTOMATICA: NGROK TUNNEL (VM)" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

# --- Variables de Configuracion ---
$NgrokDir = "C:\ngrok"
$NgrokExe = Join-Path $NgrokDir "ngrok.exe"
$DomainFile = Join-Path $NgrokDir "ngrok_domain.txt"
$RunnerScript = Join-Path $NgrokDir "run_ngrok.ps1"
$TaskName = "NgrokTunnelTask"
$LocalPort = 8000

# --- Paso 1: Descargar ngrok si no existe ---
Write-Host "`n[Paso 1/5] Verificando instalacion de ngrok..." -ForegroundColor Yellow

if (-not (Test-Path $NgrokDir)) {
    New-Item -ItemType Directory -Path $NgrokDir -Force | Out-Null
}

if (-not (Test-Path $NgrokExe)) {
    Write-Host "Descargando ngrok para Windows (amd64)..." -ForegroundColor Gray
    $NgrokZipUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    $NgrokZipPath = Join-Path $NgrokDir "ngrok.zip"
    
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $NgrokZipUrl -OutFile $NgrokZipPath -UseBasicParsing
        Expand-Archive -Path $NgrokZipPath -DestinationPath $NgrokDir -Force
        Remove-Item -Path $NgrokZipPath -ErrorAction SilentlyContinue
        
        if (Test-Path $NgrokExe) {
            Write-Host "[OK] ngrok descargado y descomprimido en: $NgrokExe" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] No se encontro ngrok.exe tras descomprimir." -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "[ERROR] Fallo la descarga de ngrok: $_" -ForegroundColor Red
        Write-Host "Descargalo manualmente desde https://ngrok.com/download y colocalo en $NgrokDir" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "[OK] ngrok encontrado en: $NgrokExe" -ForegroundColor Green
}

# --- Paso 2: Configurar Authtoken ---
Write-Host "`n[Paso 2/5] Configurando autenticacion de ngrok..." -ForegroundColor Yellow

# Verificar si ya hay un token configurado
$NgrokConfigCheck = & "$NgrokExe" config check 2>&1
$TokenConfigured = $false

# Intentar leer el config.yml de ngrok para ver si tiene authtoken
$NgrokConfigPath = Join-Path $env:USERPROFILE ".ngrok2\ngrok.yml"
$NgrokConfigPathV3 = Join-Path $env:LOCALAPPDATA "ngrok\ngrok.yml"

foreach ($cfgPath in @($NgrokConfigPathV3, $NgrokConfigPath)) {
    if (Test-Path $cfgPath) {
        $cfgContent = Get-Content $cfgPath -Raw -ErrorAction SilentlyContinue
        if ($cfgContent -match "authtoken:") {
            $TokenConfigured = $true
            Write-Host "[OK] Authtoken de ngrok ya esta configurado." -ForegroundColor Green
            break
        }
    }
}

if (-not $TokenConfigured) {
    Write-Host "====================================================================" -ForegroundColor Yellow
    Write-Host "  ACCION REQUERIDA: Ingresa tu authtoken de ngrok" -ForegroundColor Yellow
    Write-Host "====================================================================" -ForegroundColor Yellow
    Write-Host "1. Inicia sesion en https://dashboard.ngrok.com" -ForegroundColor White
    Write-Host "2. Ve a 'Your Authtoken' en el menu lateral" -ForegroundColor White
    Write-Host "3. Copia el token y pegalo aqui abajo" -ForegroundColor White
    Write-Host "====================================================================" -ForegroundColor Yellow
    Write-Host ""
    $AuthToken = Read-Host "  Pega tu authtoken de ngrok"
    
    if ([string]::IsNullOrWhiteSpace($AuthToken)) {
        Write-Host "[ERROR] No se ingreso ningun authtoken. Abortando." -ForegroundColor Red
        exit 1
    }
    
    & "$NgrokExe" config add-authtoken $AuthToken 2>&1 | Out-Null
    Write-Host "[OK] Authtoken configurado exitosamente." -ForegroundColor Green
}

# --- Paso 3: Configurar dominio estatico ---
Write-Host "`n[Paso 3/5] Configurando dominio estatico de ngrok..." -ForegroundColor Yellow

if (Test-Path $DomainFile) {
    $NgrokDomain = (Get-Content -Path $DomainFile -Raw).Trim()
    Write-Host "[OK] Dominio estatico cargado: $NgrokDomain" -ForegroundColor Green
} else {
    Write-Host "====================================================================" -ForegroundColor Yellow
    Write-Host "  ACCION REQUERIDA: Ingresa tu dominio estatico de ngrok" -ForegroundColor Yellow
    Write-Host "====================================================================" -ForegroundColor Yellow
    Write-Host "1. Ve a https://dashboard.ngrok.com/domains" -ForegroundColor White
    Write-Host "2. Copia tu dominio gratuito (ej: algo-random.ngrok-free.app)" -ForegroundColor White
    Write-Host "3. Pegalo aqui abajo (sin https://)" -ForegroundColor White
    Write-Host "====================================================================" -ForegroundColor Yellow
    Write-Host ""
    $NgrokDomain = Read-Host "  Pega tu dominio estatico de ngrok"
    
    if ([string]::IsNullOrWhiteSpace($NgrokDomain)) {
        Write-Host "[ERROR] No se ingreso ningun dominio. Abortando." -ForegroundColor Red
        exit 1
    }
    
    # Limpiar https:// si lo pegaron
    $NgrokDomain = $NgrokDomain -replace "^https?://", ""
    $NgrokDomain = $NgrokDomain.Trim("/")
    
    Set-Content -Path $DomainFile -Value $NgrokDomain -Encoding UTF8
    Write-Host "[OK] Dominio estatico guardado: $NgrokDomain" -ForegroundColor Green
}

# --- Paso 4: Limpieza y creacion del servicio ---
Write-Host "`n[Paso 4/5] Limpiando servicios anteriores y creando runner..." -ForegroundColor Yellow

# Matar procesos anteriores de ngrok, ssh tunnels, cloudflared
Stop-Process -Name "ngrok" -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object { $_.ProcessName -eq "ssh" } | Stop-Process -Force -ErrorAction SilentlyContinue
Stop-Process -Name "cloudflared" -Force -ErrorAction SilentlyContinue

# Eliminar tareas programadas anteriores (Serveo y ngrok)
schtasks /delete /tn "ServeoTunnelTask" /f 2>$null | Out-Null
schtasks /delete /tn "$TaskName" /f 2>$null | Out-Null

# Detener servicio Cloudflared si existia
$CloudflaredService = Get-Service -Name "Cloudflared" -ErrorAction SilentlyContinue
if ($CloudflaredService) {
    Stop-Service "Cloudflared" -ErrorAction SilentlyContinue
    & C:\cloudflared\cloudflared.exe service uninstall 2>$null | Out-Null
}

Write-Host "[OK] Entorno limpio." -ForegroundColor Green

# Crear el script runner persistente
$RunnerContent = @"
# Runner persistente de ngrok con auto-reconexion
`$NgrokExe = "$NgrokExe"
`$NgrokDomain = "$NgrokDomain"
`$LocalPort = $LocalPort
`$LogFile = "$NgrokDir\ngrok_tunnel.log"

while (`$true) {
    try {
        "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] Iniciando tunel ngrok para `$NgrokDomain..." | Out-File -FilePath `$LogFile -Append -Encoding UTF8
        & `$NgrokExe http --domain=`$NgrokDomain `$LocalPort --log=`$LogFile --log-format=logfmt 2>&1
    } catch {
        "[ERROR] `$_" | Out-File -FilePath `$LogFile -Append -Encoding UTF8
    }
    "[$(Get-Date)] Tunel cerrado. Reintentando en 10 segundos..." | Out-File -FilePath `$LogFile -Append -Encoding UTF8
    Start-Sleep -Seconds 10
}
"@

Set-Content -Path $RunnerScript -Value $RunnerContent -Encoding UTF8
Write-Host "[OK] Script runner guardado en: $RunnerScript" -ForegroundColor Green

# --- Paso 5: Crear tarea programada e iniciar ---
Write-Host "`n[Paso 5/5] Creando Tarea Programada de Windows e iniciando tunel..." -ForegroundColor Yellow

$ActionCmd = "powershell.exe"
$ActionArgs = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunnerScript`""

schtasks /create /tn "$TaskName" /tr "$ActionCmd $ActionArgs" /sc onstart /ru "SYSTEM" /f | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Tarea programada '$TaskName' creada para arranque automatico." -ForegroundColor Green
} else {
    Write-Host "[AVISO] Intentando crear tarea bajo la cuenta actual..." -ForegroundColor Yellow
    schtasks /create /tn "$TaskName" /tr "$ActionCmd $ActionArgs" /sc onstart /f | Out-Null
}

# Arrancar inmediatamente
schtasks /run /tn "$TaskName" | Out-Null
Start-Sleep -Seconds 5

# Verificar que el proceso esta corriendo
$NgrokProcess = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
if ($NgrokProcess) {
    Write-Host "[OK] ngrok esta corriendo (PID: $($NgrokProcess.Id))." -ForegroundColor Green
} else {
    Write-Host "[AVISO] ngrok no aparece en la lista de procesos. Revisa el log en $NgrokDir\ngrok_tunnel.log" -ForegroundColor Yellow
}

# --- Resumen final ---
Write-Host "`n====================================================================" -ForegroundColor Green
Write-Host "  [PROCESO COMPLETADO CON EXITO]" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "  El tunel ngrok ya corre de fondo en la VM Server."
Write-Host ""
Write-Host "  URL publica fija del backend:" -ForegroundColor White
Write-Host "  https://$NgrokDomain" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Rutas utiles de prueba:"
Write-Host "  - Estado API:   https://$NgrokDomain/api/status"
Write-Host "  - Docs Swagger: https://$NgrokDomain/docs"
Write-Host "  - Dashboard:    http://127.0.0.1:4040"
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "  [ATENCION] Configurar en Netlify:" -ForegroundColor Yellow
Write-Host "  VITE_API_URL=https://$NgrokDomain" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Nota: Log de depuracion en: $NgrokDir\ngrok_tunnel.log" -ForegroundColor Gray
Write-Host "  Nota: Para iniciar manualmente: $NgrokExe http --domain=$NgrokDomain $LocalPort" -ForegroundColor Gray
Write-Host "====================================================================" -ForegroundColor Green
