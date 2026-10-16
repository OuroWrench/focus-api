# =====================================================================
#  Focus! - Paso 1: crear los recursos en Azure
#    - Grupo de recursos
#    - Azure SQL Database (oferta gratuita serverless)
#    - Cuenta de almacenamiento + contenedor "fotos" (Blob Storage)
#    - App Service (Linux, Python 3.12) para la API
#    - Function App (Linux, Python) para la API serverless
#
#  Uso (PowerShell, desde la carpeta del repo):
#    az login
#    .\deploy\01_crear_recursos.ps1
# =====================================================================
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\config.ps1"

function Paso($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }
function Revisar($accion) { if ($LASTEXITCODE -ne 0) { throw "Fallo: $accion (revisa el mensaje de az arriba)" } }

$seguro = Read-Host "Contrasena para el administrador de Azure SQL ($SqlUsuario)" -AsSecureString
$SqlPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro))
if ($SqlPassword.Length -lt 8) { throw "La contrasena debe tener al menos 8 caracteres, con mayusculas, minusculas y numeros." }
if ($SqlPassword -match '[&|^%<>"'' ]') { throw "Evita los caracteres & | ^ % < > comillas y espacios: el CLI de Azure en Windows los interpreta mal. Usa letras, numeros y ! @ # _ -" }

Paso "Grupo de recursos $Grupo ($Ubicacion)"
az group create -n $Grupo -l $Ubicacion -o none; Revisar "crear grupo"

Paso "Servidor Azure SQL $SqlServidor ($UbicacionSql)"
az sql server create -g $Grupo -n $SqlServidor -l $UbicacionSql -u $SqlUsuario -p $SqlPassword -o none; Revisar "crear servidor SQL"

Paso "Firewall: permitir servicios de Azure y tu IP actual"
az sql server firewall-rule create -g $Grupo -s $SqlServidor -n PermitirAzure --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 -o none; Revisar "regla de firewall Azure"
try {
    $miIp = (Invoke-RestMethod -Uri "https://api.ipify.org")
    az sql server firewall-rule create -g $Grupo -s $SqlServidor -n MiIP --start-ip-address $miIp --end-ip-address $miIp -o none
} catch { Write-Warning "No se pudo detectar tu IP; agregala desde el portal si quieres conectarte desde tu compu." }

Paso "Base de datos $SqlBase (serverless, oferta gratuita)"
az sql db create -g $Grupo -s $SqlServidor -n $SqlBase `
    --edition GeneralPurpose --family Gen5 --capacity 2 --compute-model Serverless `
    --use-free-limit --free-limit-exhaustion-behavior AutoPause --auto-pause-delay 60 -o none
if ($LASTEXITCODE -ne 0) {
    Write-Warning "La oferta gratuita no estuvo disponible; se crea la base Basic (5 DTU, aprox. 5 USD/mes de creditos)."
    az sql db create -g $Grupo -s $SqlServidor -n $SqlBase --edition Basic -o none; Revisar "crear base de datos"
}

Paso "Cuenta de almacenamiento $Storage y contenedor '$Contenedor'"
az storage account create -g $Grupo -n $Storage -l $Ubicacion --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2 -o none; Revisar "crear storage"
$StorageConn = az storage account show-connection-string -g $Grupo -n $Storage --query connectionString -o tsv; Revisar "leer connection string"
az storage container create -n $Contenedor --connection-string $StorageConn -o none; Revisar "crear contenedor"

Paso "App Service $WebApp (Linux, Python 3.12, SKU $SkuApp)"
az appservice plan create -g $Grupo -n $PlanApp -l $Ubicacion --is-linux --sku $SkuApp -o none; Revisar "crear plan"
az webapp create -g $Grupo -p $PlanApp -n $WebApp --runtime "PYTHON:3.12" -o none; Revisar "crear web app"

Paso "Variables de entorno de la API"
az webapp config appsettings set -g $Grupo -n $WebApp -o none --settings `
    "AZURE_SQL_SERVER=$SqlServidor.database.windows.net" `
    "AZURE_SQL_DB=$SqlBase" `
    "AZURE_SQL_USER=$SqlUsuario" `
    "AZURE_SQL_PASSWORD=$SqlPassword" `
    "AZURE_STORAGE_CONNECTION_STRING=$StorageConn" `
    "AZURE_STORAGE_CONTAINER=$Contenedor" `
    "AZURE_STORAGE_PUBLICO=false" `
    "SCM_DO_BUILD_DURING_DEPLOYMENT=true"
Revisar "configurar app settings"
az webapp config set -g $Grupo -n $WebApp -o none `
    --startup-file "gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --timeout 180 main:app"
Revisar "configurar comando de inicio"

Paso "Function App $FuncApp (serverless)"
az functionapp create -g $Grupo -n $FuncApp --storage-account $Storage `
    --consumption-plan-location $Ubicacion --os-type Linux --runtime python --runtime-version 3.11 --functions-version 4 -o none
if ($LASTEXITCODE -ne 0) {
    Write-Warning "El plan de consumo clasico no estuvo disponible; se intenta con Flex Consumption."
    az functionapp create -g $Grupo -n $FuncApp --storage-account $Storage `
        --flexconsumption-location $Ubicacion --runtime python --runtime-version 3.11 -o none
    Revisar "crear function app"
}

@"
API_URL=https://$WebApp.azurewebsites.net
FUNC_URL=https://$FuncApp.azurewebsites.net/api/ajuste-semanal
AZURE_SQL_SERVER=$SqlServidor.database.windows.net
AZURE_SQL_DB=$SqlBase
AZURE_SQL_USER=$SqlUsuario
AZURE_SQL_PASSWORD=$SqlPassword
AZURE_STORAGE_CONNECTION_STRING=$StorageConn
AZURE_STORAGE_CONTAINER=$Contenedor
"@ | Set-Content -Encoding UTF8 $ArchivoSalida

Write-Host "`nListo. Recursos creados en $Grupo." -ForegroundColor Green
Write-Host "Datos guardados en deploy\salida.env (no lo subas a GitHub)."
Write-Host "Siguiente paso: .\deploy\02_desplegar_api.ps1"
