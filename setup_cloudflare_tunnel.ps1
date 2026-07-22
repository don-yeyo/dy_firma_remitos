# Requires -RunAsAdministrator

Clear-Host
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  ASISTENTE DE CONFIGURACION AUTOMATICA: CLOUDFLARE TUNNEL (VM)" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

# 1. Buscar cloudflared.exe en el directorio actual o en la carpeta superior
$CloudflaredPath = ""
$PathsToSearch = @(
    "$PSScriptRoot\cloudflared.exe",
    "$PSScriptRoot\..\cloudflared.exe",
    "C:\Users\Administrador\Documents\cloudflared.exe"
)

foreach ($Path in $PathsToSearch) {
    if (Test-Path $Path) {
        $CloudflaredPath = $Path
        break
    }
}

if (-not $CloudflaredPath) {
    Write-Host "[ERROR] No se encontro 'cloudflared.exe' en el disco de la VM." -ForegroundColor Red
    Write-Host "Por favor, descargalo de GitHub Releases y ubicalo en la carpeta del proyecto o en C:\Users\Administrador\Documents\"
    exit 1
}

Write-Host "[OK] Encontrado cloudflared.exe en: $CloudflaredPath" -ForegroundColor Green

# 2. Iniciar sesion
Write-Host "`n[Paso 1/5] Iniciando sesion en Cloudflare..." -ForegroundColor Yellow
Write-Host "Se abrira el navegador. Inicia sesion en la cuenta y selecciona el dominio corporativo a autorizar."
& $CloudflaredPath tunnel login

# Confirmar existencia de cert.pem
$CertPath = "C:\Users\Administrador\.cloudflared\cert.pem"
if (-not (Test-Path $CertPath)) {
    Write-Host "[ERROR] No se detecto el archivo de autorizacion en $CertPath." -ForegroundColor Red
    Write-Host "Asegurate de haber completado la autorizacion en la ventana web."
    exit 1
}
Write-Host "[OK] Autorizacion exitosa. Certificado guardado en $CertPath." -ForegroundColor Green

# 3. Solicitar Hostname
Write-Host "`n[Paso 2/5] Ingresa el subdominio que deseas mapear (ej. remitos-api.donyeyo.com.ar):" -ForegroundColor Yellow
$Hostname = Read-Host "Subdominio de destino"
if (-not $Hostname) {
    Write-Host "[ERROR] El subdominio no puede estar vacio." -ForegroundColor Red
    exit 1
}

# 4. Crear el tunel
Write-Host "`n[Paso 3/5] Creando tunel nombrado 'dy-remitos-tunnel'..." -ForegroundColor Yellow
$TunnelName = "dy-remitos-tunnel"
$Output = & $CloudflaredPath tunnel create $TunnelName

# Parsear el UUID del tunel
$Uuid = ""
foreach ($line in $Output) {
    if ($line -match "Created tunnel dy-remitos-tunnel with id ([a-f0-9\-]+)") {
        $Uuid = $Matches[1]
        break
    }
}

if (-not $Uuid) {
    # Alternativa: Buscar el archivo JSON mas reciente en la carpeta .cloudflared
    $RecentJson = Get-ChildItem "C:\Users\Administrador\.cloudflared\*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($RecentJson) {
        $Uuid = $RecentJson.BaseName
    }
}

if (-not $Uuid) {
    Write-Host "[ERROR] No se pudo recuperar el ID unico (UUID) del tunel creado." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Tunel creado con UUID: $Uuid" -ForegroundColor Green

# 5. Generar archivo config.yml
Write-Host "`n[Paso 4/5] Generando config.yml de forma automatica..." -ForegroundColor Yellow
$ConfigContent = @"
tunnel: $Uuid
credentials-file: C:\Users\Administrador\.cloudflared\$Uuid.json

ingress:
  - hostname: $Hostname
    service: http://localhost:8000
  - service: http_status:404
"@

$ConfigFileDir = "C:\Users\Administrador\.cloudflared"
if (-not (Test-Path $ConfigFileDir)) {
    New-Item -ItemType Directory -Path $ConfigFileDir -Force | Out-Null
}
$ConfigFilePath = Join-Path $ConfigFileDir "config.yml"
Set-Content -Path $ConfigFilePath -Value $ConfigContent -Encoding UTF8
Write-Host "[OK] config.yml escrito con exito en: $ConfigFilePath" -ForegroundColor Green

# 6. Registrar DNS
Write-Host "`n[Paso 5/5] Asociando DNS route en Cloudflare para $Hostname..." -ForegroundColor Yellow
& $CloudflaredPath tunnel route dns $TunnelName $Hostname

# 7. Instalar y arrancar el servicio de Windows
Write-Host "`nInstalando Cloudflare Tunnel como Servicio de Windows (Arranque de fondo)..." -ForegroundColor Yellow
$Service = Get-Service -Name "Cloudflared" -ErrorAction SilentlyContinue
if ($Service) {
    Write-Host "Removiendo servicio existente..."
    & $CloudflaredPath service uninstall | Out-Null
}

# Instalar el servicio indicándole la configuración explícita
& $CloudflaredPath --config $ConfigFilePath service install

# Copia de seguridad al perfil del sistema (SYSTEM) para evitar problemas de permisos de LocalSystem
$SystemProfileDir = "C:\Windows\System32\config\systemprofile\.cloudflared"
if (Test-Path "C:\Windows\System32\config\systemprofile") {
    if (-not (Test-Path $SystemProfileDir)) {
        New-Item -ItemType Directory -Path $SystemProfileDir -Force | Out-Null
    }
    Copy-Item -Path $ConfigFilePath -Destination (Join-Path $SystemProfileDir "config.yml") -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "C:\Users\Administrador\.cloudflared\$Uuid.json" -Destination (Join-Path $SystemProfileDir "$Uuid.json") -Force -ErrorAction SilentlyContinue
}

# Arrancar servicio
Start-Service "Cloudflared" -ErrorAction SilentlyContinue

Write-Host "`n====================================================================" -ForegroundColor Green
Write-Host "  [PROCESO COMPLETADO CON EXITO]" -ForegroundColor Green
Write-Host "  El tunel ya corre de fondo en la VM Server."
Write-Host "  URL del backend asociada de forma fija: https://$Hostname"
Write-Host "`n  Nota: Para pruebas manuales en consola sin servicio, ejecuta:"
Write-Host "  $CloudflaredPath --config $ConfigFilePath tunnel run $TunnelName"
Write-Host "====================================================================" -ForegroundColor Green
pause
