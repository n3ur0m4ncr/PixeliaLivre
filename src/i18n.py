"""Universal localization and Windows UI language detection for Pixelia Livre."""
# Project credit: n3urom4nc3r

from __future__ import annotations

import ctypes
import json
import locale
from pathlib import Path
import re
import sys
from typing import Any


BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent

DEFAULT_LOCALE = "en"

CHINESE_ALIASES = {
    "zh": "zh-Hans",
    "zh-cn": "zh-Hans",
    "zh-sg": "zh-Hans",
    "zh-hans": "zh-Hans",
    "zh-tw": "zh-Hant",
    "zh-hk": "zh-Hant",
    "zh-mo": "zh-Hant",
    "zh-hant": "zh-Hant",
}


def normalize_tag(tag: str) -> str:
    """Normalize a BCP-47 / POSIX locale tag (e.g. 'pt_BR.UTF-8' -> 'pt-br')."""
    cleaned = tag.strip().split(".", 1)[0].split("@", 1)[0]
    return cleaned.replace("_", "-").lower()


def detect_windows_tags() -> list[str]:
    """Return Windows UI language tags in user preference order."""
    tags: list[str] = []

    def add(tag: str | None) -> None:
        if not tag:
            return
        norm = normalize_tag(tag)
        if norm and norm not in tags:
            tags.append(norm)

    if sys.platform == "win32":
        try:
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            num = ctypes.c_uint32(0)
            cch = ctypes.c_uint32(0)
            # MUI_LANGUAGE_NAME = 0x8 returns ordered BCP-47 display language tags.
            kernel.GetUserPreferredUILanguages(0x8, ctypes.byref(num), None, ctypes.byref(cch))
            if cch.value > 0:
                buf = ctypes.create_unicode_buffer(cch.value)
                if kernel.GetUserPreferredUILanguages(0x8, ctypes.byref(num), buf, ctypes.byref(cch)):
                    for item in ctypes.wstring_at(buf, cch.value).split("\x00"):
                        add(item)
        except OSError:
            pass

        for fn_name in ("GetUserDefaultUILanguage", "GetSystemDefaultUILanguage"):
            try:
                lang_id = getattr(ctypes.windll.kernel32, fn_name)()
                add(locale.windows_locale.get(lang_id))
            except (AttributeError, OSError):
                pass

    try:
        loc, _ = locale.getlocale()
        add(loc)
    except ValueError:
        pass

    return tags


def _locale_dirs() -> list[Path]:
    dirs: list[Path] = []
    for candidate in (BASE_DIR / "locales", APP_DIR / "locales"):
        if candidate.is_dir() and candidate not in dirs:
            dirs.append(candidate)
    return dirs


class I18n:
    """Loads built-in and user-provided locale packs with English fallback."""

    def __init__(self, search_dirs: list[Path] | None = None) -> None:
        self.locales: dict[str, dict[str, Any]] = {}
        dirs = search_dirs if search_dirs is not None else _locale_dirs()
        for directory in dirs:
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.json")):
                if path.name.startswith("_"):
                    continue
                self._load_file(path)

        if DEFAULT_LOCALE not in self.locales:
            self.locales[DEFAULT_LOCALE] = {
                "meta": {"code": DEFAULT_LOCALE, "name": "English", "native_name": "English", "match_tags": ["en"]},
                "number_format": {"thousands": ",", "decimal": "."},
                "skills": {},
                "patterns": {},
                "strings": {},
            }

        self.detected_tags = detect_windows_tags()
        self.detected_language = self.match_tags(self.detected_tags)

    def _load_file(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, dict):
            return
        meta = data.get("meta")
        code = str(meta.get("code", path.stem) if isinstance(meta, dict) else path.stem).strip()
        if not code:
            return
        existing = self.locales.get(code, {})
        merged = {
            "meta": {**(existing.get("meta") or {}), **(meta if isinstance(meta, dict) else {}), "code": code},
            "number_format": {**(existing.get("number_format") or {}), **(data.get("number_format") or {})},
            "skills": {**(existing.get("skills") or {}), **(data.get("skills") or {})},
            "patterns": {**(existing.get("patterns") or {}), **(data.get("patterns") or {})},
            "strings": {**(existing.get("strings") or {}), **(data.get("strings") or {})},
        }
        self.locales[code] = merged

    def match_tags(self, tags: list[str]) -> str:
        """Resolve the best available locale code for a list of BCP-47 tags."""
        by_norm: dict[str, str] = {}
        for code, payload in self.locales.items():
            by_norm[normalize_tag(code)] = code
            for alias in (payload.get("meta") or {}).get("match_tags") or ():
                by_norm[normalize_tag(str(alias))] = code

        for raw in tags:
            norm = normalize_tag(raw)
            if not norm:
                continue
            if norm in by_norm:
                return by_norm[norm]
            if norm in CHINESE_ALIASES and CHINESE_ALIASES[norm] in self.locales:
                return CHINESE_ALIASES[norm]
            parts = norm.split("-")
            if len(parts) >= 2:
                prefix = f"{parts[0]}-{parts[1]}"
                if prefix in CHINESE_ALIASES and CHINESE_ALIASES[prefix] in self.locales:
                    return CHINESE_ALIASES[prefix]
                if prefix in by_norm:
                    return by_norm[prefix]
            if parts[0] in CHINESE_ALIASES and CHINESE_ALIASES[parts[0]] in self.locales:
                return CHINESE_ALIASES[parts[0]]
            if parts[0] in by_norm:
                return by_norm[parts[0]]

        return DEFAULT_LOCALE if DEFAULT_LOCALE in self.locales else next(iter(self.locales))

    def available_codes(self) -> list[str]:
        preferred = [c for c in ("pt", "en", "es", "fr", "de", "it", "pl", "ru", "tr", "ja", "ko", "zh-Hans", "zh-Hant") if c in self.locales]
        extras = sorted(c for c in self.locales if c not in preferred)
        return preferred + extras

    def display_name(self, code: str) -> str:
        meta = (self.locales.get(code) or {}).get("meta") or {}
        return str(meta.get("native_name") or meta.get("name") or code)

    def _entry(self, code: str) -> dict[str, Any]:
        return self.locales.get(code) or self.locales[DEFAULT_LOCALE]

    def pattern(self, key: str, code: str, **kwargs: Any) -> str:
        entry = self._entry(code)
        template = (entry.get("patterns") or {}).get(key)
        if template is None:
            template = (self._entry(DEFAULT_LOCALE).get("patterns") or {}).get(key, "")
        return str(template).format(**kwargs) if kwargs else str(template)

    def skill_label(self, skill_id: str, code: str) -> str:
        entry = self._entry(code)
        label = (entry.get("skills") or {}).get(skill_id)
        if label is None:
            label = (self._entry(DEFAULT_LOCALE).get("skills") or {}).get(skill_id)
        return str(label or skill_id)

    def format_number(self, value: Any, code: str) -> str:
        if value is None:
            return "—"
        try:
            numeric = float(value)
            fmt = (self._entry(code).get("number_format") or {})
            thousands = str(fmt.get("thousands", ","))
            decimal = str(fmt.get("decimal", "."))
            raw = f"{int(numeric):,}" if numeric.is_integer() else f"{numeric:,.1f}"
            return raw.replace(",", "\x00").replace(".", decimal).replace("\x00", thousands)
        except (TypeError, ValueError, OverflowError):
            return str(value)

    def translate(self, text: str, code: str) -> str:
        if not text:
            return text
        entry = self._entry(code)
        strings = entry.get("strings") or {}
        if text in strings:
            return str(strings[text])

        # Dynamic status / error messages from panel.py, backend.py, bootstrap.py, agent.js, basketball.js, minigames.js
        for prefix, pattern_key, arg_name in (
            ("Saldo: ", "balance_line", "value"),
            ("Atual: ", "skill_current_line", "value"),
            ("Inteligência atual: ", "intelligence_current_line", "value"),
            ("Mod pausado: ", "mod_paused", "details"),
            ("Classe ambígua: ", "ambiguous_class", "name"),
            ("Classe incompatível: ", "incompatible_class", "name"),
            ("Versão incompatível: campo ", "incompatible_field", "name"),
            ("Método incompatível: ", "incompatible_method", "name"),
            ("Verificação do basquete falhou: ", "basketball_check_failed", "name"),
            ("Verificação do minigame falhou: ", "minigame_check_failed", "name"),
            ("Minigame sem implementação: ", "minigame_unavailable", "name"),
            ("Evento de acerto incompatível: ", "hit_event_incompatible", "name"),
        ):
            if text.startswith(prefix):
                arg = text[len(prefix):]
                if pattern_key == "mod_paused":
                    arg = self.translate(arg, code)
                return self.pattern(pattern_key, code, **{arg_name: arg})

        if ": digite um número inteiro entre " in text:
            label, bounds = text.split(": digite um número inteiro entre ", 1)
            lo, hi = (bounds.rstrip(".").split(" e ", 1) + [""])[:2]
            return self.pattern("int_range_error", code, label=self.translate(label, code), min=lo, max=hi)

        if ": use um valor entre " in text:
            label, bounds = text.split(": use um valor entre ", 1)
            lo, hi = (bounds.rstrip(".").split(" e ", 1) + [""])[:2]
            return self.pattern("bounds_error", code, label=self.translate(label, code), min=lo, max=hi)

        m = re.match(
            r"^A versão do jogo difere da versão preparada \(Steam build (\d+)\)\. O mod precisa ser atualizado para essa versão\.$",
            text,
        )
        if m:
            return self.pattern("game_version_mismatch", code, build=m.group(1))

        prefix_boot = "Não foi possível preparar a conexão. A primeira abertura precisa de internet para baixar 42 MB do PyPI. Detalhes: "
        if text.startswith(prefix_boot):
            details = self.translate(text[len(prefix_boot):], code)
            return self.pattern("bootstrap_failed", code, details=details)

        if not (code == "pt" or code.startswith("pt-")):
            fallback_strings = self._entry(DEFAULT_LOCALE).get("strings") or {}
            if text in fallback_strings:
                return str(fallback_strings[text])

        return text
