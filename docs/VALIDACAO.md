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

1. **Inspeção de metadados IL2CPP e disassembly x86 da build 25632131:**
   - Conferida a presença das classes e métodos centrais usados por dinheiro, habilidades, Inteligência, necessidades, saúde, relógio e atualização de interface (`PlayerStats`, `Player`, `TimeManager`, `SceneControllerManager`, `UIManager`, `StatsValueChange`).
   - Revalidados na `GameAssembly.dll` e `global-metadata.dat` locais da build `25632131` os endereços nativos de basquete em [`src/basketball.js`](../src/basketball.js):
     - `Player_Basketball.Player_ShotTaken` (`0x60c760`) → instrução `movd xmm0, edi` (`66 0f 6e c7`) em RVA `0x60cb6e` (cobre partidas e lances livres via `FreeThrow`).
     - `StreetBasketballPlayer.Player_ShotTaken` (`0x52c5d0`) → instrução `movd xmm0, edi` (`66 0f 6e c7`) em RVA `0x52c79a` (cobre basquete de rua).
     - `Player_Basketball.Update` (`0x610b60`) e `StreetBasketballPlayer.Update` (`0x52de90`) confirmados com 0 argumentos e implementação ativa.
   - A validação de tipos de campos, instruções (`Instruction.parse`) e assinaturas também é executada dinamicamente em runtime por `src/agent.js` e `src/basketball.js` antes de habilitar qualquer controle.
2. **Autoteste do pacote compilado (`PixeliaLivre.exe --self-test`):**
   - Executado após o empacotamento com PyInstaller `6.9.0` + Python `3.12.4`:
     - `package_startup`: `passed`
     - `tkinter`: `passed`
     - `resources`: `true` (`agent.js`, `basketball.js`, `minigames.js`, `compatibility.json`, `locales/en.json`, `locales/pt.json` presentes)
     - `detected_language` / `available_locales`: confirma detecção automática do idioma do Windows e carregamento dos 13 pacotes nativos
     - `gameplay_tested`: `false`
   - Os hashes SHA-256 oficiais do pacote `.zip` e do `PixeliaLivre.exe` publicados acompanham cada versão no arquivo `SHA256SUMS.txt` na aba **Releases**.

---

## Limites Conhecidos desta Atualização

- **Sem teste ao vivo dentro de uma partida:** o pacote atualizado foi compilado e passou no `--self-test` de inicialização, e os RVAs de basquete foram confirmados por disassembly estático na `GameAssembly.dll` da build `25632131`, porém **o funcionamento dentro de uma partida real ainda aguarda validação prática em gameplay**.
- **Demais minigames desativados (`minigames_supported: false`, `basketball_supported: true`):** apenas os hooks de basquete em `src/basketball.js` foram revalidados para a build `25632131`. Os endereços nativos dos demais minigames em `src/minigames.js` pertencem à Steam build anterior (`23486352`) e continuam desativados até revalidação (atalho `Ctrl+Alt+F11` sem efeito; `Ctrl+Alt+F12` ativo para basquete).
- **Trava estrita de build:** o painel rejeita qualquer versão cujos arquivos `GameAssembly.dll` ou `global-metadata.dat` tenham SHA-256 diferente dos registrados acima.
