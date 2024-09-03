import colorsys
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


def generate_pastel_palette(num_colors: int) -> list[str]:
    """
    Generate a well-spaced pastel color palette.

    Args:
    num_colors (int): The number of colors to generate.

    Returns:
    List[str]: A list of hex color codes.
    """
    palette: list[str] = []
    hue_step: float = 1.0 / num_colors

    for i in range(num_colors):
        hue: float = i * hue_step
        # Use fixed saturation and value for pastel colors
        saturation: float = 0.4  # Lower saturation for softer colors
        value: float = 0.95  # High value for brightness

        # Convert HSV to RGB
        rgb: tuple[float, float, float] = colorsys.hsv_to_rgb(hue, saturation, value)

        # Convert RGB to hex
        hex_color: str = "#{:02x}{:02x}{:02x}".format(
            int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        )

        palette.append(hex_color)

    return palette
