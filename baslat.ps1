# Windows için başlatma betiği (PowerShell).
# Kullanım: proje klasöründe   .\baslat.ps1
Set-Location $PSScriptRoot
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "Masaüstü açılıyor... (ilk seferde birkaç saniye bekleyin)"
Start-Sleep -Seconds 4
Start-Process "http://localhost:6080/vnc.html?autoconnect=true&resize=scale"
