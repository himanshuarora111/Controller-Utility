import os
import sys

APP_NAME = "ControllerUtility"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _require_windows():
    if os.name != "nt":
        raise RuntimeError("Startup toggle is implemented only for Windows.")


def get_launch_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'

    python_exe = sys.executable
    pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    if os.path.exists(pythonw):
        python_exe = pythonw

    app_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "app.py"))
    return f'"{python_exe}" "{app_py}"'


def is_startup_enabled() -> bool:
    _require_windows()
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable_startup() -> None:
    _require_windows()
    import winreg

    command = get_launch_command()
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)


def disable_startup() -> None:
    _require_windows()
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass
    except OSError:
        pass
