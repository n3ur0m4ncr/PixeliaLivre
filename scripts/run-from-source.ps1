<#
.SYNOPSIS
    Executa o Pixelia Livre diretamente pelo Python (sem PyInstaller .exe).
#>
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Entry = Join-Path $RepoRoot 'src\entry.py'

Write-Host 'Iniciando Pixelia Livre direto pelo código-fonte Python...' -ForegroundColor Cyan
python $Entry
