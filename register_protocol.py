import winreg


def register():
    exe_path = __import__("sys").executable
    script_path = __file__.replace("register_protocol.py", "main.py")

    key_path = r"Software\Classes\employee-monitor"
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
    winreg.SetValue(key, "", winreg.REG_SZ, "URL:Employee Monitor Protocol")
    winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

    command_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\shell\open\command")
    command = f'"{exe_path}" "{script_path}" "%1"'
    winreg.SetValue(command_key, "", winreg.REG_SZ, command)

    print("employee-monitor:// protocol registered successfully.")


if __name__ == "__main__":
    register()
