# Relatório de Compatibilidade e Validação — v1.1.28

**Data de preparação da atualização:** `31/10/2026`  
**Alvo:** *To Pixelia* (Steam App ID `1954160`)

---

## Ambiente e Versão Verificada

| Item | Valor conferido |
| --- | --- |
| **Jogo** | To Pixelia |
| **Versão anunciada** | `v1.1.28` |
| **Steam App ID** | `1954160` |
| **Steam Build** | `25632131` (conferido no `appmanifest` local instalado) |
| **Plataforma / Engine** | Windows x86 (`ia32`), Unity `2020.1.13f1`, IL2CPP |

### Hashes SHA-256 conferidos (`src/compatibility.json`)

| Arquivo do jogo | SHA-256 esperado |
| --- | --- |
| `GameAssembly.dll` | `e3e4de497d31c8899e9441d23e8138462afab2b73e321f51bcd982b3545cdc07` |
| `To Pixelia_Data/il2cpp_data/Metadata/global-metadata.dat` | `beccf98791936d74975c20a5e9e63609eac990de6ca734873b9bd37cc1b07f88` |

---

## O que foi validado

1. **Inspeção de metadados IL2CPP da build 25632131:**
   - Conferida a presença das classes e métodos centrais usados por dinheiro, habilidades, Inteligência, necessidades, saúde, relógio e atualização de interface (`PlayerStats`, `Player`, `TimeManager`, `SceneControllerManager`, `UIManager`, `StatsValueChange`).
   - A validação de tipos de campos e assinaturas também é executada dinamicamente em runtime por `src/agent.js` antes de habilitar qualquer controle.
2. **Autoteste do pacote compilado (`PixeliaLivre.exe --self-test`):**
   - Executado após o empacotamento com PyInstaller `6.9.0` + Python `3.12.4`:
     - `package_startup`: `passed`
     - `tkinter`: `passed`
     - `resources`: `true` (`agent.js`, `minigames.js`, `compatibility.json` presentes)
     - `gameplay_tested`: `false`
   - Os hashes SHA-256 oficiais do pacote `.zip` e do `PixeliaLivre.exe` publicados acompanham cada versão no arquivo `SHA256SUMS.txt` na aba **Releases**.

---

## Limites Conhecidos desta Atualização

- **Sem teste ao vivo dentro de uma partida:** o pacote atualizado foi compilado e passou no `--self-test` de inicialização, porém **ainda não foi conectado ao jogo em uma sessão real** para validação prática das alterações em gameplay.
- **Minigames e basquete desativados (`minigames_supported: false`):** os endereços nativos fixos (RVAs) em `src/minigames.js` pertencem à Steam build anterior (`23486352`) e precisam ser revalidados na `GameAssembly.dll` da build `25632131` antes de reativar esses controles e os atalhos `Ctrl+Alt+F11` / `F12`.
- **Trava estrita de build:** o painel rejeita qualquer versão cujos arquivos `GameAssembly.dll` ou `global-metadata.dat` tenham SHA-256 diferente dos registrados acima.
