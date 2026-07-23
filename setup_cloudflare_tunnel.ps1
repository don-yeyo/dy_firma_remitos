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

# 1b. Copiar a C:\cloudflared\ para evitar restricciones de permisos de Servicio de Windows (LocalSystem)
$SystemBinaryDir = "C:\cloudflared"
if (-not (Test-Path $SystemBinaryDir)) {
    New-Item -ItemType Directory -Path $SystemBinaryDir -Force | Out-Null
}
$SystemCloudflaredPath = Join-Path $SystemBinaryDir "cloudflared.exe"
Copy-Item -Path $CloudflaredPath -Destination $SystemCloudflaredPath -Force -ErrorAction SilentlyContinue
$CloudflaredPath = $SystemCloudflaredPath
Write-Host "[OK] Copiado ejecutable del servicio a: $CloudflaredPath" -ForegroundColor Green

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

# 5. Generar archivo config.yml y preparar carpeta para el Servicio de Windows (SYSTEM)
Write-Host "`n[Paso 4/5] Generando config.yml de forma automatica..." -ForegroundColor Yellow

$SystemProfileDir = "C:\Windows\System32\config\systemprofile\.cloudflared"
if (-not (Test-Path $SystemProfileDir)) {
    New-Item -ItemType Directory -Path $SystemProfileDir -Force | Out-Null
}

# Copiar JSON de credenciales a la carpeta del sistema
Copy-Item -Path "C:\Users\Administrador\.cloudflared\$Uuid.json" -Destination (Join-Path $SystemProfileDir "$Uuid.json") -Force -ErrorAction SilentlyContinue

$ConfigContent = @"
tunnel: $Uuid
credentials-file: C:/Windows/System32/config/systemprofile/.cloudflared/$Uuid.json
logfile: C:/Windows/System32/config/systemprofile/.cloudflared/cloudflared.log

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

# Copiar config.yml al perfil del sistema
Copy-Item -Path $ConfigFilePath -Destination (Join-Path $SystemProfileDir "config.yml") -Force -ErrorAction SilentlyContinue

Write-Host "[OK] config.yml escrito con exito en: $ConfigFilePath y en $SystemProfileDir" -ForegroundColor Green

# 6. Registrar DNS
Write-Host "`n[Paso 5/5] Asociando DNS route en Cloudflare para $Hostname..." -ForegroundColor Yellow
& $CloudflaredPath tunnel route dns $TunnelName $Hostname

# 7. Instalar y arrancar el servicio de Windows
Write-Host "`nInstalando Cloudflare Tunnel como Servicio de Windows (Arranque de fondo)..." -ForegroundColor Yellow
$Service = Get-Service -Name "Cloudflared" -ErrorAction SilentlyContinue
if ($Service) {
    Write-Host "Removiendo servicio existente..."
    Stop-Service "Cloudflared" -ErrorAction SilentlyContinue
    Stop-Process -Name "cloudflared" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    & $CloudflaredPath service uninstall 2>$null | Out-Null
    Start-Sleep -Seconds 2
}

# Instalar el servicio
& $CloudflaredPath service install

# Garantizar el comando exacto en el Registro de Servicios de Windows (ImagePath)
$RegPath = "HKLM:\SYSTEM\CurrentControlSet\Services\Cloudflared"
$ExactImagePath = "`"$CloudflaredPath`" --config `"$SystemProfileDir\config.yml`" tunnel run"
Set-ItemProperty -Path $RegPath -Name "ImagePath" -Value $ExactImagePath -Force -ErrorAction SilentlyContinue

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
