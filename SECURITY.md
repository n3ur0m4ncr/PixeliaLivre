# Política de Segurança e Transparência — Pixelia Livre

## Escopo e Uso Pretendido

O **Pixelia Livre** foi desenvolvido exclusivamente para uso local e **single-player** no jogo *To Pixelia* (Windows, Steam App ID `1954160`).

Por segurança, o agente (`src/agent.js`) e o backend (`src/backend.py`) verificam antes de atuar:
1. O nome do processo (`To Pixelia.exe`) e a arquitetura (`ia32` / 32 bits).
2. A integridade exata via **SHA-256** de `GameAssembly.dll` e `To Pixelia_Data/il2cpp_data/Metadata/global-metadata.dat` em comparação com `src/compatibility.json`.
3. A presença das classes, campos, tipos e métodos IL2CPP esperados em `Assembly-CSharp.dll`.

Se o jogo for atualizado na Steam e os hashes mudarem, o mod **recusa a conexão** em vez de gravar em endereços de memória desconhecidos.

---

## Sobre Falsos Positivos no VirusTotal e Antivírus

É comum que o executável compilado (`PixeliaLivre.exe`) dispare alertas heurísticos no **VirusTotal** ou no Windows Defender (por exemplo: `Dropper`, `Downloader`, `Injector`, `GameHack`, `Win32/Wacatac` ou `Suspicious.Cloud`).

### Por que isso acontece?

1. **Drop de arquivo em runtime (`src/bootstrap.py`):** para manter o pacote ZIP compacto (~12 MB), o build exclui o módulo `frida` (`--exclude-module frida`). Na primeira vez que você clica em **Conectar ao jogo**, `bootstrap.py` baixa o pacote oficial `frida-17.2.17-cp37-abi3-win_amd64.whl` (~42 MB) do PyPI e **extrai ("dropa") no disco** a biblioteca nativa `frida/_frida.pyd` dentro da pasta `runtime/frida-17.2.17/`. Sandboxes automáticas classificam esse padrão ("`.exe` baixa pacote da internet e grava DLL/pyd em subpasta") como comportamento de *Dropper/Downloader*.
2. **Bootloader do PyInstaller sem assinatura digital:** como o projeto não possui certificado comercial Authenticode/EV, o stub do PyInstaller costuma ser marcado por motores heurísticos genéricos.
3. **Anexação ao processo do jogo (`Frida` + `OpenProcess`):** o mod precisa ler e alterar valores em memória do processo `To Pixelia.exe` (`frida.attach` + `Interceptor.attach` em `GameAssembly.dll`), técnica naturalmente detectada por antivírus como *Process Injection* / *GameHack*.
4. **Monitoramento local de atalhos (`GetAsyncKeyState`):** `src/agent.js` consulta `user32.dll!GetAsyncKeyState` para os atalhos `Ctrl+Alt+F6..F10` **exclusivamente quando a janela em primeiro plano pertence ao PID do jogo**, o que motores estáticos às vezes confundem com keylogger.

### Garantias Implementadas no Código

Em `src/bootstrap.py`:
- Apenas requisições `HTTPS` para `pypi.org` e `files.pythonhosted.org` são aceitas (`_open`).
- A versão e o arquivo exato (`frida-17.2.17-cp37-abi3-win_amd64.whl`) são fixos no código.
- Tamanho máximo de download travado em `80 MB` (e `2 MB` para metadados JSON).
- Verificação rigorosa do **tamanho em bytes** e do digest **SHA-256** publicado pelo PyPI antes da extração.
- Proteção contra *Zip Slip* (rejeita caminhos com `..`, `:` ou `\`) e extração restrita aos diretórios `frida` e `frida-17.2.17.dist-info`.
- Registro auditável em `runtime/frida-17.2.17/download.json`.

Leia a explicação técnica completa em [`docs/FALSO-POSITIVO-VIRUSTOTAL.md`](docs/FALSO-POSITIVO-VIRUSTOTAL.md).

---

## Como Verificar a Integridade

1. Baixe apenas da aba [Releases](../../releases) deste repositório ou compile a partir do código-fonte (`scripts/build.ps1`).
2. Compare o hash SHA-256 do ZIP/executável com o arquivo `SHA256SUMS.txt` da release:
   ```powershell
   Get-FileHash .\PixeliaLivre.exe -Algorithm SHA256
   ```
3. Se preferir evitar o `.exe` do PyInstaller ou o download automático em runtime, consulte as instruções em [`docs/FALSO-POSITIVO-VIRUSTOTAL.md`](docs/FALSO-POSITIVO-VIRUSTOTAL.md) para executar direto pelo Python (`scripts/run-from-source.ps1`) ou pré-popular a pasta `runtime/frida-17.2.17/` offline.

## Reportando Problemas de Segurança

Caso encontre qualquer vulnerabilidade ou comportamento inesperado, abra uma issue privada/detalhada ou entre em contato com o mantenedor (`n3ur0m4ncr`).
