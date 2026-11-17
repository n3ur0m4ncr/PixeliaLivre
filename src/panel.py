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
from i18n import I18n


SKILL_IDS = (
    "computer", "writing", "cooking", "guitar", "piano", "painting",
    "drumming", "singing", "conversation", "modelling", "basketball",
    "comedy", "romance", "lockpicking", "driving", "farming",
)

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

    def __init__(self, backend: Backend | None = None, i18n: I18n | None = None) -> None:
        super().__init__()
        self.backend = backend if backend is not None else Backend()
        self.i18n = i18n if i18n is not None else I18n()
        self.minigames_supported = bool(self.backend.manifest.get("minigames_supported", True))
        self.basketball_supported = bool(self.backend.manifest.get("basketball_supported", self.minigames_supported))
        self.language_mode = "auto"
        self.language = self.i18n.detected_language

        self.title(self._tx("Pixelia Livre"))
        self.geometry("820x780")
        self.minsize(760, 640)
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
        self._status_raw = "Abra To Pixelia, carregue seu personagem e conecte o painel."
        self._status_is_error = False
        self._skill_id = SKILL_IDS[0]
        self._lang_map: dict[str, str] = {}

        self.money_amount = tk.StringVar(value="10000")
        self.language_choice = tk.StringVar()
        self.skill_name = tk.StringVar(value=self.i18n.skill_label(self._skill_id, self.language))
        self.skill_value = tk.StringVar(value="100")
        self.all_skill_value = tk.StringVar(value="100")
        self.intelligence_value = tk.StringVar(value="100")
        self.speed_value = tk.StringVar(value=self.i18n.pattern("speed_normal", self.language))
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
        return self.i18n.translate(text, self.language)

    def _language_options(self) -> tuple[list[str], str]:
        detected_name = self.i18n.display_name(self.i18n.detected_language)
        auto_label = self.i18n.pattern("auto_label", self.language, language=detected_name)
        if not auto_label:
            auto_label = f"Auto ({detected_name})"
        options = [auto_label]
        mapping = {auto_label: "auto"}
        selected_display = auto_label
        for code in self.i18n.available_codes():
            display = f"{self.i18n.display_name(code)} [{code}]"
            options.append(display)
            mapping[display] = code
            if self.language_mode == code:
                selected_display = display
        self._lang_map = mapping
        return options, selected_display

    def _on_language_select(self, event: tk.Event | None = None) -> None:
        target = self._lang_map.get(self.language_choice.get())
        if target:
            self._set_language(target)

    def _set_language(self, language: str) -> None:
        if language == "auto":
            mode, resolved = "auto", self.i18n.detected_language
        elif language in self.i18n.locales:
            mode, resolved = language, language
        else:
            return
        if mode == self.language_mode and resolved == self.language:
            return
        self.language_mode = mode
        self.language = resolved
        self.skill_name.set(self.i18n.skill_label(self._skill_id, self.language))
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
        self.badge = self._label(header, "DESCONECTADO", size=9, bold=True, color="muted")
        self.badge.pack(side="right", pady=(8, 0))
        lang_options, selected_lang = self._language_options()
        self.language_choice.set(selected_lang)
        self.language_combo = ttk.Combobox(
            header, textvariable=self.language_choice, values=lang_options,
            state="readonly", width=21, style="Pixel.TCombobox",
        )
        self.language_combo.pack(side="right", padx=(8, 12), pady=(4, 0))
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_select)
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
            self.body, self._status_raw,
            color="error" if self._status_is_error else "muted",
            justify="left", wraplength=730,
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
        skill_labels = [self.i18n.skill_label(sid, self.language) for sid in SKILL_IDS]
        self._skill_label_to_id = dict(zip(skill_labels, SKILL_IDS))
        self.skill_name.set(self.i18n.skill_label(self._skill_id, self.language))
        self.skill_combo = ttk.Combobox(skill_row, textvariable=self.skill_name,
                                        values=skill_labels, state="readonly", width=19,
                                        style="Pixel.TCombobox")
        self.skill_combo.pack(side="left")
        self._controls.append((self.skill_combo, "readonly"))
        self.skill_combo.bind("<<ComboboxSelected>>", lambda event: self._on_skill_select())
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
        normal_speed = self.i18n.pattern("speed_normal", self.language)
        self.speed_combo = ttk.Combobox(
            clock_row, textvariable=self.speed_value, width=14,
            values=(normal_speed, "2×", "5×", "10×", "20×"),
            state="readonly", style="Pixel.TCombobox",
        )
        self.speed_combo.pack(side="left")
        self._controls.append((self.speed_combo, "readonly"))
        self.speed_combo.bind("<<ComboboxSelected>>", self._set_speed)
        self._button(clock_row, "Restaurar necessidades", lambda: self._command("refill")).pack(
            side="right", padx=(10, 0))
        self._label(world, "A velocidade escolhida é aplicada ao selecionar.", size=9,
                    color="muted").pack(fill="x", pady=(7, 0))

        games = self._card(self.body, "Minigames e basquete", "ACERTOS E ASSISTÊNCIA")
        for text, variable, name, supported in (
            ("Acertos e assistência nos minigames", self.minigames_value, "minigames", self.minigames_supported),
            ("Acertar arremessos de basquete (rua, partidas e lances livres)", self.basket_value, "basket", self.basketball_supported),
        ):
            toggle = tk.Checkbutton(
                games, text=self._tx(text), variable=variable,
                command=lambda n=name, v=variable: self._command(n, v.get()),
                bg=COLORS["card"], fg=COLORS["text"], selectcolor=COLORS["field"],
                activebackground=COLORS["card"], activeforeground=COLORS["green"],
                disabledforeground="#738797", bd=0, highlightthickness=0,
                cursor="hand2", font=("Segoe UI", 10), anchor="w",
            )
            toggle.pack(fill="x", pady=4)
            self._controls.append((toggle, "normal" if supported else "disabled"))
        if self.minigames_supported and self.basketball_supported:
            game_note = (
                "Inicie a atividade normalmente. No basquete, mova e arremesse você mesmo.\n"
                "Recursos experimentais; consulte a cobertura no LEIA-ME."
            )
        elif self.basketball_supported:
            game_note = (
                "Basquete ativo (mova e arremesse você mesmo; válido para rua, partidas e lances livres).\n"
                "Demais minigames continuam desativados nesta build."
            )
        else:
            game_note = "Assistência de minigames e basquete desativada nesta atualização; os outros controles estão disponíveis."
        self._label(games, game_note, size=9, color="muted", justify="left").pack(fill="x", pady=(5, 0))

        footer_text = (
            "Uso local, para um jogador. Dinheiro e habilidades permanecem ao salvar o jogo.\n"
            "Os efeitos começam desligados. Desconectar interrompe a manutenção e a aceleração.\n"
            "No jogo: Ctrl+Alt+F6 necessidades • F7 +10 mil • F8 habilidades 100\n"
            "Ctrl+Alt+F9 velocidade • F10 saúde"
        )
        if self.minigames_supported and self.basketball_supported:
            footer_text += ". • F11 minigames • F12 basquete."
        elif self.basketball_supported:
            footer_text += " • F12 basquete.\nF11 e a assistência geral de minigames estão desativados nesta build."
        else:
            footer_text += ".\nF11/F12 e a assistência de minigames estão desativados nesta build."
        self.footer = self._label(
            self.body, footer_text, size=9, color="muted", justify="left", wraplength=730,
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
        self._status_raw = str(text)
        self._status_is_error = error
        self.status_label.configure(text=self._tx(self._status_raw), fg=COLORS["error"] if error else COLORS["muted"])
        self._message_until = time.monotonic() + hold

    def _number(self, value: Any) -> str:
        return self.i18n.format_number(value, self.language)

    def _show_values(self) -> None:
        self.money_label.configure(text=self._tx("Saldo: " + self._number(self._state.get("money"))))
        self._show_skill()
        attributes = self._state.get("attributes") or {}
        intelligence = attributes.get("intelligence") if isinstance(attributes, dict) else None
        self.intelligence_label.configure(
            text=self._tx("Inteligência atual: " + self._number(intelligence))
        )
        self.needs_value.set(bool(self._state.get("freezeNeeds", False)))
        self.health_value.set(bool(self._state.get("freezeHealth", False)))
        self.minigames_value.set(bool(self._state.get("autoMinigames", False)))
        self.basket_value.set(bool(self._state.get("autoBasket", False)))
        normal_speed = self.i18n.pattern("speed_normal", self.language)
        try:
            speed = float(self._state.get("speed", 1))
            self.speed_value.set(normal_speed if speed == 1 else f"{speed:g}×")
        except (TypeError, ValueError):
            self.speed_value.set(normal_speed)

    def _on_skill_select(self) -> None:
        self._skill_id = self._skill_label_to_id.get(self.skill_name.get(), self._skill_id)
        self._show_skill()

    def _show_skill(self) -> None:
        skills = self._state.get("skills") or {}
        value = skills.get(self._skill_id) if isinstance(skills, dict) else None
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
            self._set_status(
                f"{label}: digite um número inteiro entre {self._number(minimum)} e {self._number(maximum)}.",
                error=True, hold=6,
            )
            return None
        if not minimum <= value <= maximum:
            self._set_status(
                f"{label}: use um valor entre {self._number(minimum)} e {self._number(maximum)}.",
                error=True, hold=6,
            )
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
            skill_id = self._skill_label_to_id.get(self.skill_name.get(), self._skill_id)
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
