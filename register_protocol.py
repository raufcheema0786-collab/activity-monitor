import os
import sys
import winreg


def register():
    if getattr(sys, "frozen", False):
        # Packaged executable: sys.executable *is* the .exe, and it can be
        # invoked directly with the clicked link as its only argument.
        command = f'"{sys.executable}" "%1"'
    else:
        # Dev mode: sys.executable is the interpreter, so main.py has to be
        # passed explicitly, resolved relative to this file rather than
        # hardcoded, so it's correct no matter where the project lives.
        main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        command = f'"{sys.executable}" "{main_py}" "%1"'

    key_path = r"Software\Classes\employee-monitor"
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
    winreg.SetValue(key, "", winreg.REG_SZ, "URL:Employee Monitor Protocol")
    winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

    command_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\shell\open\command")
    winreg.SetValue(command_key, "", winreg.REG_SZ, command)


if __name__ == "__main__":
    register()
    print("employee-monitor:// protocol registered successfully.")
