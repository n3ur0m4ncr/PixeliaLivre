# Guia Completo Passo a Passo — Pixelia Livre

Este guia ensina, passo a passo, **como instalar, usar, auditar e compilar** o **Pixelia Livre** para *To Pixelia* (Windows / Steam).

---

## Parte 1 — Para Jogadores (Uso do Executável)

### Passo 1: Conferir os pré-requisitos
- **Jogo:** *To Pixelia* na Steam, **versão 1.1.28** (**Steam build 25632131**, Windows x86 / IL2CPP).
- **Sistema:** Windows 10/11 (64 bits para rodar o painel; o jogo em si roda em 32 bits).
- **Internet (apenas na 1ª conexão):** necessária uma única vez para baixar o componente oficial do Frida (~42 MB) direto do PyPI.
- **Não precisa instalar:** Python nem Cheat Engine.

> [!TIP]
> Antes de usar qualquer mod em qualquer jogo, faça uma cópia de segurança (backup) do seu save por precaução.

---

### Passo 2: Baixar e extrair corretamente
1. Acesse a aba [**Releases**](../../releases) do repositório no GitHub e baixe o arquivo `.zip` da versão correspondente (`PixeliaLivre-v1.1.28-win64.zip`).
2. *(Opcional, recomendado)* Verifique a integridade do download no PowerShell comparando com o `SHA256SUMS.txt` da Release:
   ```powershell
   Get-FileHash .\PixeliaLivre-v1.1.28-win64.zip -Algorithm SHA256
   ```
3. **Extraia o `.zip` inteiro** para uma pasta comum (por exemplo, `C:\Mods\PixeliaLivre\`).
   - **Importante:** nunca execute `PixeliaLivre.exe` diretamente de dentro do ZIP nem mova o `.exe` para outro lugar separado da pasta `_internal\`.
   - A estrutura extraída deve ficar assim:
     ```text
     PixeliaLivre\
     ├── PixeliaLivre.exe
     ├── _internal\
     ├── Codigo-fonte\
     ├── Licencas\
     ├── LEIA-ME.md
     ├── README.en.md
     └── VALIDACAO.txt
     ```

> [!NOTE]
> Se o Windows Defender / SmartScreen ou o VirusTotal apontar alerta, leia o documento [`FALSO-POSITIVO-VIRUSTOTAL.md`](FALSO-POSITIVO-VIRUSTOTAL.md) antes de executar para entender exatamente por que isso acontece (por causa do *drop* do arquivo `frida/_frida.pyd` em `runtime/`, do PyInstaller sem assinatura e da anexação ao processo do jogo).

---

### Passo 3: Abrir o jogo e carregar seu personagem
1. Abra o **To Pixelia pela Steam** (ou clique no botão **Abrir pela Steam** dentro do painel, que dispara `steam://rungameid/1954160`).
2. Carregue seu save e entre na partida com o personagem ativo no mundo.
   - Enquanto estiver apenas no menu inicial ou em tela de carregamento (`sceneLoad_ActionBlocker` ativo), o painel exibirá o status **`AGUARDANDO PERSONAGEM`** e manterá os controles bloqueados por segurança.

---

### Passo 4: Conectar o painel (1ª execução)
1. Execute **`PixeliaLivre.exe`**.
2. Se desejar interface em inglês, clique em **EN** no canto superior direito (clique em **PT** para voltar ao português). A troca de idioma preserva a conexão e a habilidade selecionada.
3. Clique em **Conectar ao jogo**.
4. **Na primeira conexão**, o painel exibirá:
   > *"Conectando. Na primeira vez, será baixado um componente de 42 MB. Aguarde…"*
   - Nesse momento, o módulo `bootstrap.py` acessa `https://pypi.org/pypi/frida/17.2.17/json`, baixa o wheel oficial `frida-17.2.17-cp37-abi3-win_amd64.whl`, confere o **SHA-256** e extrai os arquivos para a subpasta:
     ```text
     PixeliaLivre\runtime\frida-17.2.17\
     ```
   - Nas próximas vezes em que abrir o painel, esse componente já estará salvo localmente e **não precisará baixar nada nem ter internet**.
5. Quando o jogo estiver com o personagem carregado, o selo no topo mudará para **`CONECTADO`** (em verde) e os cartões ficarão habilitados.

---

### Passo 5: Usando cada recurso do painel

| Seção no Painel | O que faz | Regras e limites |
| --- | --- | --- |
| **Dinheiro** | Adiciona o valor digitado ao saldo atual | Entre `1` e `10.000.000` por clique; saldo máximo travado em `2.000.000.000` (2 bilhões). |
| **Habilidades** | Define uma das 16 habilidades ou todas de uma vez | Aceita inteiros de `0` a `100` (intervalo do painel). |
| **Atributos** | Define o nível de **Inteligência** | Aceita inteiros de `0` a `100`. |
| **Necessidades não caem** | Mantém fome, energia, higiene, banheiro, humor e limpeza da roupa em `100` | Efeito temporário: só atua enquanto marcado e com o painel ativo. |
| **Restaurar necessidades** | Enche as 6 necessidades uma única vez | Ação pontual sem manter travado. |
| **Manter saúde cheia** | Mantém a saúde em `100` durante as atualizações | Efeito temporário enquanto marcado e conectado. |
| **Velocidade do relógio** | Multiplica a passagem do relógio: `1×`, `2×`, `5×`, `10×` ou `20×` | Só multiplica ticks normais de 1 segundo (`TimeManager.Update` → `UpdateGameSecond`), respeitando pausas e transições de cena. |
| **Minigames e basquete** | *(Desativado nesta build)* | Desabilitado na v1.1.28 até revalidação dos endereços nativos (RVAs). |

---

### Passo 6: Atalhos direto no jogo (Hotkeys)

Mantenha **`Ctrl + Alt`** pressionados com a janela de *To Pixelia* em foco e aperte a tecla:

| Atalho | Ação |
| --- | --- |
| `Ctrl + Alt + F6` | Liga/desliga **Necessidades não caem** |
| `Ctrl + Alt + F7` | Adiciona **+10.000** de dinheiro |
| `Ctrl + Alt + F8` | Define **todas as 16 habilidades para 100** |
| `Ctrl + Alt + F9` | Alterna velocidade do relógio: `1× → 2× → 5× → 10× → 20×` |
| `Ctrl + Alt + F10` | Liga/desliga **Manter saúde cheia** |
| `Ctrl + Alt + F11 / F12` | Desativados nesta atualização (não alteram o jogo) |

> [!NOTE]
> Em alguns notebooks, as teclas `F6`–`F12` exigem segurar também a tecla **`Fn`** (`Ctrl + Alt + Fn + F7`).

---

### Passo 7: Salvar, desconectar e *lease* de segurança

- **Tudo começa desligado** ao conectar.
- **Ao desconectar ou fechar o painel:** a manutenção de necessidades, saúde e aceleração do relógio param imediatamente.
- **O que permanece no save:** valores já alterados (como dinheiro, habilidades, Inteligência) e o tempo que já avançou **não são desfeitos** e serão gravados se o jogo salvar.
- **Proteção automática (*lease* de 5 segundos):** o painel envia um pulso (`snapshot`) a cada 1 segundo para o agente dentro do jogo. Se o painel travar ou for encerrado à força e ficar **mais de 5 segundos** sem responder, o agente zera automaticamente todos os efeitos contínuos (`freezeNeeds`, `freezeHealth`, `speed = 1`).

---

### Passo 8: Modo Avançado — Pré-instalar o Frida offline (sem download em runtime)

Se você não quer que `PixeliaLivre.exe` faça nenhum download na primeira execução:

1. Baixe manualmente o wheel oficial no PyPI usando o `pip`:
   ```powershell
   pip download --only-binary=:all: --platform win_amd64 --python-version 312 --no-deps frida==17.2.17 -d .\tmp_frida
   ```
2. Confira o SHA-256 do arquivo `.whl` baixado com o hash oficial da página do [frida 17.2.17 no PyPI](https://pypi.org/project/frida/17.2.17/#files).
3. Extraia de dentro do `.whl` (que é um ZIP comum) apenas as pastas `frida/` e `frida-17.2.17.dist-info/` para:
   ```text
   PixeliaLivre\runtime\frida-17.2.17\
   ```
4. Ao clicar em **Conectar ao jogo**, `bootstrap.py` detecta `runtime\frida-17.2.17\frida\__init__.py` e **não realiza nenhuma conexão externa**.

---

## Solução de Problemas Comuns

| Mensagem / Sintoma | Causa provável | Como resolver |
| --- | --- | --- |
| *"A versão do jogo difere da versão preparada (Steam build 25632131)"* | O jogo atualizou na Steam ou está em outra build. | Confira se o jogo está na v1.1.28; se atualizou, é preciso atualizar `compatibility.json` (veja `CONTRIBUTING.md`). |
| *"Não foi possível consultar o jogo. Abra o jogo e o painel com o mesmo usuário."* | Jogo rodando como Administrador e painel como usuário padrão (ou vice-versa). | Execute ambos com o mesmo nível de usuário (preferencialmente usuário padrão). |
| *"To Pixelia não está aberto"* | O processo `To Pixelia.exe` ainda não iniciou. | Abra o jogo pela Steam primeiro e aguarde carregar. |
| Erro envolvendo `init.tcl` | Ambiente Windows restringiu leitura de scripts Tcl dentro da pasta do usuário. | O `entry.py` tenta fallback para `C:\Python312\tcl`; mantenha `_internal\tcl` intacto junto do `.exe` ou extraia em `C:\Mods\PixeliaLivre`. |
| Erro na pasta `runtime` | Download interrompido deixou pasta parcial. | Apague a pasta `runtime\` ao lado do `.exe` e clique em **Conectar ao jogo** novamente. |
| Precisa diagnosticar um erro | — | Consulte o arquivo `PixeliaLivre.log` gerado na mesma pasta do executável. |

---

## Parte 2 — Para Desenvolvedores (Código-fonte e Build)

### 1. Executar direto pelo Python (sem `.exe`)
```powershell
git clone https://github.com/n3ur0m4ncr/PixeliaLivre.git
cd PixeliaLivre
.\scripts\run-from-source.ps1
```
Ou manualmente:
```powershell
python src\entry.py
```

### 2. Compilar o executável localmente com PyInstaller
Requer **Python 3.12 (Windows 64 bits)** com Tkinter/Tcl-Tk instalado.
```powershell
pip install -r requirements.txt
.\scripts\build.ps1
```
O script executa `python src\build.py`, copia a documentação/licenças/fontes, roda o autoteste (`PixeliaLivre.exe --self-test`) e gera o arquivo `.zip` + `SHA256SUMS.txt` em `release-assets\`.

### 3. Executar apenas o autoteste de empacotamento
```powershell
.\PixeliaLivre\PixeliaLivre.exe --self-test
Get-Content .\PixeliaLivre\self-test.json
```
Esse comando valida a abertura sem erros do app Tkinter, o carregamento de Tcl/Tk e a presença de `agent.js`, `minigames.js` e `compatibility.json` dentro de `_internal\`.
