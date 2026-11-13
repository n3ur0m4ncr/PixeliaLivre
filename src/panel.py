"""Pixelia Livre desktop panel. All game operations use a worker thread."""
# Project credit: n3urom4nc3r

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from backend import Backend


SKILLS = {
    "Computação": "computer",
    "Escrita": "writing",
    "Culinária": "cooking",
    "Violão": "guitar",
    "Piano": "piano",
    "Pintura": "painting",
    "Bateria": "drumming",
    "Canto": "singing",
    "Conversação": "conversation",
    "Carreira de modelo": "modelling",
    "Basquete": "basketball",
    "Comédia": "comedy",
    "Romance": "romance",
    "Arrombamento": "lockpicking",
    "Direção": "driving",
    "Agricultura": "farming",
}
SKILLS_EN = {
    "Computação": "Computing", "Escrita": "Writing", "Culinária": "Cooking",
    "Violão": "Guitar", "Piano": "Piano", "Pintura": "Painting", "Bateria": "Drums",
    "Canto": "Singing", "Conversação": "Conversation", "Carreira de modelo": "Modeling",
    "Basquete": "Basketball", "Comédia": "Comedy", "Romance": "Romance",
    "Arrombamento": "Lockpicking", "Direção": "Driving", "Agricultura": "Farming",
}
TEXT_EN = {
    "DESCONECTADO": "DISCONNECTED", "Seu ritmo. Suas possibilidades.": "Your pace. Your possibilities.",
    "Conectar ao jogo": "Connect to game", "Desconectar": "Disconnect", "Abrir pela Steam": "Launch through Steam",
    "Abra To Pixelia, carregue seu personagem e conecte o painel.": "Open To Pixelia, load your character, then connect the panel.",
    "Dinheiro": "Money", "ALTERA O PERSONAGEM": "CHARACTER SETTINGS", "Saldo: —": "Balance: —",
    "Adicionar dinheiro": "Add money", "Habilidades": "Skills", "16 HABILIDADES · NÍVEIS 0–100": "16 SKILLS · LEVELS 0–100",
    "Atual: —": "Current: —", "Aplicar nível": "Set level", "Definir todas de uma vez": "Set every skill", "Aplicar a todas": "Set all",
    "Atributos": "Attributes", "INTELIGÊNCIA · NÍVEL 0–100": "INTELLIGENCE · LEVEL 0–100",
    "Inteligência atual: —": "Current intelligence: —", "Definir inteligência": "Set intelligence",
    "Tempo e bem-estar": "Time and wellbeing", "EFEITOS TEMPORÁRIOS": "TEMPORARY EFFECTS",
    "Necessidades não caem": "Needs do not decrease", "Manter saúde cheia": "Keep health full",
    "Velocidade do relógio": "Clock speed", "Restaurar necessidades": "Refill needs",
    "A velocidade escolhida é aplicada ao selecionar.": "The selected speed takes effect immediately.",
    "Minigames e basquete": "Minigames and basketball", "ACERTOS E ASSISTÊNCIA": "SUCCESS AND ASSISTANCE",
    "Acertos e assistência nos minigames": "Minigame success and assistance",
    "Acertar arremessos de basquete (rua, partidas e lances livres)": "Make basketball shots (street, matches, and free throws)",
    "Inicie a atividade normalmente. No basquete, mova e arremesse você mesmo.\nRecursos experimentais; consulte a cobertura no LEIA-ME.":
        "Start activities as usual. In basketball, move and shoot yourself.\nExperimental features; see README for coverage.",
    "Assistência de minigames e basquete desativada nesta atualização; os outros controles estão disponíveis.":
        "Minigame and basketball assistance is disabled for this game update; other controls are available.",
    "F11/F12 e a assistência de minigames estão desativados nesta build.":
        "F11/F12 and minigame assistance are disabled for this build.",
    "Uso local, para um jogador. Dinheiro e habilidades permanecem ao salvar o jogo.\nOs efeitos começam desligados. Desconectar interrompe a manutenção e a aceleração.\nNo jogo: Ctrl+Alt+F6 necessidades • F7 +10 mil • F8 habilidades 100\nCtrl+Alt+F9 velocidade • F10 saúde. • F11 minigames • F12 basquete.":
        "Local single-player use. Money and skills can persist when the game saves.\nEffects start disabled. Disconnecting stops maintenance and time acceleration.\nIn game: Ctrl+Alt+F6 needs • F7 +10,000 • F8 all skills to 100\nCtrl+Alt+F9 speed • F10 health. • F11 minigames • F12 basketball.",
    "Uso local, para um jogador. Dinheiro e habilidades permanecem ao salvar o jogo.\nOs efeitos começam desligados. Desconectar interrompe a manutenção e a aceleração.\nNo jogo: Ctrl+Alt+F6 necessidades • F7 +10 mil • F8 habilidades 100\nCtrl+Alt+F9 velocidade • F10 saúde.\nF11/F12 e a assistência de minigames estão desativados nesta build.":
        "Local single-player use. Money and skills can persist when the game saves.\nEffects start disabled. Disconnecting stops maintenance and time acceleration.\nIn game: Ctrl+Alt+F6 needs • F7 +10,000 • F8 all skills to 100\nCtrl+Alt+F9 speed • F10 health.\nF11/F12 and minigame assistance are disabled for this build.",
    "Uso local, para um jogador. Dinheiro e habilidades permanecem ao salvar o jogo.\nOs efeitos começam desligados. Desconectar interrompe a manutenção e a aceleração.\nNo jogo: Ctrl+Alt+F6 necessidades • F7 +10 mil • F8 habilidades 100\nCtrl+Alt+F9 velocidade • F10 saúde • F11 minigames • F12 basquete.":
        "Local single-player use. Money and skills can persist when the game saves.\nEffects start disabled. Disconnecting stops maintenance and time acceleration.\nIn game: Ctrl+Alt+F6 needs • F7 +10,000 • F8 all skills to 100\nCtrl+Alt+F9 speed • F10 health • F11 minigames • F12 basketball.",
    "ENCERRANDO": "CLOSING", "PROCESSANDO…": "PROCESSING…", "CONECTADO": "CONNECTED",
    "AGUARDANDO PERSONAGEM": "WAITING FOR CHARACTER", "Aguardando o jogo e seu personagem…": "Waiting for the game and your character…",
    "Conectado. Alterações disponíveis.": "Connected. Options are available.",
    "Conectado. Aguardando o personagem…": "Connected. Waiting for your character…",
    "Não foi possível conectar ao jogo.": "Could not connect to the game.", "Alteração aplicada.": "Change applied.",
    "Aguardando o carregamento da partida.": "Waiting for the game session to load.",
    "Aguarde o carregamento da partida.": "Wait for the game session to load.",
    "Aguarde o comando anterior.": "Please wait for the previous command.",
    "O jogo não respondeu. O comando foi cancelado.": "The game did not respond. The command was canceled.",
    "O jogo ainda está iniciando. Tente conectar novamente.": "The game is still starting. Try connecting again.",
    "Os componentes de To Pixelia ainda não foram carregados.": "To Pixelia components have not loaded yet.",
    "Entre em uma partida para habilitar o painel.": "Load a game to enable the panel.",
    "Conectado ao To Pixelia. Opções prontas.": "Connected to To Pixelia. Options are ready.",
    "Entre em uma partida e aguarde o carregamento.": "Load a game and wait for it to finish loading.",
    "Esta edição exige To Pixelia para Windows, 32 bits.": "This build requires the 32-bit Windows version of To Pixelia.",
    "Versão incompatível. Atualize o mod para a versão atual do jogo.": "Unsupported game version. Update the mod for the current game version.",
    "Opção inválida.": "Invalid option.", "Velocidade inválida.": "Invalid speed.",
    "Informe de 1 a 10.000.000.": "Enter a value from 1 to 10,000,000.",
    "Habilidade ou nível inválido.": "Invalid skill or level.", "Informe um nível de 0 a 100.": "Enter a level from 0 to 100.",
    "Atributo ou nível inválido.": "Invalid attribute or level.", "Comando desconhecido.": "Unknown command.",
    "Limite de dinheiro atingido (2 bilhões).": "Money limit reached (2 billion).",
    "Valor aplicado; reabra a tela de atributos para atualizar a interface.": "Value applied; reopen the attributes screen to refresh the display.",
    "Atalhos indisponíveis; utilize o painel.": "Hotkeys are unavailable; use the panel.",
    "Aguardando uma partida carregada.": "Waiting for a loaded game session.",
    "O jogo está carregando ou sem atualizar. Aguarde.": "The game is loading or paused. Please wait.",
    "Não foi possível validar o controle do relógio nesta versão.": "Could not verify clock control for this game version.",
    "O jogo recusou a atualização da interface.": "The game rejected the interface update.",
    "Aguarde o jogo e seu personagem…": "Waiting for the game and your character…",
    "Jogo desconectado. Abra-o e conecte novamente.": "Game disconnected. Reopen it and reconnect.",
    "To Pixelia não está aberto. Abra o jogo pela Steam primeiro.": "To Pixelia is not open. Launch the game through Steam first.",
    "Há mais de uma cópia de To Pixelia aberta. Deixe apenas uma.": "More than one copy of To Pixelia is open. Leave only one running.",
    "Processo incompatível.": "Unsupported process.",
    "Conecte o painel ao jogo primeiro.": "Connect the panel to the game first.",
    "Dinheiro": "Money", "Nível da habilidade": "Skill level",
    "Nível das habilidades": "Skill level", "Inteligência": "Intelligence",
    "Falha ao iniciar o mod.": "Could not start the mod.",
    "O mod foi desconectado pelo jogo.": "The game disconnected the mod.",
    "O jogo não está atualizando. Aguarde ou reconecte.": "The game is not updating. Wait or reconnect.",
    "O jogo ainda está iniciando. Tente conectar novamente.": "The game is still starting. Try connecting again.",
    "Aplicando alteração ao personagem…": "Applying change to your character…",
    "Solicitando abertura de To Pixelia pela Steam…": "Launching To Pixelia through Steam…",
    "Abertura solicitada à Steam. Carregue seu personagem e conecte o painel.": "Launch requested through Steam. Load your character and connect the panel.",
    "Conectando. Na primeira vez, será baixado um componente de 42 MB. Aguarde…": "Connecting. A 42 MB component downloads the first time. Please wait…",
    "Desconectando e restaurando efeitos temporários…": "Disconnecting and restoring temporary effects…",
    "Conectado. Aguardando o personagem…": "Connected. Waiting for your character…",
    "Desconectado. Os efeitos temporários foram desativados.": "Disconnected. Temporary effects have been disabled.",
    "Encerrando e desativando efeitos temporários…": "Closing and disabling temporary effects…",
}

COLORS = {
    "bg": "#101923",
    "card": "#192634",
    "field": "#233445",
    "border": "#304356",
    "text": "#e8f0f4",
    "muted": "#a2b5c3",
    "green": "#9cddb9",
    "green_hover": "#b7ebcd",
    "ink": "#17382a",
    "error": "#f2b8a9",
}


class App(tk.Tk):
    """Interface com fila serial e atualização exclusiva pelo thread principal."""

    def __init__(self, backend: Backend | None = None) -> None:
        super().__init__()
        self.backend = backend if backend is not None else Backend()
        self.minigames_supported = bool(self.backend.manifest.get("minigames_supported", True))
        self.language = "pt"
        self.title("Pixelia Livre")
        self.geometry("780x760")
        self.minsize(720, 620)
        self.configure(bg=COLORS["bg"])
        self._jobs: queue.Queue = queue.Queue()
        self._results: queue.Queue = queue.Queue()
        self._pending: dict[int, str] = {}
        self._next_id = 0
        self._closing = False
        self._close_deadline = 0.0
        self._connected = False
        self._ready = False
        self._state: dict[str, Any] = {}
        self._controls: list[tuple[tk.Widget, str]] = []
        self._message_until = 0.0
        self._last_error = ""

        self.money_amount = tk.StringVar(value="10000")
        self.skill_name = tk.StringVar(value=next(iter(SKILLS)))
        self.skill_value = tk.StringVar(value="100")
        self.all_skill_value = tk.StringVar(value="100")
        self.intelligence_value = tk.StringVar(value="100")
        self.speed_value = tk.StringVar(value="1× — normal")
        self.needs_value = tk.BooleanVar(value=False)
        self.health_value = tk.BooleanVar(value=False)
        self.minigames_value = tk.BooleanVar(value=False)
        self.basket_value = tk.BooleanVar(value=False)

        self._style()
        self._build()
        self._refresh_controls()
        self.protocol("WM_DELETE_WINDOW", self._close)
        threading.Thread(target=self._worker, daemon=True, name="pixelia-worker").start()
        self.bind_all("<MouseWheel>", self._mousewheel)
        self.after(80, self._drain_results)
        self.after(1000, self._poll_snapshot)

    def _tx(self, text: str) -> str:
        if self.language == "en":
            if text in TEXT_EN:
                return TEXT_EN[text]
            for pt, en in (("Saldo: ", "Balance: "), ("Atual: ", "Current: "),
                           ("Inteligência atual: ", "Current intelligence: ")):
                if text.startswith(pt):
                    return en + text[len(pt):]
            if text.startswith("Minigame sem implementação:"):
                return text.replace("Minigame sem implementação:", "Minigame is unavailable:", 1)
            if ": digite um número inteiro entre " in text:
                label, bounds = text.split(": digite um número inteiro entre ", 1)
                return f"{self._tx(label)}: enter a whole number from " + bounds.replace(" e ", " to ")
            if ": use um valor entre " in text:
                label, bounds = text.split(": use um valor entre ", 1)
                return f"{self._tx(label)}: enter a value from " + bounds.replace(" e ", " to ")
            return text
        return text

    def _set_language(self, language: str) -> None:
        if language not in ("pt", "en") or language == self.language:
            return
        skill_id = SKILLS.get(self.skill_name.get())
        self.language = language
        labels = SKILLS_EN if language == "en" else {name: name for name in SKILLS}
        self.skill_name.set(next((label for name, label in labels.items()
                                  if SKILLS[name] == skill_id), next(iter(labels.values()))))
        self.title(self._tx("Pixelia Livre"))
        self._build()
        self._show_values()
        self._refresh_controls()

    def _style(self) -> None:
        self.option_add("*Font", "{Segoe UI} 10")
        self.option_add("*TCombobox*Listbox.background", COLORS["field"])
        self.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
        self.option_add("*TCombobox*Listbox.selectBackground", COLORS["green"])
        self.option_add("*TCombobox*Listbox.selectForeground", COLORS["ink"])
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Pixel.TEntry", fieldbackground=COLORS["field"],
            foreground=COLORS["text"], bordercolor=COLORS["border"],
            lightcolor=COLORS["border"], darkcolor=COLORS["border"],
            insertcolor=COLORS["text"], padding=(9, 7),
        )
        style.configure(
            "Pixel.TCombobox", fieldbackground=COLORS["field"],
            background=COLORS["field"], foreground=COLORS["text"],
            arrowcolor=COLORS["muted"], bordercolor=COLORS["border"],
            lightcolor=COLORS["border"], darkcolor=COLORS["border"], padding=(9, 7),
        )
        for name in ("Pixel.TEntry", "Pixel.TCombobox"):
            style.map(name, foreground=[("disabled", "#738797")],
                      fieldbackground=[("disabled", "#1c2b39"),
                                       ("readonly", COLORS["field"])])
        style.configure("Pixel.Vertical.TScrollbar", background=COLORS["field"],
                        troughcolor=COLORS["bg"], bordercolor=COLORS["bg"],
                        arrowcolor=COLORS["muted"], width=10)

    def _label(self, parent: tk.Widget, text: str = "", *, size: int = 10,
               bold: bool = False, color: str = "text", **kw: Any) -> tk.Label:
        return tk.Label(parent, text=self._tx(text), bg=parent.cget("bg"), fg=COLORS[color],
                        font=("Segoe UI", size, "bold" if bold else "normal"),
                        anchor="w", **kw)

    def _button(self, parent: tk.Widget, text: str, command: Callable,
                *, primary: bool = False, control: bool = True, **kw: Any) -> tk.Button:
        button = tk.Button(
            parent, text=self._tx(text), command=command, relief="flat", bd=0,
            bg=COLORS["green"] if primary else COLORS["field"],
            fg=COLORS["ink"] if primary else COLORS["text"],
            activebackground=COLORS["green_hover"] if primary else COLORS["border"],
            activeforeground=COLORS["ink"] if primary else COLORS["text"],
            disabledforeground="#6e8392", cursor="hand2", padx=14, pady=9,
            font=("Segoe UI", 10, "bold"), highlightthickness=0, **kw,
        )
        if control:
            self._controls.append((button, "normal"))
        return button

    def _entry(self, parent: tk.Widget, variable: tk.StringVar, width: int = 12) -> ttk.Entry:
        widget = ttk.Entry(parent, textvariable=variable, width=width, style="Pixel.TEntry")
        self._controls.append((widget, "normal"))
        return widget

    def _card(self, parent: tk.Widget, title: str, eyebrow: str) -> tk.Frame:
        card = tk.Frame(parent, bg=COLORS["card"], padx=18, pady=13,
                        highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))
        heading = tk.Frame(card, bg=COLORS["card"])
        heading.pack(fill="x", pady=(0, 10))
        self._label(heading, title, size=12, bold=True).pack(side="left")
        self._label(heading, eyebrow, size=9, color="muted").pack(side="right")
        return card

    def _build(self) -> None:
        # Recreate only the view when changing language; the game connection stays intact.
        for child in self.winfo_children():
            child.destroy()
        self._controls = []
        # The scrollable surface also keeps long connection/error messages readable.
        shell = tk.Frame(self, bg=COLORS["bg"])
        shell.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(shell, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=self.canvas.yview,
                                  style="Pixel.Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=COLORS["bg"], padx=22, pady=18)
        self._body_window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda event: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._resize)

        header = tk.Frame(self.body, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 4))
        self._label(header, "Pixelia Livre", size=25, bold=True).pack(side="left")
        language_row = tk.Frame(header, bg=COLORS["bg"])
        language_row.pack(side="right", padx=(8, 10), pady=(6, 0))
        for code, label in (("pt", "PT"), ("en", "EN")):
            tk.Button(language_row, text=label, command=lambda c=code: self._set_language(c),
                      relief="flat", bd=0, padx=8, pady=4, cursor="hand2",
                      bg=COLORS["green"] if code == self.language else COLORS["field"],
                      fg=COLORS["ink"] if code == self.language else COLORS["muted"],
                      font=("Segoe UI", 9, "bold")).pack(side="left", padx=2)
        self.badge = self._label(header, "DESCONECTADO", size=9, bold=True, color="muted")
        self.badge.pack(side="right", pady=(8, 0))
        self._label(self.body, "Seu ritmo. Suas possibilidades.", size=11,
                    color="muted").pack(fill="x", pady=(0, 15))

        connection = tk.Frame(self.body, bg=COLORS["bg"])
        connection.pack(fill="x", pady=(0, 8))
        self.connect_button = self._button(connection, "Conectar ao jogo", self._connect,
                                            primary=True, control=False)
        self.connect_button.pack(side="left")
        self.launch_button = self._button(connection, "Abrir pela Steam", self._launch,
                                           control=False)
        self.launch_button.pack(side="left", padx=(10, 0))
        self.status_label = self._label(
            self.body, "Abra To Pixelia, carregue seu personagem e conecte o painel.",
            color="muted", justify="left", wraplength=690,
        )
        self.status_label.pack(fill="x", pady=(0, 14))

        money = self._card(self.body, "Dinheiro", "ALTERA O PERSONAGEM")
        row = tk.Frame(money, bg=COLORS["card"])
        row.pack(fill="x")
        self.money_label = self._label(row, "Saldo: —", size=14, bold=True, color="green")
        self.money_label.pack(side="left", fill="x", expand=True)
        self._entry(row, self.money_amount, 12).pack(side="left", padx=(10, 8))
        self._button(row, "Adicionar dinheiro", self._add_money, primary=True).pack(side="left")

        skills = self._card(self.body, "Habilidades", "16 HABILIDADES · NÍVEIS 0–100")
        skill_row = tk.Frame(skills, bg=COLORS["card"])
        skill_row.pack(fill="x", pady=(0, 9))
        labels = SKILLS_EN if self.language == "en" else {name: name for name in SKILLS}
        self.skill_combo = ttk.Combobox(skill_row, textvariable=self.skill_name,
                                        values=list(labels.values()), state="readonly", width=19,
                                        style="Pixel.TCombobox")
        self.skill_combo.pack(side="left")
        self._controls.append((self.skill_combo, "readonly"))
        self.skill_combo.bind("<<ComboboxSelected>>", lambda event: self._show_skill())
        self.current_skill_label = self._label(skill_row, "Atual: —", color="muted")
        self.current_skill_label.pack(side="left", padx=12, fill="x", expand=True)
        self._entry(skill_row, self.skill_value, 5).pack(side="left", padx=(0, 8))
        self._button(skill_row, "Aplicar nível", self._set_skill, width=12).pack(side="left")
        all_row = tk.Frame(skills, bg=COLORS["card"])
        all_row.pack(fill="x")
        self._label(all_row, "Definir todas de uma vez", color="muted").pack(
            side="left", fill="x", expand=True)
        self._entry(all_row, self.all_skill_value, 5).pack(side="left", padx=(0, 8))
        self._button(all_row, "Aplicar a todas", self._set_all_skills, width=12).pack(side="left")

        attributes = self._card(self.body, "Atributos", "INTELIGÊNCIA · NÍVEL 0–100")
        attribute_row = tk.Frame(attributes, bg=COLORS["card"])
        attribute_row.pack(fill="x")
        self.intelligence_label = self._label(
            attribute_row, "Inteligência atual: —", size=12, bold=True, color="green"
        )
        self.intelligence_label.pack(side="left", fill="x", expand=True)
        self._entry(attribute_row, self.intelligence_value, 5).pack(side="left", padx=(10, 8))
        self._button(
            attribute_row, "Definir inteligência", self._set_intelligence, width=16
        ).pack(side="left")

        world = self._card(self.body, "Tempo e bem-estar", "EFEITOS TEMPORÁRIOS")
        toggles = tk.Frame(world, bg=COLORS["card"])
        toggles.pack(fill="x", pady=(0, 11))
        for text, variable, name in (
            ("Necessidades não caem", self.needs_value, "needs"),
            ("Manter saúde cheia", self.health_value, "health"),
        ):
            toggle = tk.Checkbutton(
                toggles, text=self._tx(text), variable=variable,
                command=lambda n=name, v=variable: self._command(n, v.get()),
                bg=COLORS["card"], fg=COLORS["text"],
                selectcolor=COLORS["field"], activebackground=COLORS["card"],
                activeforeground=COLORS["green"], disabledforeground="#738797",
                font=("Segoe UI", 10), bd=0, highlightthickness=0,
                cursor="hand2", padx=0, pady=3,
            )
            toggle.pack(side="left", padx=(0, 24))
            self._controls.append((toggle, "normal"))
        clock_row = tk.Frame(world, bg=COLORS["card"])
        clock_row.pack(fill="x")
        self._label(clock_row, "Velocidade do relógio", color="muted").pack(side="left", padx=(0, 10))
        self.speed_combo = ttk.Combobox(
            clock_row, textvariable=self.speed_value, width=14,
            values=("1× — normal", "2×", "5×", "10×", "20×"),
            state="readonly", style="Pixel.TCombobox",
        )
        self.speed_combo.pack(side="left")
        self._controls.append((self.speed_combo, "readonly"))
        self.speed_combo.bind("<<ComboboxSelected>>", self._set_speed)
        self._button(clock_row, "Restaurar necessidades", lambda: self._command("refill")).pack(
            side="right", padx=(10, 0))
        self._label(world, "A velocidade escolhida é aplicada ao selecionar.", size=9,
                    color="muted").pack(fill="x", pady=(7, 0))

        games = self._card(self.body, 'Minigames e basquete', 'ACERTOS E ASSISTÊNCIA')
        for text, variable, name in (
            ('Acertos e assistência nos minigames', self.minigames_value, 'minigames'),
            ('Acertar arremessos de basquete (rua, partidas e lances livres)', self.basket_value, 'basket'),
        ):
            toggle = tk.Checkbutton(
                games, text=self._tx(text), variable=variable,
                command=lambda n=name, v=variable: self._command(n, v.get()),
                bg=COLORS['card'], fg=COLORS['text'], selectcolor=COLORS['card'],
                activebackground=COLORS['card'], activeforeground=COLORS['text'],
                font=('Segoe UI', 10), anchor='w',
            )
            toggle.pack(fill='x', pady=4)
            self._controls.append((toggle, 'normal' if self.minigames_supported else 'disabled'))
        game_note = ('Inicie a atividade normalmente. No basquete, mova e arremesse você mesmo.\n'
                     'Recursos experimentais; consulte a cobertura no LEIA-ME.'
                     if self.minigames_supported else
                     'Assistência de minigames e basquete desativada nesta atualização; os outros controles estão disponíveis.')
        self._label(games, game_note,
                    size=9, color='muted').pack(fill='x', pady=(5, 0))

        footer_text = (
            "Uso local, para um jogador. Dinheiro e habilidades permanecem ao salvar o jogo.\n"
            "Os efeitos começam desligados. Desconectar interrompe a manutenção e a aceleração.\n"
            "No jogo: Ctrl+Alt+F6 necessidades • F7 +10 mil • F8 habilidades 100\n"
            "Ctrl+Alt+F9 velocidade • F10 saúde."
        )
        footer_text += (" • F11 minigames • F12 basquete." if self.minigames_supported else
                        "\nF11/F12 e a assistência de minigames estão desativados nesta build.")
        self.footer = self._label(
            self.body,
            footer_text,
            size=9, color="muted", justify="left", wraplength=690,
        )
        self.footer.pack(fill="x", pady=(2, 0))

    def _resize(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self._body_window, width=event.width)
        wrap = max(400, event.width - 48)
        self.status_label.configure(wraplength=wrap)
        self.footer.configure(wraplength=wrap)

    def _mousewheel(self, event: tk.Event) -> None:
        # Do not change a numeric selection while scrolling the page.
        if isinstance(event.widget, ttk.Combobox):
            return
        bounds = self.canvas.bbox("all")
        if bounds and bounds[3] > self.canvas.winfo_height():
            self.canvas.yview_scroll(-int(event.delta / 120), "units")

    def _worker(self) -> None:
        while True:
            token, name, operation = self._jobs.get()
            try:
                result = operation()
                self._results.put((token, name, result, None))
            except Exception as error:
                self._results.put((token, name, None, error))
            finally:
                self._jobs.task_done()
            if name == "close":
                return

    def _submit(self, name: str, operation: Callable, message: str | None = None) -> None:
        if self._closing and name != "close":
            return
        self._next_id += 1
        self._pending[self._next_id] = name
        self._jobs.put((self._next_id, name, operation))
        if message:
            self._set_status(message)
        self._refresh_controls()

    def _drain_results(self) -> None:
        try:
            while True:
                token, name, result, error = self._results.get_nowait()
                self._pending.pop(token, None)
                if name == "close":
                    self.destroy()
                    return
                if self._closing:
                    continue
                if error is not None:
                    self._report_error(name, str(error) or type(error).__name__)
                else:
                    self._handle_result(name, result)
                self._refresh_controls()
        except queue.Empty:
            pass
        if self._closing and time.monotonic() >= self._close_deadline:
            self.destroy()
            return
        self.after(80, self._drain_results)

    def _handle_result(self, name: str, result: Any) -> None:
        if isinstance(result, dict):
            if result.get("error"):
                self._report_error(name, str(result["error"]))
                return
            if result.get("ok") is False or result.get("success") is False:
                self._report_error(name, str(result.get("status") or result.get("message") or
                                              "O jogo não aceitou a alteração."))
                return
            if "connected" in result:
                self._connected = bool(result["connected"])
            if "ready" in result:
                self._ready = bool(result["ready"])
            if not self._connected:
                self._ready = False
            self._state.update(result)
            self._show_values()
        if name == "disconnect":
            self._connected = False
            self._ready = False
            self._state = {}
            self._show_values()
            self._set_status("Desconectado. Os efeitos temporários foram desativados.", hold=3)
        elif name == "launch":
            self._set_status("Abertura solicitada à Steam. Carregue seu personagem e conecte o painel.", hold=5)
        elif name == "connect":
            message = result.get("status") if isinstance(result, dict) else None
            self._set_status(message or ("Conectado. Aguardando o personagem…" if self._connected
                                         else "Não foi possível conectar ao jogo."), hold=2)
        elif name.startswith("command:"):
            message = result.get("message") or result.get("status") if isinstance(result, dict) else None
            self._set_status(message or "Alteração aplicada.", hold=3)
            # Read back the game's actual values rather than assuming a command succeeded.
            if not self._pending:
                self._submit("snapshot", self.backend.snapshot)
        elif name == "snapshot":
            if time.monotonic() >= self._message_until and not self._action_busy():
                status = self._state.get("status")
                self._set_status(status or ("Conectado. Alterações disponíveis." if self._ready
                                            else "Aguardando o jogo e seu personagem…" if self._connected
                                            else "Abra To Pixelia, carregue seu personagem e conecte o painel."))
            self._last_error = ""

    def _report_error(self, name: str, message: str) -> None:
        if name in ("connect", "disconnect", "snapshot"):
            self._ready = False
        self._set_status(message, error=True, hold=5)
        self._last_error = message
        # Toggles must always reflect the last confirmed state after a rejected command.
        self._show_values()

    def _set_status(self, text: str, *, error: bool = False, hold: float = 0) -> None:
        self.status_label.configure(text=self._tx(str(text)), fg=COLORS["error"] if error else COLORS["muted"])
        self._message_until = time.monotonic() + hold

    def _number(self, value: Any) -> str:
        if value is None:
            return "—"
        try:
            numeric = float(value)
            if self.language == "en":
                if numeric.is_integer():
                    return f"{int(numeric):,}"
                return f"{numeric:,.1f}"
            if numeric.is_integer():
                return f"{int(numeric):,}".replace(",", ".")
            return f"{numeric:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")
        except (TypeError, ValueError, OverflowError):
            return str(value)

    def _show_values(self) -> None:
        self.money_label.configure(text=self._tx("Saldo: ") + self._number(self._state.get("money")))
        self._show_skill()
        attributes = self._state.get("attributes") or {}
        intelligence = attributes.get("intelligence") if isinstance(attributes, dict) else None
        self.intelligence_label.configure(
            text=self._tx("Inteligência atual: " + self._number(intelligence))
        )
        self.needs_value.set(bool(self._state.get("freezeNeeds", False)))
        self.health_value.set(bool(self._state.get("freezeHealth", False)))
        self.minigames_value.set(bool(self._state.get('autoMinigames', False)))
        self.basket_value.set(bool(self._state.get('autoBasket', False)))
        try:
            speed = float(self._state.get("speed", 1))
            self.speed_value.set("1× — normal" if speed == 1 else f"{speed:g}×")
        except (TypeError, ValueError):
            self.speed_value.set("1× — normal")

    def _show_skill(self) -> None:
        skills = self._state.get("skills") or {}
        identifier = SKILLS.get(self.skill_name.get())
        if identifier is None and self.language == "en":
            identifier = next((SKILLS[name] for name, label in SKILLS_EN.items()
                               if label == self.skill_name.get()), None)
        value = skills.get(identifier) if isinstance(skills, dict) else None
        self.current_skill_label.configure(text=self._tx("Atual: " + self._number(value)))

    def _action_busy(self) -> bool:
        return any(name != "snapshot" for name in self._pending.values())

    def _refresh_controls(self) -> None:
        enabled = self._ready and self._connected and not self._action_busy() and not self._closing
        for widget, normal in self._controls:
            widget.configure(state=normal if enabled else "disabled")
        idle = not self._action_busy() and not self._closing
        self.connect_button.configure(text=self._tx("Desconectar") if self._connected else self._tx("Conectar ao jogo"),
                                      state="normal" if idle else "disabled")
        self.launch_button.configure(state="normal" if idle else "disabled")
        if self._closing:
            badge, color = self._tx("ENCERRANDO"), "muted"
        elif self._action_busy():
            badge, color = self._tx("PROCESSANDO…"), "muted"
        elif self._ready:
            badge, color = self._tx("CONECTADO"), "green"
        elif self._connected:
            badge, color = self._tx("AGUARDANDO PERSONAGEM"), "muted"
        else:
            badge, color = self._tx("DESCONECTADO"), "muted"
        self.badge.configure(text=badge, fg=COLORS[color])

    def _poll_snapshot(self) -> None:
        if self._closing:
            return
        if not self._pending:
            self._submit("snapshot", self.backend.snapshot)
        self.after(1000, self._poll_snapshot)

    def _connect(self) -> None:
        if self._connected:
            self._submit("disconnect", self.backend.disconnect, "Desconectando e restaurando efeitos temporários…")
        else:
            self._submit("connect", self.backend.connect, "Conectando. Na primeira vez, será baixado um componente de 42 MB. Aguarde…")

    def _launch(self) -> None:
        self._submit("launch", self.backend.start_game, "Solicitando abertura de To Pixelia pela Steam…")

    def _integer(self, variable: tk.StringVar, label: str, minimum: int, maximum: int) -> int | None:
        try:
            value = int(variable.get().strip())
        except (TypeError, ValueError):
            self._set_status(f"{self._tx(label)}: digite um número inteiro entre {self._number(minimum)} e "
                             f"{self._number(maximum)}.", error=True, hold=6)
            return None
        if not minimum <= value <= maximum:
            self._set_status(f"{self._tx(label)}: use um valor entre {self._number(minimum)} e "
                             f"{self._number(maximum)}.", error=True, hold=6)
            return None
        return value

    def _command(self, name: str, value: Any = None) -> None:
        if not self._ready or not self._connected or self._action_busy() or self._closing:
            self._show_values()
            return
        self._submit("command:" + name, lambda: self.backend.command(name, value),
                     "Aplicando alteração ao personagem…")

    def _add_money(self) -> None:
        value = self._integer(self.money_amount, "Dinheiro", 1, 10_000_000)
        if value is not None:
            self._command("addmoney", value)

    def _set_skill(self) -> None:
        value = self._integer(self.skill_value, "Nível da habilidade", 0, 100)
        if value is not None:
            skill_id = SKILLS.get(self.skill_name.get())
            if skill_id is None and self.language == "en":
                skill_id = next(SKILLS[name] for name, label in SKILLS_EN.items()
                                if label == self.skill_name.get())
            self._command("skill", {"name": skill_id, "value": value})

    def _set_all_skills(self) -> None:
        value = self._integer(self.all_skill_value, "Nível das habilidades", 0, 100)
        if value is not None:
            self._command("allskills", value)

    def _set_intelligence(self) -> None:
        value = self._integer(self.intelligence_value, "Inteligência", 0, 100)
        if value is not None:
            self._command("attribute", {"name": "intelligence", "value": value})

    def _set_speed(self, event: tk.Event | None = None) -> None:
        self._command("speed", int(self.speed_value.get().split("×", 1)[0]))

    def _close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._close_deadline = time.monotonic() + 3.0
        self._submit("close", self.backend.disconnect,
                     "Encerrando e desativando efeitos temporários…")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
