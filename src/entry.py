"""Application entry point for Pixelia Livre."""
# Project credit: n3urom4nc3r
from pathlib import Path
import json
import os
import sys

def create_app():
    from panel import App
    import tkinter
    try:
        return App()
    except tkinter.TclError as error:
        if 'init.tcl' not in str(error):
            raise
        # Some restricted Windows environments cannot resolve Tcl scripts under Documents.
        # A matching local Tcl installation is a fallback; the bundled copy remains the default.
        candidates=[Path('C:/Python312/tcl')]
        for base in candidates:
            if (base/'tcl8.6/init.tcl').is_file() and (base/'tk8.6/tk.tcl').is_file():
                os.environ['TCL_LIBRARY']=str(base/'tcl8.6')
                os.environ['TK_LIBRARY']=str(base/'tk8.6')
                return App()
        raise

def main():
    if '--self-test' in sys.argv:
        from backend import BASE
        out=Path(sys.executable).resolve().parent/'self-test.json'
        try:
            app=create_app()
            app.withdraw()
            app.update_idletasks()
            result={'package_startup':'passed','tkinter':'passed','tcl_library':app.tk.eval('info library'),'resources':all((BASE/n).is_file() for n in ['agent.js','basketball.js','minigames.js','compatibility.json']),'initial_state':app.backend.snapshot(),'gameplay_tested':False}
            app.destroy()
        except Exception as error:
            result={'package_startup':'failed','error':str(error),'gameplay_tested':False}
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
        return
    create_app().mainloop()

if __name__=='__main__':
    main()
