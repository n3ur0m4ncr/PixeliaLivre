# Pixelia Livre — Painel Single-Player para To Pixelia

[![Versão Suportada](https://img.shields.io/badge/To%20Pixelia-v1.1.28%20(build%2025632131)-9cddb9?style=flat-square)](#compatibilidade-e-status)
[![Plataforma](https://img.shields.io/badge/Windows-x86%20IL2CPP-233445?style=flat-square)](#compatibilidade-e-status)
[![Python](https://img.shields.io/badge/Python-3.12-304356?style=flat-square)](#rodar-do-código-fonte-ou-compilar)
[![Licença](https://img.shields.io/badge/Licença-MIT-blue?style=flat-square)](LICENSE)

Painel desktop bilíngue (**Português / English**) em Python + Tkinter com instrumentação **Frida (IL2CPP)** para ajuste de ritmo, habilidades, atributos, necessidades e dinheiro no modo single-player de **To Pixelia** (Steam).

> 📖 **Documentação completa:**
> - [**Guia Passo a Passo (Uso & Build)**](docs/GUIA-PASSO-A-PASSO.md)
> - [**Por que dá Falso Positivo no VirusTotal (Drop do Arquivo)**](docs/FALSO-POSITIVO-VIRUSTOTAL.md)
> - [**Arquitetura Interna (Diagramas & Módulos)**](docs/ARQUITETURA.md)
> - [**Relatório de Validação & Hashes**](docs/VALIDACAO.md)
> - [**English README**](README.en.md)

---

## Índice

1. [Recursos e Status Atual](#-recursos-e-status-atual)
2. [Instalação e Uso Rápido (Passo a Passo)](#-instalação-e-uso-rápido-passo-a-passo)
3. [Atalhos dentro do Jogo](#-atalhos-dentro-do-jogo)
4. [Falso Positivo no VirusTotal e "Drop" de Arquivo](#-falso-positivo-no-virustotal-e-drop-de-arquivo)
5. [Estrutura do Repositório](#-estrutura-do-repositório)
6. [Rodar do Código-Fonte ou Compilar](#-rodar-do-código-fonte-ou-compilar)
7. [Compatibilidade e Limitações Conhecidas](#-compatibilidade-e-limitações-conhecidas)
8. [Créditos e Licença](#-créditos-e-licença)

---

## ✨ Recursos e Status Atual

| Recurso | Status na v1.1.28 | Detalhes |
| --- | --- | --- |
| **Dinheiro** | ✅ Disponível | Adiciona de `1` a `10.000.000` por clique (limite de saldo de `2.000.000.000`). |
| **16 Habilidades** | ✅ Disponível | Define uma habilidade específica ou todas as 16 de uma vez entre `0` e `100`. |
| **Inteligência** | ✅ Disponível | Ajusta o atributo `intelligence` entre `0` e `100`. |
| **Necessidades sempre cheias** | ✅ Disponível | Mantém fome, energia, higiene, banheiro, humor e limpeza da roupa em `100`. |
| **Restaurar necessidades** | ✅ Disponível | Preenche as 6 necessidades uma única vez sob demanda. |
| **Manter saúde cheia** | ✅ Disponível | Mantém `health` em `100` durante as atualizações do personagem. |
| **Velocidade do relógio** | ✅ Disponível | `1×`, `2×`, `5×`, `10×` ou `20×` — multiplica apenas ticks normais de 1 segundo, respeitando pausas e transições. |
| **Interface Bilíngue (PT / EN)** | ✅ Disponível | Botões **PT / EN** no canto superior direito preservando conexão e seleção atual. |
| **Minigames e Basquete** | ⏸️ Desativado | Desativado nesta build até revalidação dos endereços nativos (RVAs) em `src/minigames.js`. |

> [!NOTE]
> A faixa `0–100` do painel representa o intervalo aceito pela interface, não uma afirmação sobre o teto oficial de cada habilidade no jogo.

---

## 🚀 Instalação e Uso Rápido (Passo a Passo)

1. **Baixe o pacote pronto** na aba [**Releases**](../../releases) (arquivo `PixeliaLivre-v1.1.28-win64.zip`).
2. **Extraia o ZIP inteiro** para uma pasta (ex.: `C:\Mods\PixeliaLivre\`).
   - Mantenha a pasta `_internal` sempre junto de `PixeliaLivre.exe`.
   - Não é necessário instalar Python nem Cheat Engine.
3. **Abra To Pixelia pela Steam** e entre em sua partida (carregue o personagem).
4. **Execute `PixeliaLivre.exe`** e clique em **Conectar ao jogo**.
5. **Na primeira conexão**, aguarde o download automático de aproximadamente **42 MB** do componente oficial do Frida direto do PyPI. Ele fica salvo na pasta `runtime/` e é reutilizado sem internet nas próximas execuções.
6. Volte à janela do jogo para usar os controles ou os atalhos. Mantenha o painel aberto enquanto estiver com efeitos ativos.

Para instruções detalhadas (incluindo verificação SHA-256, modo 100% offline e solução de erros), leia [`docs/GUIA-PASSO-A-PASSO.md`](docs/GUIA-PASSO-A-PASSO.md).

---

## ⌨️ Atalhos dentro do Jogo

Com a janela do **To Pixelia** em foco, segure **`Ctrl + Alt`** e pressione:

| Tecla | Ação |
| --- | --- |
| `F6` | Ativar / desativar **Necessidades não caem** |
| `F7` | Adicionar **+10.000** de dinheiro |
| `F8` | Definir as **16 habilidades para 100** |
| `F9` | Alternar velocidade do relógio: `1× → 2× → 5× → 10× → 20×` |
| `F10` | Ativar / desativar **Manter saúde cheia** |
| `F11` / `F12` | Desativados nesta atualização (não alteram o jogo) |

*(Em alguns notebooks é necessário pressionar também a tecla **`Fn`**.)*

---

## 🛡️ Falso Positivo no VirusTotal e "Drop" de Arquivo

Ao enviar `PixeliaLivre.exe` ao **VirusTotal**, alguns motores antivírus podem marcar alertas heurísticos genéricos (como *Dropper*, *Downloader*, *Injector*, `Win32/Wacatac` ou *RiskWare*). **Entenda o motivo técnico exato:**

1. **O "Drop" do Frida em runtime (`src/bootstrap.py`):**
   - O build (`src/build.py`) exclui o módulo `frida` (`--exclude-module frida`) para manter o ZIP compacto (~12 MB).
   - Na primeira conexão, `bootstrap.py` baixa o wheel oficial `frida-17.2.17-cp37-abi3-win_amd64.whl` do PyPI (`pypi.org` / `files.pythonhosted.org`), verifica o tamanho e o **SHA-256**, e **extrai ("dropa") no disco** a biblioteca nativa `frida/_frida.pyd` dentro da pasta `runtime/frida-17.2.17/`.
   - Sandboxes do VirusTotal classificam automaticamente qualquer `.exe` não assinado que baixa um pacote e grava uma DLL/`.pyd` no disco como padrão de **Dropper / Downloader**.
2. **PyInstaller sem assinatura digital:** o bootloader padrão do PyInstaller sem certificado comercial Authenticode gera falsos positivos recorrentes em motores de *machine learning*.
3. **Injeção em memória e hotkeys:** `backend.py` usa `OpenProcess` para validar o jogo, `frida` anexa em `To Pixelia.exe` para instalar hooks IL2CPP na `GameAssembly.dll`, e `agent.js` usa `GetAsyncKeyState` apenas quando a janela do jogo está em primeiro plano.

### Como você mesmo pode auditar e evitar isso
- **100% código aberto e sem ofuscação** na pasta [`src/`](src) (leia `bootstrap.py`, `backend.py`, `agent.js` e `panel.py`).
- **Travas de integridade em `src/bootstrap.py`:** só aceita HTTPS de `pypi.org` e `files.pythonhosted.org`, trava nome/versão do wheel, valida **SHA-256 oficial do PyPI**, bloqueia *Zip Slip* e grava `runtime/frida-17.2.17/download.json`.
- **Alternativa sem `.exe`:** execute direto pelo Python oficial via [`scripts/run-from-source.ps1`](scripts/run-from-source.ps1).
- **Alternativa sem download em runtime:** pré-popule `runtime/frida-17.2.17/` manualmente com o wheel baixado via `pip download` (passo a passo em [`docs/FALSO-POSITIVO-VIRUSTOTAL.md`](docs/FALSO-POSITIVO-VIRUSTOTAL.md)).

Leia a explicação completa em [**`docs/FALSO-POSITIVO-VIRUSTOTAL.md`**](docs/FALSO-POSITIVO-VIRUSTOTAL.md) e [**`SECURITY.md`**](SECURITY.md).

---

## 📁 Estrutura do Repositório

```text
PixeliaLivre/
├── .github/
│   ├── ISSUE_TEMPLATE/          # Templates organizados para bugs e updates do jogo
│   └── workflows/
│       └── build-release.yml    # Build reproduzível no Windows + autoteste + SHA256
├── docs/
│   ├── ARQUITETURA.md           # Diagramas Mermaid e fluxo interno dos módulos
│   ├── FALSO-POSITIVO-VIRUSTOTAL.md  # Análise técnica detalhada do drop e VirusTotal
│   ├── GUIA-PASSO-A-PASSO.md    # Manual completo para jogadores e desenvolvedores
│   └── VALIDACAO.md             # Hashes conferidos da Steam build 25632131 e limites
├── licenses/                    # Licenças do Python e PyInstaller incluídas no pacote
├── scripts/
│   ├── build.ps1                # Script local de build, --self-test, ZIP e SHA256SUMS.txt
│   └── run-from-source.ps1      # Execução direta pelo Python sem PyInstaller
├── src/
│   ├── agent.js                 # Agente Frida injetado no jogo (hooks IL2CPP + hotkeys)
│   ├── backend.py               # Verificação SHA-256 do jogo, attach Frida e RPC
│   ├── bootstrap.py             # Download e extração verificada (SHA-256) do Frida
│   ├── build.py                 # Configuração PyInstaller (--onedir --exclude-module frida)
│   ├── compatibility.json       # Manifesto da build Steam 25632131 (v1.1.28)
│   ├── entry.py                 # Ponto de entrada, fallback Tcl e --self-test
│   ├── minigames.js             # Hooks legados (build 23486352 — desativados na v1.1.28)
│   └── panel.py                 # Interface Tkinter bilíngue PT/EN
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE                      # Licença MIT
├── README.md                    # Documentação principal (PT-BR)
├── README.en.md                 # English documentation
├── requirements.txt
└── SECURITY.md
```

---

## 🛠️ Rodar do Código-Fonte ou Compilar

### Executar direto pelo Python (Windows, Python 3.12+)
```powershell
git clone https://github.com/n3ur0m4ncr/PixeliaLivre.git
cd PixeliaLivre
.\scripts\run-from-source.ps1
```

### Compilar o executável `.exe` + ZIP com SHA-256
```powershell
pip install -r requirements.txt
.\scripts\build.ps1
```
O script executa `py_compile`, compila via `src/build.py`, valida `PixeliaLivre.exe --self-test` e gera os artefatos em `release-assets/`.

---

## ⚠️ Compatibilidade e Limitações Conhecidas

- **Build suportada:** Steam App `1954160`, build **`25632131`** (*To Pixelia* **v1.1.28**, Windows x86, Unity `2020.1.13f1`, IL2CPP).
- **Trava de integridade:** o painel confere os hashes SHA-256 de `GameAssembly.dll` e `global-metadata.dat` antes de conectar. Se uma atualização da Steam alterar esses arquivos, a conexão é recusada por segurança.
- **Estado dos testes:** a atualização foi compilada e validada via `--self-test` (inicialização do painel, Tkinter e recursos), e os metadados IL2CPP da build `25632131` foram inspecionados; **a conexão e os efeitos dentro de uma partida real ainda aguardam confirmação prática em gameplay**.
- **Salvar e desconectar:** todas as opções começam desligadas. Desconectar, fechar o painel ou deixá-lo sem responder por **5 segundos** interrompe necessidades fixas, saúde cheia e aceleração de tempo. Valores já alterados (dinheiro, habilidades, Inteligência) permanecem se você salvar o jogo.
- **Logs e uso único:** erros são registrados em `PixeliaLivre.log` na pasta do executável. Não conecte duas instâncias do painel ao mesmo jogo simultaneamente.

---

## 👤 Créditos e Licença

- **Autoria / Crédito nos fontes:** `n3urom4nc3r` ([`@n3ur0m4ncr`](https://github.com/n3ur0m4ncr))
- **Licença:** [MIT License](LICENSE)
- **Componentes de runtime:** utiliza [Frida `17.2.17`](https://pypi.org/project/frida/17.2.17/) baixado do PyPI oficial via HTTPS com verificação SHA-256. Licenças do Python e PyInstaller acompanham o projeto em [`licenses/`](licenses).
