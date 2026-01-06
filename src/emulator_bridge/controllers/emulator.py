import asyncio
from shutil import which
from subprocess import DEVNULL, Popen
from typing import Literal

from adbutils import AdbDevice, adb
from pygetwindow import Win32Window, getWindowsWithTitle

from emulator_bridge.utils import log


class EmulatorNotFound(FileNotFoundError): ...


class Emulator:
    exe = which("emulator.exe")

    @staticmethod
    async def start():
        if Emulator.status() == (None, None):
            Popen(
                f"{Emulator.exe} -avd emulator -no-boot-anim -no-audio -gpu host -accel on -memory 4096 -cores 4 -netfast".split(),
                stdout=DEVNULL,
                stderr=DEVNULL,
            )
        while Emulator.status()[1] != "active":
            await asyncio.sleep(1)
        if win := Emulator.window():
            win.moveTo(-5, 0)
        while Emulator.status() != ("device", "active"):
            await asyncio.sleep(2)

    @staticmethod
    async def stop():
        emu, ui = Emulator.status()
        if emu == "device":
            for device in adb.device_list():
                if str(device.serial).startswith("emulator-"):
                    device.shell("reboot -p")
                else:
                    exc = EmulatorNotFound(
                        "Emulator is not found in adb devices to stop."
                    )
                    log.error(exc)
        elif ui == "active" and (win := Emulator.window()):
            win.close()
        while Emulator.status() != (None, None):
            await asyncio.sleep(2)

    @staticmethod
    def status() -> tuple[
        Literal[None, "offline", "booting", "device"], Literal[None, "active"]
    ]:
        emu, ui = None, None
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
        if Emulator.window():
            ui = "active"
        return emu, ui

    @staticmethod
    def window() -> Win32Window | None:
        if _win := getWindowsWithTitle("Android Emulator - emulator:"):
            return _win[0]
