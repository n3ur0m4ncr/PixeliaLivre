# Project credit: n3urom4nc3r
from pathlib import Path
import sys
import PyInstaller.__main__
base=Path(__file__).resolve().parent
args=['--noconfirm','--onedir','--windowed','--name','PixeliaLivre','--distpath',str(base/'dist'),'--workpath',str(base/'build'),'--specpath',str(base),'--paths',str(base),'--add-data',str(base/'agent.js')+';.','--add-data',str(base/'compatibility.json')+';.','--add-binary',str(Path(sys.executable).parent/'python3.dll')+';.','--exclude-module','frida']
args+=['--add-data',str(base/'basketball.js')+';.','--add-data',str(base/'minigames.js')+';.','--add-data',str(base/'locales')+';locales']
for module in ['asyncio','typing_extensions','concurrent.futures','codecs','dataclasses','inspect']:args+=['--hidden-import',module]
args.append(str(base/'entry.py'))
PyInstaller.__main__.run(args)
