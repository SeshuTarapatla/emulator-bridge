from importlib import resources
from pathlib import Path
from shutil import which

from cli_utils import wt_profile
from click import BadOptionUsage
from typer import Context, Option, Typer

from emulator_bridge.main import main

cli = Typer(name="emulator-bridge", help="Emulator Bridge CLI")


@cli.callback(invoke_without_command=True)
def emulator_bridge(
    ctx: Context,
    dev: bool = Option(False, "-d", "--dev", help="Run uvicorn in auto reload mode."),
):
    if ctx.invoked_subcommand is not None and dev:
        raise BadOptionUsage("--dev", "-d/--dev should be used only with base command.")
    if ctx.invoked_subcommand is None:
        main(dev)


@cli.command(
    name="install-profile",
    help="Install a windows terminal profile for Emulator Bridge",
)
def install_wt_profile():
    if not (exe_file := which("emulator-bridge")):
        raise FileNotFoundError("Failed to determine the path of emulator-bridge.exe")
    exe = Path(exe_file)
    icon = (
        icon
        if isinstance(
            (
                icon := resources.files("emulator_bridge.assets").joinpath(
                    "android-48.ico"
                )
            ),
            Path,
        )
        and icon.exists()
        else None
    )
    wt_profile.add(exe=exe, name="Emulator Bridge", icon=icon)


if __name__ == "__main__":
    cli()
