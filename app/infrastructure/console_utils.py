import os
import platform

OS_NAME: str = platform.system()


def clear_console() -> None:
    if OS_NAME == "Windows":
        os.system("cls")
    else:
        os.system("clear")
