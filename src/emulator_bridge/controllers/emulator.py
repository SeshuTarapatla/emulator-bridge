import asyncio
from shutil import which
from subprocess import DEVNULL, Popen
from typing import Literal

from adbutils import AdbDevice, AdbError, adb
from psutil import NoSuchProcess, Process
from pygetwindow import Win32Window, getWindowsWithTitle


class EmulatorNotFound(FileNotFoundError): ...


class Emulator:
    exe = which("emulator.exe")

    @staticmethod
    def start() -> int:
        return Popen(
            f"{Emulator.exe} -avd emulator -no-snapshot -no-boot-anim -no-audio -gpu host -accel on -memory 4096 -cores 4 -netfast".split(),
            stdout=DEVNULL,
            stderr=DEVNULL,
        ).pid

    @staticmethod
    async def stop(pid: int):
        try:
            if pid == 0:
                return
            parent = Process(pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            await asyncio.sleep(2)
        except NoSuchProcess:
            return

    @staticmethod
    def status() -> tuple[
        Literal[None, "offline", "booting", "device"], Literal[None, "active"]
    ]:
        emu, ui = None, None
        try:
            for entry in adb.list():
                if entry.serial.startswith("emulator-"):
                    if entry.state == "offline":
                        emu = "offline"
                    else:
                        device = AdbDevice(adb, entry.serial)
                        emu = (
                            "device"
                            if device.getprop("sys.boot_completed").strip() == "1"
                            else "booting"
                        )
        except AdbError:
            pass
        if Emulator.window():
            ui = "active"
        return emu, ui

    @staticmethod
    def window() -> Win32Window | None:
        if _win := getWindowsWithTitle("Android Emulator - emulator:"):
            return _win[0]

    @staticmethod
    def adjust_window(x: int = -5, y: int = 0) -> bool:
        if win := Emulator.window():
            win.moveTo(x, y)
            return True
        return False
