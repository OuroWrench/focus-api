# =====================================================================
#  Focus! - Paso 3: publicar la API serverless (Azure Functions)
#  Requiere Azure Functions Core Tools (comando "func").
# =====================================================================
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\config.ps1"

Push-Location (Join-Path $RaizRepo "serverless")
try {
    func azure functionapp publish $FuncApp --python
    if ($LASTEXITCODE -ne 0) { throw "Fallo la publicacion de la funcion" }
} finally { Pop-Location }

$url = "https://$FuncApp.azurewebsites.net/api/ajuste-semanal"
$cuerpo = @{ uso_real_min = 200; uso_meta_min = 210; limite_actual_min = 240 } | ConvertTo-Json
Write-Host "`nProbando $url ..."
Start-Sleep 10
$r = Invoke-RestMethod -Method Post -Uri $url -Body $cuerpo -ContentType "application/json"
Write-Host ("Respuesta: " + ($r | ConvertTo-Json -Compress)) -ForegroundColor Green
