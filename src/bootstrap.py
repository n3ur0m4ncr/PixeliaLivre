"""Install the pinned official Frida wheel locally on first use; no system changes."""
# Project credit: n3urom4nc3r
from __future__ import annotations
import hashlib
import importlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
import urllib.request
from urllib.parse import urlparse
import zipfile

VERSION = '17.2.17'
FILENAME = 'frida-17.2.17-cp37-abi3-win_amd64.whl'
MAX_DOWNLOAD = 80 * 1024 * 1024

def runtime_dir():
    app_dir = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    return app_dir / 'runtime' / ('frida-' + VERSION)

def _open(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in {'pypi.org', 'files.pythonhosted.org'}:
        raise RuntimeError('Origem de download não autorizada.')
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'PixeliaLivre/1.0'}), timeout=30)

def _install(destination):
    with _open('https://pypi.org/pypi/frida/' + VERSION + '/json') as response:
        raw = response.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise RuntimeError('Resposta inesperada do PyPI.')
    metadata = json.loads(raw)
    package = next((x for x in metadata['urls'] if x['filename'] == FILENAME), None)
    if package is None or package.get('size', 0) > MAX_DOWNLOAD:
        raise RuntimeError('O componente compatível não está disponível no PyPI.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='download-', dir=destination.parent) as temporary:
        temporary = Path(temporary)
        wheel = temporary / FILENAME
        digest = hashlib.sha256()
        size = 0
        with _open(package['url']) as response, wheel.open('wb') as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_DOWNLOAD:
                    raise RuntimeError('O download excedeu o tamanho esperado.')
                digest.update(chunk)
                output.write(chunk)
        if size != package['size'] or digest.hexdigest() != package['digests']['sha256']:
            raise RuntimeError('Falha na verificação do download. Tente novamente.')
        staging = temporary / 'unpacked'
        staging.mkdir()
        with zipfile.ZipFile(wheel) as archive:
            for item in archive.infolist():
                parts = PurePosixPath(item.filename).parts
                if not parts or '..' in parts or any(':' in x or '\\' in x for x in parts):
                    raise RuntimeError('Caminho inválido no pacote.')
                if parts[0] not in {'frida', 'frida-' + VERSION + '.dist-info'}:
                    continue
                target = staging.joinpath(*parts)
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(item) as source, target.open('wb') as output:
                        shutil.copyfileobj(source, output)
        if not (staging / 'frida' / '__init__.py').is_file() or not (staging / 'frida' / '_frida.pyd').is_file():
            raise RuntimeError('Pacote incompleto.')
        (staging / 'download.json').write_text(json.dumps({'version':VERSION,'sha256':digest.hexdigest(),'source':package['url']}), encoding='utf8')
        if destination.exists():
            raise RuntimeError('Já existe um componente incompleto na pasta runtime. Renomeie essa pasta e tente novamente.')
        staging.rename(destination)

def ensure_frida():
    destination = runtime_dir()
    try:
        if not (destination / 'frida' / '__init__.py').is_file():
            _install(destination)
        if str(destination) not in sys.path:
            sys.path.insert(0, str(destination))
        importlib.invalidate_caches()
        module = importlib.import_module('frida')
        if module.__version__ != VERSION or not hasattr(module, 'get_local_device'):
            raise RuntimeError('Componente incompatível ou incompleto.')
        return module
    except Exception as error:
        raise RuntimeError('Não foi possível preparar a conexão. A primeira abertura precisa de internet para baixar 42 MB do PyPI. Detalhes: ' + str(error)) from error
