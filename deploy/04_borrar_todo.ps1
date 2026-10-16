# Borra TODOS los recursos de Focus! (para no gastar creditos despues de la materia).
. "$PSScriptRoot\config.ps1"
$ok = Read-Host "Esto elimina el grupo $Grupo y todo su contenido. Escribe SI para continuar"
if ($ok -eq "SI") { az group delete -n $Grupo --yes --no-wait; Write-Host "Eliminacion en curso." }
