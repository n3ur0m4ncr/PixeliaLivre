# Por que ocorre Falso Positivo no VirusTotal (Drop de Arquivo & Heurística)

Se você enviou `PixeliaLivre.exe` (ou o `.zip` completo) para o **VirusTotal** ou o Windows Defender exibiu um alerta, **isso é esperado para este tipo de ferramenta** — e neste documento explicamos exatamente **por que acontece**, **o que é o "drop" do arquivo no código** e **como você mesmo pode auditar tudo linha por linha**.

---

## 1. O motivo principal: o "Drop" do componente Frida em runtime (`src/bootstrap.py`)

Quando uma pessoa analisa um programa no VirusTotal ou em uma sandbox de segurança, motores heurísticos observam o que o executável faz nos primeiros segundos após ser acionado.

No **Pixelia Livre**, o processo de empacotamento (`src/build.py`) usa intencionalmente a flag:

```python
'--exclude-module', 'frida'
```

Por que o `frida` foi excluído do `.exe`?
- O pacote do Frida para Windows (`frida-17.2.17-cp37-abi3-win_amd64.whl`) tem cerca de **42 MB** descompactados/baixados.
- Excluindo-o do build inicial, o ZIP distribuído cai de ~55 MB para cerca de **12 MB**, além de evitar distribuir binários pré-empacotados de terceiros sem verificação direta na fonte oficial (PyPI).

### O que acontece quando você clica em "Conectar ao jogo" (`ensure_frida()`):

```text
PixeliaLivre.exe (PyInstaller, sem assinatura digital)
   │
   ├─► 1. Faz GET HTTPS em https://pypi.org/pypi/frida/17.2.17/json
   ├─► 2. Baixa frida-17.2.17-cp37-abi3-win_amd64.whl de files.pythonhosted.org
   ├─► 3. Valida tamanho exato e hash SHA-256 oficial do PyPI
   ├─► 4. Extrai ("dropa" no disco) em runtime\frida-17.2.17\frida\_frida.pyd (DLL nativa)
   └─► 5. Carrega _frida.pyd em memória via importlib.import_module('frida')
```

### Por que o VirusTotal marca isso como suspeito?

Em análise comportamental/heurística de antivírus, o padrão:

1. **Executável não assinado** (`PixeliaLivre.exe`) +
2. **Conexão HTTPS para baixar um arquivo binário** +
3. **Extração/gravação ("drop") de uma extensão binária nativa (`.pyd` / DLL)** dentro de uma subpasta no disco (`runtime\frida-17.2.17\frida\_frida.pyd`) +
4. **Carregamento dinâmico desse binário recém-criado**

é classificado por motores heurísticos como comportamento típico de **Dropper / Downloader** (gerando rótulos genéricos como `Trojan.Downloader`, `Generic.Dropper`, `Suspicious.Cloud` ou `Behavior.Win32.Dropper`).

> [!IMPORTANT]
> **"Dropper"** em antivírus descreve o *mecanismo* (um programa que extrai/baixa e grava outro arquivo executável/DLL em disco), **não** prova malícia por si só. Instaladores legítimos e launchers também fazem drop de arquivos, mas grandes empresas pagam por **certificados digitais EV (Authenticode)** para entrar em whitelist — algo inviável em projetos comunitários gratuitos.

---

## 2. Os outros 3 fatores técnicos que somam pontuação heurística

Além do **drop** do `_frida.pyd`, o Pixelia Livre utiliza APIs de sistema que, juntas, disparam alertas em motores de *machine learning* no VirusTotal:

| Fator no Código | Onde está | Para que serve no mod | Como o Antivírus interpreta |
| --- | --- | --- | --- |
| **Bootloader PyInstaller sem assinatura** | `src/build.py` | Empacota Python 3.12 + Tkinter em `.exe` | Stub padrão do PyInstaller é muito marcado por heurísticas genéricas (`Win32/Wacatac`, `Gen:Variant`, `PyInstaller`). |
| **`OpenProcess` + Injeção IL2CPP** | `src/backend.py` + `frida` + `src/agent.js` | Verifica o caminho de `To Pixelia.exe` (`OpenProcess(0x1000, ...)`), anexa ao processo e instala hooks (`Interceptor.attach`) na `GameAssembly.dll` | Detectado como *Process Injection*, *Memory Patching* ou *GameHack / RiskWare*. É o único jeito de modificar o jogo em memória sem alterar arquivos da Steam. |
| **`GetAsyncKeyState` + `GetForegroundWindow`** | `src/agent.js` (linhas 167–188) | Lê atalhos `Ctrl+Alt+F6..F10` **somente** quando a janela em foco pertence ao `To Pixelia.exe` | Análise estática frequentemente acusa qualquer uso de `GetAsyncKeyState` como possível *Keylogger*. |

---

## 3. Como o código prova que o download/drop é seguro (`src/bootstrap.py`)

O arquivo [`src/bootstrap.py`](../src/bootstrap.py) foi escrito com travas rígidas de segurança para impedir qualquer redirecionamento malicioso ou adulteração do arquivo baixado:

1. **Whitelist estrita de domínios (`_open`, linhas 24–28):**
   - Exige `https://` e aceita **apenas** `pypi.org` e `files.pythonhosted.org`. Qualquer outro domínio gera exceção imediatamente.
2. **Versão e nome de pacote fixos (linhas 16–17):**
   - Travado exatamente em `VERSION = '17.2.17'` e `FILENAME = 'frida-17.2.17-cp37-abi3-win_amd64.whl'`.
3. **Limites de tamanho (linhas 18, 32 e 51):**
   - Metadados JSON limitados a `2 MB`; download do wheel limitado a `80 MB`.
4. **Verificação criptográfica SHA-256 (linha 55):**
   - Compara o tamanho em bytes e o `SHA-256` calculado localmente com o digest publicado na API oficial do PyPI antes de extrair qualquer arquivo.
5. **Proteção contra Zip Slip (linhas 60–65):**
   - Bloqueia caminhos contendo `..`, `:` ou `\`, e extrai **apenas** os diretórios `frida` e `frida-17.2.17.dist-info`.
6. **Trilha de auditoria local (linha 75):**
   - Grava `runtime\frida-17.2.17\download.json` contendo `version`, `sha256` e `source` URL exata do pacote baixado.

---

## 4. Como verificar ou rodar sem depender de executável pronto

Se você prefere **zero confiança cega**, existem 3 formas transparentes de usar o projeto:

### Opção A — Rodar direto pelo código-fonte em Python (Sem PyInstaller `.exe`)
1. Leia todos os arquivos da pasta [`src/`](../src) (`entry.py`, `panel.py`, `backend.py`, `bootstrap.py`, `agent.js`, `minigames.js`, `compatibility.json`). São menos de ~1.500 linhas somadas, sem ofuscação.
2. Execute direto com o Python oficial:
   ```powershell
   .\scripts\run-from-source.ps1
   ```
   *(Isso elimina completamente o stub bootloader do PyInstaller, que é o maior causador de falsos positivos estáticos no VirusTotal.)*

### Opção B — Pré-instalar o Frida offline na pasta `runtime/` (Sem "drop" automático)
Se você não quer que o `PixeliaLivre.exe` faça download nem extraia arquivos na rede:
1. Baixe você mesmo o wheel oficial do PyPI:
   ```powershell
   pip download --only-binary=:all: --platform win_amd64 --python-version 312 --no-deps frida==17.2.17 -d .\tmp_frida
   ```
2. Extraia manualmente as pastas `frida/` e `frida-17.2.17.dist-info/` de dentro do `.whl` para `PixeliaLivre\runtime\frida-17.2.17\`.
3. Quando `runtime\frida-17.2.17\frida\__init__.py` já existe, `bootstrap.py` **pula o download** e **não faz nenhum acesso à internet**.

### Opção C — Compilar seu próprio `.exe` (ou conferir o GitHub Actions)
1. Compile localmente com `.\scripts\build.ps1`.
2. Ou confira os logs de compilação pública na aba **Actions** do repositório GitHub, onde o `.exe` é gerado diretamente a partir deste código-fonte em ambiente limpo `windows-latest`, com hash SHA-256 registrado em `SHA256SUMS.txt`.
