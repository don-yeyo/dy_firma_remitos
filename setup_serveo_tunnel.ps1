# Requires -RunAsAdministrator

Clear-Host
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  ASISTENTE DE CONFIGURACION AUTOMATICA: SERVEO TUNNEL (VM)" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

# 1. Comprobar que SSH esté instalado y disponible
$SshPath = (Get-Command ssh.exe -ErrorAction SilentlyContinue).Source
if (-not $SshPath) {
    Write-Host "[ERROR] No se encontró 'ssh.exe' en el sistema." -ForegroundColor Red
    Write-Host "Asegúrate de tener instalado el cliente OpenSSH de Windows." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Cliente OpenSSH encontrado en: $SshPath" -ForegroundColor Green

# 2. Definir o recuperar Subdominio Fijo Persistente y Carpeta Base
Write-Host "`n[Paso 1/5] Configurando subdominio estático persistente para Serveo..." -ForegroundColor Yellow
$TunnelDir = "C:\cloudflared"
if (-not (Test-Path $TunnelDir)) {
    New-Item -ItemType Directory -Path $TunnelDir -Force | Out-Null
}
$SubdomainFile = Join-Path $TunnelDir "serveo_subdomain.txt"

if (Test-Path $SubdomainFile) {
    $Subdomain = (Get-Content -Path $SubdomainFile -Raw).Trim()
    Write-Host "[OK] Cargando subdominio persistente anterior: $Subdomain.serveo.net" -ForegroundColor Green
} else {
    # Generar un subdominio legible y aleatorio
    $RandomSuffix = Get-Random -Minimum 1000 -Maximum 9999
    $Subdomain = "dy-remitos-$RandomSuffix"
    Set-Content -Path $SubdomainFile -Value $Subdomain -Encoding UTF8
    Write-Host "[OK] Generado nuevo subdominio persistente amigable: $Subdomain.serveo.net" -ForegroundColor Green
}

# 2b. Crear y configurar Llave SSH persistente (Requerida por Serveo para subdominios fijos)
$SshKeyPath = Join-Path $TunnelDir "id_rsa"
if (-not (Test-Path $SshKeyPath)) {
    Write-Host "Generando clave SSH en el servidor local para reservar el subdominio en Serveo..." -ForegroundColor Yellow
    # ssh-keygen requiere comillas vacías para la frase de contraseña
    & ssh-keygen -t rsa -b 2048 -N '""' -f "$SshKeyPath" | Out-Null
    if (Test-Path $SshKeyPath) {
        Write-Host "[OK] Clave SSH de reserva generada en: $SshKeyPath" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] No se pudo generar la clave SSH de forma automática. Serveo podría rechazar el subdominio fijo." -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] Clave SSH de reserva encontrada en: $SshKeyPath" -ForegroundColor Green
}

# 3. Limpieza de procesos y servicios anteriores (Cloudflared y SSH previos)
Write-Host "`n[Paso 2/5] Deteniendo y limpiando servicios/procesos anteriores..." -ForegroundColor Yellow

# Detener servicio Cloudflared si existía
$CloudflaredService = Get-Service -Name "Cloudflared" -ErrorAction SilentlyContinue
if ($CloudflaredService) {
    Write-Host "Desactivando servicio previo Cloudflared..." -ForegroundColor Gray
    Stop-Service "Cloudflared" -ErrorAction SilentlyContinue
    & C:\cloudflared\cloudflared.exe service uninstall 2>$null | Out-Null
}

# Matar procesos de ssh previos o cloudflared
Stop-Process -Name "cloudflared" -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object { $_.ProcessName -eq "ssh" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Eliminar tarea programada anterior si existe
$TaskName = "ServeoTunnelTask"
schtasks /delete /tn "$TaskName" /f 2>$null | Out-Null
Write-Host "[OK] Entorno limpio y listo para el nuevo túnel." -ForegroundColor Green

# 4. Crear carpeta de persistencia y el Runner Script con Keep-Alive robusto y Llave Explícita
Write-Host "`n[Paso 3/5] Creando scripts de auto-reconexión del túnel..." -ForegroundColor Yellow

$RunnerScriptPath = Join-Path $TunnelDir "run_serveo_runner.ps1"
$RunnerContent = @"
# Script de ejecución persistente con auto-reconexión para Serveo
Write-Host "[SERVIEO] Iniciando túnel para $Subdomain.serveo.net..." -ForegroundColor Cyan

while (`$true) {
    try {
        # -i "$SshKeyPath" obliga a usar la clave SSH persistente para reservar el subdominio
        # -o ExitOnForwardFailure=yes hace que ssh aborte si falla el reenvío de puerto
        # -o UserKnownHostsFile=\\.\NUL evita que intente escribir known_hosts en el home de SYSTEM
        & "$SshPath" -i "$SshKeyPath" -N -o StrictHostKeyChecking=no -o UserKnownHostsFile=\\.\NUL -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R "$Subdomain:80:localhost:8000" serveo.net
    } catch {
        Write-Host "[SERVIEO ERROR] `$($_)" -ForegroundColor Red
    }
    Write-Host "[SERVIEO] Conexión cerrada o interrumpida. Reintentando en 5 segundos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}
"@

Set-Content -Path $RunnerScriptPath -Value $RunnerContent -Encoding UTF8
Write-Host "[OK] Script de auto-reconexión guardado en: $RunnerScriptPath" -ForegroundColor Green

# 5. Crear la Tarea Programada en Windows para arranque automático
Write-Host "`n[Paso 4/5] Creando Tarea Programada de Windows (Arranque de fondo)..." -ForegroundColor Yellow

$ActionCmd = "powershell.exe"
$ActionArgs = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunnerScriptPath`""

# Crear tarea programada que se ejecute bajo la cuenta SYSTEM al iniciar el sistema
schtasks /create /tn "$TaskName" /tr "$ActionCmd $ActionArgs" /sc onstart /ru "SYSTEM" /f | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Tarea programada '$TaskName' creada exitosamente para arranque automático." -ForegroundColor Green
} else {
    Write-Host "[AVISO] Creando tarea programada bajo la cuenta actual..." -ForegroundColor Yellow
    schtasks /create /tn "$TaskName" /tr "$ActionCmd $ActionArgs" /sc onstart /f | Out-Null
}

# 6. Iniciar la tarea inmediatamente
Write-Host "`n[Paso 5/5] Arrancando el túnel de fondo..." -ForegroundColor Yellow
schtasks /run /tn "$TaskName" | Out-Null
Start-Sleep -Seconds 3

Write-Host "`n====================================================================" -ForegroundColor Green
Write-Host "  [PROCESO COMPLETADO CON EXITO]" -ForegroundColor Green
Write-Host "  El túnel Serveo ya corre de fondo en la VM Server."
Write-Host "  URL pública fija del backend: https://$Subdomain.serveo.net"
Write-Host "  URL alternativa HTTP:         http://$Subdomain.serveo.net"
Write-Host "`n  Rutas útiles de prueba:"
Write-Host "  - Estado API: https://$Subdomain.serveo.net/api/status"
Write-Host "  - Docs Swagger: https://$Subdomain.serveo.net/docs"
Write-Host "====================================================================" -ForegroundColor Green

Write-Host "`n[ATENCION] Recordá configurar este subdominio fijo en Netlify:"
Write-Host "VITE_API_URL=https://$Subdomain.serveo.net" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "`n  Nota: Para pruebas manuales de depuración en consola, usa:"
Write-Host "  ssh -i $SshKeyPath -R $Subdomain:80:localhost:8000 serveo.net" -ForegroundColor Gray
Write-Host "====================================================================" -ForegroundColor Green
