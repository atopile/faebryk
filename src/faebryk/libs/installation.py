import importlib
import subprocess
import sys
from types import ModuleType

from rich.prompt import Confirm


class InstallationError(Exception):
    """Raised when there's a problem installing a module."""


def offer_install(module_name, install_name=None, ex=None) -> ModuleType | None:
    """
    Offer to install a missing module using pip.
    """
    cmd = [sys.executable, "-m", "pip", "install", install_name or module_name]

    print(f"The module '{module_name}' is not installed.")

    if Confirm.ask(
        f"Do you want to run the install command [cyan mono]`{' '.join(cmd)}`[/]"
    ):
        try:
            # Attempt to install the module using pip
            subprocess.check_call(cmd)

        except subprocess.CalledProcessError:
            print(f"Failed to install {module_name}. Please install it manually.")
            raise ex or InstallationError(f"Failed to install {module_name}")

        print(f"Successfully installed {module_name}")
        return importlib.import_module(module_name)


def offer_missing_install(
    module_name: str, install_name: str = None
) -> ModuleType | None:
    """
    Offer to install a missing module using pip.
    """
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        return offer_install(module_name, install_name)

