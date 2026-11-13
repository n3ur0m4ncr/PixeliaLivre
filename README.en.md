# Pixelia Livre — Single-Player Panel for To Pixelia

[![Supported Version](https://img.shields.io/badge/To%20Pixelia-v1.1.28%20(build%2025632131)-9cddb9?style=flat-square)](#compatibility-and-limitations)
[![Platform](https://img.shields.io/badge/Windows-x86%20IL2CPP-233445?style=flat-square)](#compatibility-and-limitations)
[![Python](https://img.shields.io/badge/Python-3.12-304356?style=flat-square)](#run-from-source-or-build)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

Bilingual (**Português / English**) desktop control panel built with Python + Tkinter and **Frida (IL2CPP)** instrumentation for single-player *To Pixelia* (Steam, Windows).

> 📖 **Documentation (Portuguese / Technical Docs):**
> - [**Step-by-Step Guide (PT-BR)**](docs/GUIA-PASSO-A-PASSO.md)
> - [**VirusTotal False Positive & File Drop Explanation (PT-BR)**](docs/FALSO-POSITIVO-VIRUSTOTAL.md)
> - [**Internal Architecture & Mermaid Diagrams (PT-BR)**](docs/ARQUITETURA.md)
> - [**Validation Report & Game Hashes (PT-BR)**](docs/VALIDACAO.md)
> - [**Documentação Principal em Português**](README.md)

---

## Features & Current Status

| Feature | Status in v1.1.28 | Details |
| --- | --- | --- |
| **Money** | ✅ Available | Add `1` to `10,000,000` per click (capped at a `2,000,000,000` balance). |
| **16 Skills** | ✅ Available | Set a single skill or all 16 skills at once from `0` to `100` (panel range). |
| **Intelligence** | ✅ Available | Set `intelligence` from `0` to `100`. |
| **Needs never decrease** | ✅ Available | Keeps hunger, energy, hygiene, toilet, mood, and clothing hygiene at `100`. |
| **Refill needs** | ✅ Available | Refills all 6 needs once on demand. |
| **Keep health full** | ✅ Available | Keeps `health` at `100` during player updates. |
| **Clock speed** | ✅ Available | `1×`, `2×`, `5×`, `10×`, or `20×` — only multiplies ordinary 1-second ticks while respecting pauses and scene transitions. |
| **Bilingual UI (PT / EN)** | ✅ Available | Switch via **PT / EN** buttons at the top right while keeping connection and skill selection. |
| **Minigames & Basketball** | ⏸️ Disabled | Temporarily disabled for this build until native RVAs in `src/minigames.js` are revalidated. |

---

## Getting Started

1. Download the packaged release (`PixeliaLivre-v1.1.28-win64.zip`) from [**Releases**](../../releases).
2. Extract the **entire ZIP archive** into a folder (for example, `C:\Mods\PixeliaLivre\`).
   - Keep `_internal` next to `PixeliaLivre.exe`. You do **not** need Python or Cheat Engine installed.
3. Launch **To Pixelia through Steam** and load your character.
4. Open **`PixeliaLivre.exe`** and click **Connect to game**.
5. On the **first connection**, wait for the automatic download (~42 MB) of the official Frida component from PyPI. It is saved into `runtime/` and reused offline afterward.
6. Return to the game window to enable controls. Keep the panel open while temporary effects are active.

---

## In-Game Hotkeys

Hold **`Ctrl + Alt`** while *To Pixelia* is focused, then press:

| Key | Action |
| --- | --- |
| `F6` | Toggle **Needs do not decrease** |
| `F7` | Add **+10,000** money |
| `F8` | Set **all 16 skills to 100** |
| `F9` | Cycle clock speed: `1× → 2× → 5× → 10× → 20×` |
| `F10` | Toggle **Keep health full** |
| `F11` / `F12` | Disabled for this build (no effect) |

*(Some laptops also require holding **`Fn`**.)*

---

## VirusTotal False Positives & Runtime "File Drop" Explained

`PixeliaLivre.exe` may trigger heuristic detections on **VirusTotal** or Windows Defender (such as *Dropper*, *Downloader*, *Injector*, `Win32/Wacatac`, or *RiskWare*). Here is the exact technical cause:

1. **Runtime file drop (`src/bootstrap.py`):**
   - `src/build.py` excludes `frida` (`--exclude-module frida`) so the release ZIP stays compact (~12 MB).
   - On first connection, `bootstrap.py` downloads `frida-17.2.17-cp37-abi3-win_amd64.whl` from official PyPI (`pypi.org` / `files.pythonhosted.org`), verifies byte size and **SHA-256**, and **unpacks ("drops") `frida/_frida.pyd`** into `runtime/frida-17.2.17/`.
   - Automated sandboxes flag any unsigned `.exe` that fetches a binary over HTTPS and writes a native `.pyd`/DLL to disk as a **Dropper / Downloader**.
2. **Unsigned PyInstaller bootloader:** PyInstaller executables without a commercial Authenticode certificate commonly trigger generic ML heuristics.
3. **Process instrumentation & hotkeys:** `backend.py` uses `OpenProcess` to verify the game path, `frida` attaches to `To Pixelia.exe` to hook `GameAssembly.dll` (IL2CPP), and `agent.js` reads `GetAsyncKeyState` strictly when the game window is in the foreground.

### How to verify & avoid alerts
- **Fully open, unobfuscated source code** in [`src/`](src).
- **Strict guarantees in `src/bootstrap.py`:** HTTPS-only domain allowlist (`pypi.org`, `files.pythonhosted.org`), pinned version/filename, PyPI **SHA-256** verification, Zip Slip protection, and local audit record `runtime/frida-17.2.17/download.json`.
- **Run from source without `.exe`:** use `.\scripts\run-from-source.ps1` with official Python 3.12.
- **Pre-stage `runtime/` offline:** manually download `frida==17.2.17` wheel via `pip download` and extract `frida/` + `frida-17.2.17.dist-info/` into `runtime/frida-17.2.17/` so `PixeliaLivre.exe` makes zero network calls.

---

## Run from Source or Build

### Run directly with Python (Windows, Python 3.12+)
```powershell
git clone https://github.com/n3ur0m4ncr/PixeliaLivre.git
cd PixeliaLivre
.\scripts\run-from-source.ps1
```

### Build executable + release ZIP + SHA-256 checksums
```powershell
pip install -r requirements.txt
.\scripts\build.ps1
```

---

## Compatibility and Limitations

- **Supported build:** Steam App `1954160`, build **`25632131`** (*To Pixelia* **v1.1.28**, Windows x86, Unity `2020.1.13f1`, IL2CPP).
- **Strict hash check:** `backend.py` verifies SHA-256 hashes of `GameAssembly.dll` and `global-metadata.dat` before attaching. Steam updates require updating `src/compatibility.json`.
- **Testing scope:** the v1.1.28 package compiled cleanly and passed `--self-test` (Tkinter/Tcl startup and resource presence), and IL2CPP metadata was inspected for target classes/methods; **live in-game session behavior has not yet been tested in gameplay**.
- **Safety lease:** options start disabled. Disconnecting, closing the panel, or failing to poll for **5 seconds** automatically disables temporary effects. Money, skills, and Intelligence already applied are not reverted and may persist if the game saves.
- **Logs:** check `PixeliaLivre.log` next to the executable if an error occurs. Do not connect two panel instances to the same game.

---

## Credits & License

- **Author / Source credit:** `n3urom4nc3r` ([`@n3ur0m4ncr`](https://github.com/n3ur0m4ncr))
- **License:** [MIT License](LICENSE)
- Third-party runtime dependency: [Frida `17.2.17`](https://pypi.org/project/frida/17.2.17/). Bundled Python and PyInstaller licenses are included in [`licenses/`](licenses).
