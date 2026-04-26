import sys
import ctypes
from gui import run_app

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )

if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
        sys.exit()

    run_app()
