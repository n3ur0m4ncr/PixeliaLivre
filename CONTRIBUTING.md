# Como Contribuir — Pixelia Livre

Contribuições são muito bem-vindas, principalmente quando *To Pixelia* recebe atualizações na Steam e precisa de novos hashes ou revalidação de endereços nativos.

## Regras Gerais

1. **Mantenha o foco single-player e local.** Não adicione funcionalidades que alterem arquivos do jogo em disco permanentemente sem consentimento ou que afetem recursos online.
2. **Preserve o bloqueio por hash (`src/compatibility.json`).** Nunca remova a validação SHA-256 de `GameAssembly.dll` e `global-metadata.dat` antes do `frida.attach`.
3. **Sem binários no Git.** Não faça commit de `_internal/`, `dist/`, `build/`, `runtime/`, `.exe` ou `.zip`.

---

## Atualizando para uma Nova Build da Steam

Quando *To Pixelia* atualizar na Steam:

1. **Capture os metadados da nova instalação:**
   - Verifique o `buildid` no arquivo `appmanifest_1954160.acf` da sua biblioteca Steam.
   - Calcule os novos hashes SHA-256:
     ```powershell
     Get-FileHash "<PastaDoJogo>\GameAssembly.dll" -Algorithm SHA256
     Get-FileHash "<PastaDoJogo>\To Pixelia_Data\il2cpp_data\Metadata\global-metadata.dat" -Algorithm SHA256
     ```
2. **Atualize `src/compatibility.json`:**
   - Preencha `game_version`, `steam_build` e os dois valores em `sha256`.
   - Mantenha `"minigames_supported": false` até revalidar os RVAs de `src/minigames.js`.
3. **Valide classes, campos e métodos em `src/agent.js`:**
   - Confira nos metadados IL2CPP (por exemplo, com Il2CppDumper) se `PlayerStats`, `Player`, `TimeManager`, `SceneControllerManager`, `UIManager` e `StatsValueChange` mantiveram os mesmos nomes e tipos.
4. **(Opcional) Revalide os RVAs de `src/minigames.js`:**
   - Todos os hooks `miniProbe` e `hitProbe` usam offsets RVA relativos à base de `GameAssembly.dll` e checam o mnemônico/operandos da instrução antes de anexar. Atualize cada RVA para a nova `GameAssembly.dll` antes de mudar `"minigames_supported": true`.
5. **Teste localmente:**
   - Execute `.\scripts\build.ps1` para validar sintaxe, compilar e rodar `--self-test`.
   - Teste dentro de uma partida real do jogo antes de abrir um Pull Request.
