---
name: Atualização do jogo na Steam / Game update
about: Avise quando To Pixelia atualizar na Steam e precisar de novos hashes
title: '[Update] Nova build do To Pixelia na Steam: '
labels: enhancement
---

## Dados da nova versão na Steam
- **Versão anunciada do jogo:**
- **Novo Steam Build ID** (em `appmanifest_1954160.acf` ou Propriedades > Atualizações na Steam):

## Hashes SHA-256 (opcional, ajuda muito!)
Execute no PowerShell dentro da pasta do jogo e cole aqui:
```powershell
Get-FileHash ".\GameAssembly.dll" -Algorithm SHA256
Get-FileHash ".\To Pixelia_Data\il2cpp_data\Metadata\global-metadata.dat" -Algorithm SHA256
```
