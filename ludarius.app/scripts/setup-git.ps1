# setup-git.ps1
# Uso: powershell -ExecutionPolicy Bypass -File .\scripts\setup-git.ps1
param(
    [string]$Name = "Lv16",
    [string]$Email = "lohran.hps@gmail.com",
    [switch]$Global = $true
)
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git não está disponível no PATH. Instale o Git ou abra o Git Bash/terminal correto."
    exit 1
}
if ($Global) {
    git config --global user.name $Name
    git config --global user.email $Email
    Write-Host "Configurado globalmente: user.name=$Name user.email=$Email"
} else {
    git config user.name $Name
    git config user.email $Email
    Write-Host "Configurado localmente neste repositório: user.name=$Name user.email=$Email"
}
Write-Host "--- Verificação ---"
git --version
git config --list
