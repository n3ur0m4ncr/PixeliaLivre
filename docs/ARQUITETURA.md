# Arquitetura Interna — Pixelia Livre

O **Pixelia Livre** é dividido em uma interface desktop desacoplada (Python + Tkinter), um gerenciador de conexão/integridade (Python + `ctypes` + Frida RPC) e um agente JavaScript executado dentro do runtime IL2CPP do jogo.

---

## Visão Geral dos Componentes

```mermaid
flowchart TD
    User["Jogador (Painel GUI ou Hotkeys Ctrl+Alt)"] --> Entry["src/entry.py<br/>Ponto de entrada, fallback Tcl e --self-test"]
    Entry --> Panel["src/panel.py<br/>Interface Tkinter PT/EN + Fila Thread-Safe"]
    Panel -->|Worker Thread| Backend["src/backend.py<br/>Valida processo, SHA-256 do jogo e RPC Frida"]
    Backend -->|1a conexao| Bootstrap["src/bootstrap.py<br/>Baixa wheel oficial frida 17.2.17 do PyPI c/ SHA-256"]
    Bootstrap -->|Extrai em runtime/| Frida["frida / _frida.pyd"]
    Backend -->|frida.attach + script.load| Agent["src/agent.js<br/>Hooks IL2CPP + Hotkeys user32.dll + Lease 5s"]
    Agent <-->|Interceptor.attach / Memory| Game["To Pixelia.exe (x86)<br/>GameAssembly.dll / Assembly-CSharp.dll"]
    Basket["src/basketball.js<br/>Hooks de basquete build 25632131"] -->|Carregado quando<br/>basketball_supported=true| Agent
    Legacy["src/minigames.js<br/>RVAs legados build 23486352"] -.->|Carregado apenas se<br/>minigames_supported=true| Agent
```

---

## Fluxo de Conexão e Segurança por Etapa

```mermaid
sequenceDiagram
    participant P as panel.py (UI Thread)
    participant W as backend.py (Worker Thread)
    participant B as bootstrap.py
    participant G as To Pixelia.exe (agent.js)

    P->>W: Conectar ao jogo
    W->>B: ensure_frida()
    alt runtime/frida-17.2.17 ausente
        B->>B: GET PyPI JSON + wheel (.whl) + verifica SHA-256
        B->>B: Extrai para runtime/frida-17.2.17/
    end
    W->>W: Localiza "to pixelia.exe" via Frida + OpenProcess(0x1000)
    W->>W: Confere SHA-256 de GameAssembly.dll e global-metadata.dat
    W->>G: frida.attach(pid) + load(agent.js)
    G->>G: Valida arch ia32, classes IL2CPP, campos, tipos e métodos
    loop A cada 1000 ms (polling)
        P->>W: snapshot()
        W->>G: rpc.exports.snapshot() -> renova lease (5s)
        G-->>P: Saldo, skills, atributos, necessidades, relógio
    end
```

---

## Responsabilidade de Cada Arquivo em `src/`

| Arquivo | Papel no Projeto |
| --- | --- |
| [`src/entry.py`](../src/entry.py) | Inicializa a aplicação Tkinter, aplica fallback para `C:/Python312/tcl` caso o ambiente restrinja scripts Tcl em *Documentos* e implementa `--self-test`. |
| [`src/panel.py`](../src/panel.py) | Constrói toda a UI bilíngue (**PT** / **EN**), executa chamadas ao backend em thread separada (`pixelia-worker`) e mantém a UI responsiva com filas `queue.Queue`. |
| [`src/backend.py`](../src/backend.py) | Consulta o caminho exato de `To Pixelia.exe` via `kernel32.dll`, valida hashes SHA-256 contra `compatibility.json`, injeta `agent.js` e grava diagnósticos em `PixeliaLivre.log`. |
| [`src/bootstrap.py`](../src/bootstrap.py) | Faz o download verificado (HTTPS + whitelist PyPI + SHA-256 + proteção contra Zip Slip) do wheel `frida-17.2.17` para `runtime/frida-17.2.17/`. |
| [`src/agent.js`](../src/agent.js) | Resolve APIs exportadas por `GameAssembly.dll` (`il2cpp_*`), valida classes e offsets de `Assembly-CSharp.dll`, anexa hooks em `Player.Update`, `TimeManager.Update`, `UIManager.Update` e `TimeManager.UpdateGameSecond`, além de gerenciar hotkeys via `user32.dll` e o *lease* de 5 segundos. |
| [`src/basketball.js`](../src/basketball.js) | Hooks revalidados para a build `25632131` em `Player_Basketball` (`0x60cb6e`) e `StreetBasketballPlayer` (`0x52c79a`), garantindo acertos de arremessos quando `options.autoBasket` está ativo e mantendo o loop `frame()` ativo nas cenas de basquete. |
| [`src/minigames.js`](../src/minigames.js) | Definições de hooks legados para os demais minigames (Steam build `23486352`). Só é concatenado ao script quando `"minigames_supported": true` no manifesto. |
| [`src/compatibility.json`](../src/compatibility.json) | Manifesto declarando jogo, Steam App ID (`1954160`), versão (`1.1.28`), Steam build (`25632131`), flags `minigames_supported` (`false`) e `basketball_supported` (`true`) e hashes SHA-256 exigidos. |
| [`src/build.py`](../src/build.py) | Script PyInstaller (`--onedir --windowed --exclude-module frida`) que empacota `PixeliaLivre.exe` com `agent.js`, `basketball.js`, `minigames.js`, `compatibility.json` e `python3.dll`. |

---

## Detalhes Técnicos Importantes do Agente (`agent.js`)

1. **Multiplicador seguro do relógio (`clockOrigins`):**
   - Ao inicializar, o agente lê até 100 instruções x86 a partir de `TimeManager.Update` usando `Instruction.parse` e registra os endereços de retorno de chamadas diretas (`call`) para `TimeManager.UpdateGameSecond`.
   - Quando `UpdateGameSecond` é chamado, o agente só replica ticks extras (`options.speed - 1`) se o `returnAddress` pertencer a `clockOrigins`, se o incremento for de 1 segundo normal (`args[1] === 1 && args[2] !== 0`), e se `!gameClockPaused && gameClockCanWork`. Saltos de tempo scriptados do jogo (dormir, viagens, eventos) não são multiplicados.
2. **Lease de segurança (Dead-man's switch de 5 segundos):**
   - Sempre que `snapshot()` ou `command()` é chamado, `lease = Date.now()` é atualizado.
   - Se o painel travar ou fechar inesperadamente e `Date.now() - lease > 5000`, `frame()` reseta `options = defaults()`, desativando imediatamente manutenção de necessidades, saúde e aceleração.
3. **Verificação estrita de tipos IL2CPP:**
   - Antes de ativar qualquer hook, `field(c, n, t, stat)` verifica nome, tipo (`System.Single`, `System.Int32`, `System.Boolean`, etc.) e flag estática (`0x10`), evitando escrita corrompida caso uma atualização altere estruturas internas.
