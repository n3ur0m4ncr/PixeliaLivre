"""Connection and packaging support for the Pixelia Livre single-player mod."""
# Project credit: n3urom4nc3r
from __future__ import annotations
import ctypes
from ctypes import wintypes
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import threading

from bootstrap import ensure_frida

frida = None

BASE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
LOG_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
try:
    logging.basicConfig(filename=LOG_DIR / 'PixeliaLivre.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s', encoding='utf8')
except OSError:
    logging.basicConfig(level=logging.INFO)

def process_path(pid: int) -> Path:
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        raise OSError('Não foi possível consultar o jogo. Abra o jogo e o painel com o mesmo usuário.')
    try:
        buf = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(buf))
        if not kernel.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        return Path(buf.value)
    finally:
        kernel.CloseHandle(handle)

def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

class Backend:
    def __init__(self):
        self.session = None
        self.script = None
        self.lock = threading.RLock()
        self.status = 'Abra o To Pixelia pela Steam e clique em Conectar.'
        self.agent_error = None
        self.manifest = json.loads((BASE / 'compatibility.json').read_text(encoding='utf8'))

    def _detached(self, expected_session, reason, crash=None):
        if self.session is not expected_session:
            return
        self.session = None
        self.script = None
        self.status = 'Jogo desconectado. Abra-o e conecte novamente.'
        logging.info('Disconnected: %s', reason)

    def _message(self, message, data):
        if message.get('type') == 'error':
            self.agent_error = message.get('description', 'Falha ao iniciar o mod.')
            logging.error('Agent: %s', message.get('stack', message))
        elif message.get('type') == 'send':
            logging.info('Agent: %s', message.get('payload'))

    def connect(self):
        global frida
        with self.lock:
            if frida is None:
                frida = ensure_frida()
            if self.script is not None:
                return self.snapshot()
            matches = [p for p in frida.get_local_device().enumerate_processes()
                       if p.name.lower() == 'to pixelia.exe']
            if not matches:
                raise RuntimeError('To Pixelia não está aberto. Abra o jogo pela Steam primeiro.')
            if len(matches) != 1:
                raise RuntimeError('Há mais de uma cópia de To Pixelia aberta. Deixe apenas uma.')
            executable = process_path(matches[0].pid)
            if executable.name.lower() != 'to pixelia.exe':
                raise RuntimeError('Processo incompatível.')
            game = executable.parent
            for relative, expected in self.manifest['sha256'].items():
                target = game / relative
                if not target.is_file() or sha256(target) != expected:
                    raise RuntimeError('A versão do jogo difere da versão preparada (Steam build '
                                       + str(self.manifest['steam_build'])
                                       + '). O mod precisa ser atualizado para essa versão.')
            session = frida.attach(matches[0].pid)
            self.session = session
            session.on('detached', lambda reason, crash=None: self._detached(session, reason, crash))
            try:
                self.agent_error = None
                mini_supported = bool(self.manifest.get('minigames_supported', True))
                basket_supported = bool(self.manifest.get('basketball_supported', mini_supported))
                source = ((BASE / 'agent.js').read_text(encoding='utf8')
                          .replace('__MINIGAMES_SUPPORTED__', 'true' if mini_supported else 'false')
                          .replace('__BASKETBALL_SUPPORTED__', 'true' if basket_supported else 'false'))
                if basket_supported:
                    source += '\n' + (BASE / 'basketball.js').read_text(encoding='utf8')
                if mini_supported:
                    source += '\n' + (BASE / 'minigames.js').read_text(encoding='utf8')
                script = session.create_script(source)
                script.on('message', self._message)
                self.script = script
                script.load()
                if self.agent_error:
                    raise RuntimeError(self.agent_error)
                result = script.exports_sync.snapshot()
                logging.info('Connected to supported game build %s', self.manifest['steam_build'])
                return result
            except Exception:
                self.script = None
                self.session = None
                session.detach()
                raise

    def snapshot(self):
        with self.lock:
            script = self.script
            if script is None:
                return {'connected': False, 'ready': False, 'status': self.status,
                        'skills': {}, 'freezeNeeds': False, 'freezeHealth': False, 'speed': 1}
            return script.exports_sync.snapshot()

    def command(self, name, value=None):
        with self.lock:
            script = self.script
            if script is None:
                raise RuntimeError('Conecte o painel ao jogo primeiro.')
            return script.exports_sync.command(name, value)

    def disconnect(self):
        with self.lock:
            script, session = self.script, self.session
            self.script = self.session = None
            try:
                if script is not None:
                    script.exports_sync.shutdown()
                    script.unload()
            except Exception:
                pass
            finally:
                if session is not None:
                    try:
                        session.detach()
                    except Exception:
                        pass
            self.status = 'Desconectado. Velocidade normal e manutenção das necessidades desativada.'

    def start_game(self):
        os.startfile('steam://rungameid/1954160')
