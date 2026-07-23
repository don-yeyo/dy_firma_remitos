# Requires -RunAsAdministrator

# Configurar la salida de consola para UTF8 nativo por si la terminal lo soporta
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Clear-Host
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  ASISTENTE DE CONFIGURACION AUTOMATICA: SERVEO TUNNEL (VM)" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

# 1. Comprobar que SSH este instalado y disponible
$SshPath = (Get-Command ssh.exe -ErrorAction SilentlyContinue).Source
if (-not $SshPath) {
    Write-Host "[ERROR] No se encontro 'ssh.exe' en el sistema." -ForegroundColor Red
    Write-Host "Asegurate de tener instalado el cliente OpenSSH de Windows." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Cliente OpenSSH encontrado en: $SshPath" -ForegroundColor Green

# 2. Definir o recuperar Subdominio Fijo Persistente y Carpeta Base
Write-Host "`n[Paso 1/5] Configurando subdominio estatico persistente para Serveo..." -ForegroundColor Yellow
$TunnelDir = "C:\cloudflared"
if (-not (Test-Path $TunnelDir)) {
    New-Item -ItemType Directory -Path $TunnelDir -Force | Out-Null
}
$SubdomainFile = Join-Path $TunnelDir "serveo_subdomain.txt"

if (Test-Path $SubdomainFile) {
    $Subdomain = (Get-Content -Path $SubdomainFile -Raw).Trim()
    Write-Host "[OK] Cargando subdominio persistente anterior: $Subdomain.serveousercontent.com" -ForegroundColor Green
} else {
    # Generar un subdominio legible y aleatorio
    $RandomSuffix = Get-Random -Minimum 1000 -Maximum 9999
    $Subdomain = "dy-remitos-$RandomSuffix"
    Set-Content -Path $SubdomainFile -Value $Subdomain -Encoding UTF8
    Write-Host "[OK] Generado nuevo subdominio persistente amigable: $Subdomain.serveousercontent.com" -ForegroundColor Green
}

# 2b. Crear y configurar Llave SSH persistente (Requerida por Serveo para subdominios fijos)
$SshKeyPath = Join-Path $TunnelDir "id_rsa"
if (-not (Test-Path $SshKeyPath)) {
    Write-Host "Generando clave SSH en el servidor local para reservar el subdominio en Serveo..." -ForegroundColor Yellow
    # ssh-keygen requiere comillas vacias para la frase de contrasena
    & ssh-keygen -t rsa -b 2048 -N '""' -f "$SshKeyPath" | Out-Null
    if (Test-Path $SshKeyPath) {
        Write-Host "[OK] Clave SSH de reserva generada en: $SshKeyPath" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] No se pudo generar la clave SSH de forma automatica. Serveo podria rechazar el subdominio fijo." -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] Clave SSH de reserva encontrada en: $SshKeyPath" -ForegroundColor Green
}

# Configurar permisos NTFS estrictos (ACL) para id_rsa (Requerido obligatoriamente por OpenSSH en Windows)
Write-Host "Configurando permisos de seguridad (ACL) estrictos para la clave privada..." -ForegroundColor Yellow
try {
    $Acl = Get-Acl $SshKeyPath
    $Acl.SetAccessRuleProtection($true, $false) # Desactivar herencia y remover accesos heredados
    
    $ArAdministradores = New-Object System.Security.AccessControl.FileSystemAccessRule("Administradores", "FullControl", "Allow")
    $ArSystem = New-Object System.Security.AccessControl.FileSystemAccessRule("SYSTEM", "FullControl", "Allow")
    
    $Acl.AddAccessRule($ArAdministradores)
    $Acl.AddAccessRule($ArSystem)
    
    Set-Acl $SshKeyPath $Acl
    Write-Host "[OK] Permisos ACL restringidos exclusivamente a Administradores y SYSTEM." -ForegroundColor Green
} catch {
    Write-Host "[WARNING] No se pudieron aplicar las restricciones ACL a la clave SSH: $_" -ForegroundColor Yellow
}

# 3. Limpieza de procesos y servicios anteriores (Cloudflared y SSH previos)
Write-Host "`n[Paso 2/5] Deteniendo y limpiando servicios/procesos anteriores..." -ForegroundColor Yellow

# Detener servicio Cloudflared si existia
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
Write-Host "[OK] Entorno limpio y listo para el nuevo tunel." -ForegroundColor Green

# 3b. Registro Interactivo de la Clave SSH en Serveo
Write-Host "`n====================================================================" -ForegroundColor Yellow
Write-Host "  [ATENCION: REGISTRO DE CLAVE SSH EN SERVEO.NET]" -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Yellow
Write-Host "Para reservar el subdominio fijo '$Subdomain', Serveo requiere asociar tu clave SSH."

# Obtener fingerprint y construir el link de registro de forma nativa
$KeyRegistryUrl = "https://console.serveo.net/ssh/keys"
if (Test-Path "$SshKeyPath.pub") {
    $KeyInfo = & ssh-keygen -l -f "$SshKeyPath.pub" 2>$null
    if ($KeyInfo -match "SHA256:([a-zA-Z0-9\+/=]+)") {
        $Hash = $Matches[1]
        $FullFingerprint = "SHA256:$Hash"
        $EncodedFingerprint = [uri]::EscapeDataString($FullFingerprint)
        $KeyRegistryUrl = "https://console.serveo.net/ssh/keys?add=$EncodedFingerprint"
    }
}

Write-Host "Por favor, sigue estos pasos:"
Write-Host "1. Abre el siguiente enlace en tu navegador para registrar tu clave publica:"
Write-Host "   $KeyRegistryUrl" -ForegroundColor Cyan
Write-Host "2. Inicia sesion con tu cuenta de Google o GitHub."
Write-Host "3. Haz clic en 'Register' o 'Authorize' para asociar tu clave."
Write-Host "4. Una vez completado en el navegador, regresa aqui y presiona [ENTER]."
Write-Host "====================================================================" -ForegroundColor Yellow
Write-Host "Iniciando conexion de registro de fondo..." -ForegroundColor Gray
Start-Sleep -Seconds 2

# Lanzar SSH en segundo plano redirigiendo su salida para no desalinear la terminal
$TempLogPath = Join-Path $TunnelDir "serveo_temp.log"
Remove-Item -Path $TempLogPath -ErrorAction SilentlyContinue | Out-Null

# NOTA: Redirigimos el puerto local 8000 a traves de la IP de loopback IPv4 '127.0.0.1' en lugar de 'localhost'.
# Esto evita errores '502 Bad Gateway' si Windows Server resuelve 'localhost' a la IP IPv6 '[::1]'.
$SshArgs = @("-i", "`"$SshKeyPath`"", "-o", "StrictHostKeyChecking=no", "-o UserKnownHostsFile=\\.\NUL", "-R", "`"${Subdomain}:80:127.0.0.1:8000`"", "serveo.net")
$SshProcess = Start-Process -FilePath "$SshPath" -ArgumentList $SshArgs -NoNewWindow -PassThru -RedirectStandardOutput "$TempLogPath" -RedirectStandardError "$TempLogPath" -ErrorAction SilentlyContinue

Write-Host ""
Read-Host "  Presiona [ENTER] una vez que hayas registrado la clave en tu navegador"

# Matar el proceso SSH temporal de registro
if ($SshProcess -and -not $SshProcess.HasExited) {
    Write-Host "  Deteniendo conexion temporal de registro..." -ForegroundColor Gray
    Stop-Process -Id $SshProcess.Id -Force -ErrorAction SilentlyContinue
}
Remove-Item -Path $TempLogPath -ErrorAction SilentlyContinue | Out-Null

Write-Host "`n[OK] Conexion temporal finalizada. Continuando con la instalacion del servicio de fondo..." -ForegroundColor Green
Start-Sleep -Seconds 2

# 4. Crear carpeta de persistencia y el Runner Script con Keep-Alive robusto y Llave Explicita
Write-Host "`n[Paso 3/5] Creando scripts de auto-conexion del tunel..." -ForegroundColor Yellow

$RunnerScriptPath = Join-Path $TunnelDir "run_serveo_runner.ps1"
$RunnerContent = @"
# Script de ejecucion persistente con auto-conexion para Serveo
Write-Host "[SERVIEO] Iniciando tunel para $Subdomain.serveousercontent.com..." -ForegroundColor Cyan

while (`$true) {
    try {
        # -i "$SshKeyPath" obliga a usar la clave SSH persistente para reservar el subdominio
        # -o ExitOnForwardFailure=yes hace que ssh aborte si falla el reenviado de puerto
        # -o UserKnownHostsFile=\\.\NUL evita que intente escribir known_hosts en el home de SYSTEM
        # Redirigimos el reenvio a '127.0.0.1:8000' en lugar de 'localhost' para evitar fallas de IPv6 (502 Bad Gateway)
        & "$SshPath" -i "$SshKeyPath" -N -o StrictHostKeyChecking=no -o UserKnownHostsFile=\\.\NUL -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R "${Subdomain}:80:127.0.0.1:8000" serveo.net >> "$TunnelDir\serveo_tunnel.log" 2>&1
    } catch {
        "[SERVIEO ERROR] `$($_)" | Out-File -FilePath "$TunnelDir\serveo_tunnel.log" -Append -Encoding UTF8
    }
    Write-Host "[SERVIEO] Conexion cerrada o interrumpida. Reintentando en 5 segundos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}
"@

Set-Content -Path $RunnerScriptPath -Value $RunnerContent -Encoding UTF8
Write-Host "[OK] Script de auto-conexion guardado en: $RunnerScriptPath" -ForegroundColor Green

# 5. Crear la Tarea Programada en Windows para arranque automatico
Write-Host "`n[Paso 4/5] Creando Tarea Programada de Windows (Arranque de fondo)..." -ForegroundColor Yellow

$ActionCmd = "powershell.exe"
$ActionArgs = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunnerScriptPath`""

# Crear tarea programada que se ejecute bajo la cuenta SYSTEM al iniciar el sistema
schtasks /create /tn "$TaskName" /tr "$ActionCmd $ActionArgs" /sc onstart /ru "SYSTEM" /f | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Tarea programada '$TaskName' creada exitosamente para arranque automatico." -ForegroundColor Green
} else {
    Write-Host "[AVISO] Creando tarea programada bajo la cuenta actual..." -ForegroundColor Yellow
    schtasks /create /tn "$TaskName" /tr "$ActionCmd $ActionArgs" /sc onstart /f | Out-Null
}

# 6. Iniciar la tarea inmediatamente
Write-Host "`n[Paso 5/5] Arrancando el tunel de fondo..." -ForegroundColor Yellow
schtasks /run /tn "$TaskName" | Out-Null
Start-Sleep -Seconds 3

Write-Host "`n====================================================================" -ForegroundColor Green
Write-Host "  [PROCESO COMPLETADO CON EXITO]" -ForegroundColor Green
Write-Host "  El tunel Serveo ya corre de fondo en la VM Server."
Write-Host "  URL publica fija del backend: https://$Subdomain.serveousercontent.com"
Write-Host "  URL alternativa HTTP:         http://$Subdomain.serveousercontent.com"
Write-Host "`n  Rutas utiles de prueba:"
Write-Host "  - Estado API: https://$Subdomain.serveousercontent.com/api/status"
Write-Host "  - Docs Swagger: https://$Subdomain.serveousercontent.com/docs"
Write-Host "====================================================================" -ForegroundColor Green

Write-Host "`n[ATENCION] Recorda configurar este subdominio fijo en Netlify:"
Write-Host "VITE_API_URL=https://$Subdomain.serveousercontent.com" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "`n  Nota: Para pruebas manuales de depuracion en consola (VERBOSO), usa:"
Write-Host "  ssh -v -i $SshKeyPath -R ${Subdomain}:80:127.0.0.1:8000 serveo.net" -ForegroundColor Gray
Write-Host "`n  Puedes inspeccionar los logs de fondo en: $TunnelDir\serveo_tunnel.log" -ForegroundColor Gray
Write-Host "====================================================================" -ForegroundColor Green
