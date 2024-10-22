import os
import sys
from pathlib import Path

KICAD_VERSION = "8.0"

# footprint library paths
# ref: https://docs.kicad.org/8.0/en/kicad/kicad.html#config-file-location
match sys.platform:
    case "win32":
        appdata = os.getenv("APPDATA")
        if appdata is not None:
            GLOBAL_FP_LIB_PATH = (
                Path(appdata) / "kicad" / KICAD_VERSION / "fp-lib-table"
            )
        else:
            raise EnvironmentError("APPDATA environment variable not set")
        # TODO: verify on a windows machine
        GLOBAL_FP_DIR_PATH = Path(appdata) / "kicad" / KICAD_VERSION / "footprints"
    case "linux":
        GLOBAL_FP_LIB_PATH = (
            Path("~/.config/kicad").expanduser() / KICAD_VERSION / "fp-lib-table"
        )
        GLOBAL_FP_DIR_PATH = Path("/usr/share/kicad/footprints")
    case "darwin":
        GLOBAL_FP_LIB_PATH = (
            Path("~/Library/Preferences/kicad").expanduser()
            / KICAD_VERSION
            / "fp-lib-table"
        )
        GLOBAL_FP_DIR_PATH = Path(
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
        )
    case _:
        raise EnvironmentError(f"Unsupported platform: {sys.platform}")

if not GLOBAL_FP_LIB_PATH.exists():
    raise FileNotFoundError(f"Footprint library path not found: {GLOBAL_FP_LIB_PATH}")
if not GLOBAL_FP_DIR_PATH.exists():
    raise FileNotFoundError(f"Footprint directory path not found: {GLOBAL_FP_DIR_PATH}")
