<#
.SYNOPSIS
    Compila o Pixelia Livre com PyInstaller, valida via --self-test e gera o ZIP + SHA256SUMS.txt.
#>
[CmdletBinding()]
param(
    [switch]$SkipSelfTest
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$SrcDir = Join-Path $RepoRoot 'src'
$ReleaseDir = Join-Path $RepoRoot 'release-assets'
$DistOut = Join-Path $SrcDir 'dist\PixeliaLivre'
$StageDir = Join-Path $ReleaseDir 'PixeliaLivre'

Write-Host '[1/6] Validando sintaxe Python...' -ForegroundColor Cyan
Get-ChildItem -Path $SrcDir -Filter '*.py' | ForEach-Object {
    python -m py_compile $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "Falha de sintaxe em $($_.Name)" }
}

Write-Host '[2/6] Limpando artefatos anteriores de build...' -ForegroundColor Cyan
foreach ($dir in @((Join-Path $SrcDir 'build'), (Join-Path $SrcDir 'dist'), $StageDir)) {
    if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
}
$SpecFile = Join-Path $SrcDir 'PixeliaLivre.spec'
if (Test-Path $SpecFile) { Remove-Item -Force $SpecFile }
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

Write-Host '[3/6] Compilando PixeliaLivre com PyInstaller...' -ForegroundColor Cyan
python (Join-Path $SrcDir 'build.py')
if ($LASTEXITCODE -ne 0) { throw 'Falha no PyInstaller build.py' }
if (-not (Test-Path (Join-Path $DistOut 'PixeliaLivre.exe'))) {
    throw 'PixeliaLivre.exe não foi gerado.'
}

Write-Host '[4/6] Montando pacote distribuível...' -ForegroundColor Cyan
Copy-Item -Path $DistOut -Destination $StageDir -Recurse -Force
Copy-Item -Path (Join-Path $RepoRoot 'README.md') -Destination (Join-Path $StageDir 'LEIA-ME.md') -Force
Copy-Item -Path (Join-Path $RepoRoot 'README.en.md') -Destination (Join-Path $StageDir 'README.en.md') -Force
Copy-Item -Path (Join-Path $RepoRoot 'LICENSE') -Destination (Join-Path $StageDir 'LICENSE') -Force
Copy-Item -Path (Join-Path $RepoRoot 'docs\VALIDACAO.md') -Destination (Join-Path $StageDir 'VALIDACAO.md') -Force
Copy-Item -Path (Join-Path $RepoRoot 'docs\FALSO-POSITIVO-VIRUSTOTAL.md') -Destination (Join-Path $StageDir 'FALSO-POSITIVO-VIRUSTOTAL.md') -Force

$StageSrc = Join-Path $StageDir 'Codigo-fonte'
New-Item -ItemType Directory -Force -Path $StageSrc | Out-Null
Get-ChildItem -Path $SrcDir -File | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $StageSrc -Force
}

$StageLic = Join-Path $StageDir 'Licencas'
New-Item -ItemType Directory -Force -Path $StageLic | Out-Null
Copy-Item -Path (Join-Path $RepoRoot 'licenses\*') -Destination $StageLic -Force

if (-not $SkipSelfTest) {
    Write-Host '[5/6] Executando --self-test no executável compilado...' -ForegroundColor Cyan
    $ExePath = Join-Path $StageDir 'PixeliaLivre.exe'
    $SelfTestJson = Join-Path $StageDir 'self-test.json'
    $LogFile = Join-Path $StageDir 'PixeliaLivre.log'
    $proc = Start-Process -FilePath $ExePath -ArgumentList '--self-test' -PassThru -Wait
    if ($proc.ExitCode -ne 0) { throw "PixeliaLivre.exe --self-test retornou código $($proc.ExitCode)" }
    if (-not (Test-Path $SelfTestJson)) { throw 'self-test.json não foi gerado.' }
    $report = Get-Content $SelfTestJson -Raw | ConvertFrom-Json
    if ($report.package_startup -ne 'passed' -or $report.tkinter -ne 'passed' -or -not $report.resources) {
        throw "Self-test falhou: $(Get-Content $SelfTestJson -Raw)"
    }
    Write-Host "    Self-test OK (tcl_library: $($report.tcl_library))" -ForegroundColor Green
    Remove-Item -Force $SelfTestJson -ErrorAction SilentlyContinue
    Remove-Item -Force $LogFile -ErrorAction SilentlyContinue
}

Write-Host '[6/6] Gerando ZIP e SHA256SUMS.txt...' -ForegroundColor Cyan
$Manifest = Get-Content (Join-Path $SrcDir 'compatibility.json') -Raw | ConvertFrom-Json
$Version = $Manifest.game_version
$ZipName = "PixeliaLivre-v$Version-win64.zip"
$ZipPath = Join-Path $ReleaseDir $ZipName
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }

python -c @"
import pathlib, zipfile
stage = pathlib.Path(r'$StageDir')
zip_path = pathlib.Path(r'$ZipPath')
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for item in sorted(stage.rglob('*')):
        if item.is_file():
            arcname = 'PixeliaLivre/' + item.relative_to(stage).as_posix()
            zf.write(item, arcname)
print('ZIP criado:', zip_path)
"@
if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar arquivo ZIP.' }

$ZipHash = (Get-FileHash -Path $ZipPath -Algorithm SHA256).Hash.ToLower()
$ExeHash = (Get-FileHash -Path (Join-Path $StageDir 'PixeliaLivre.exe') -Algorithm SHA256).Hash.ToLower()
$SumsPath = Join-Path $ReleaseDir 'SHA256SUMS.txt'
@(
    "$ZipHash  $ZipName"
    "$ExeHash  PixeliaLivre/PixeliaLivre.exe"
) | Set-Content -Path $SumsPath -Encoding UTF8

Get-ChildItem -Path $SrcDir -Filter '__pycache__' -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`nBuild concluído com sucesso!" -ForegroundColor Green
Write-Host "ZIP: $ZipPath"
Write-Host "SHA256: $SumsPath"
