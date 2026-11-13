# Changelog

Todas as alterações relevantes do **Pixelia Livre** são documentadas neste arquivo.

## [v1.1.28] - 2026-10-31

### Compatibilidade
- Atualizado o manifesto `src/compatibility.json` para **To Pixelia v1.1.28** (Steam app `1954160`, build `25632131`, Windows x86, Unity `2020.1.13f1`, IL2CPP).
- Hashes SHA-256 atualizados para `GameAssembly.dll` e `To Pixelia_Data/il2cpp_data/Metadata/global-metadata.dat`.
- Metadados IL2CPP inspecionados para validar presença das classes, campos e métodos de dinheiro, habilidades, Inteligência, necessidades, saúde, relógio e interface.

### Adicionado / Alterado
- Painel desktop bilíngue completo (**PT / EN**) com alternância dinâmica mantendo o estado da conexão e a habilidade selecionada.
- Desativação segura dos recursos de **Minigames e Basquete** (`"minigames_supported": false`) e dos atalhos `Ctrl+Alt+F11` / `F12` até que os RVAs nativos de `src/minigames.js` sejam revalidados para a build `25632131`.
- Documentação completa organizada para GitHub, incluindo guia passo a passo e análise detalhada sobre falsos positivos no VirusTotal.

### Limitações conhecidas
- Build compilada e validada via `--self-test` (inicialização do pacote, Tkinter, Tcl/Tk e recursos empacotados), porém **ainda não testada em uma sessão ao vivo dentro do jogo**.
- Assistência de minigames e basquete desativada temporariamente (`src/minigames.js` preservado como referência da build anterior `23486352`).

---

## [Anterior / Legado] - Build 23486352

- Versão anterior compatível com Steam build `23486352`, incluindo hooks experimentais de minigames e basquete via RVAs fixos em `minigames.js`.
