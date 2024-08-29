# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import typer

from faebryk.libs.tools.typer import typer_callback


@dataclass
class CTX: ...


def get_ctx(ctx: typer.Context) -> "CTX":
    return ctx.obj


@typer_callback(None)
def main(ctx: typer.Context):
    """
    Can be called like this: > faebryk refactor
    """
    pass


@main.command()
def libtof(ctx: typer.Context, root: Path):
    file_paths = list(root.rglob("**/*.py"))
    print(f"Found {len(file_paths)} files in path.")

    detection_pattern = re.compile(r"^from faebryk.library.[^_]")

    refactor_files = [
        path
        for path in file_paths
        if not path.stem.startswith("_")
        and any(detection_pattern.match(line) for line in path.read_text().splitlines())
    ]

    print(f"Found {len(refactor_files)} files to refactor.")

    # TO match:
    # from faebryk.library.has_kicad_footprint import has_kicad_footprint
    # from faebryk.library.has_simple_value_representation import (
    #     has_simple_value_representation,
    # )

    pyname = r"[_a-zA-Z][_a-zA-Z0-9]*"
    import_pattern = re.compile(
        r"^from faebryk.library.([^_][^ ]*) import ("
        f"{pyname}$"
        "|"
        f"\\([\n ]*{pyname},[\n ]*\\)$"  # multiline import
        r")",
        re.MULTILINE,
    )

    def refactor_file(path: Path):
        text = path.read_text()
        import_symbols = [m[0] for m in import_pattern.findall(text)]
        text = import_pattern.subn("import faebryk.library._F as F", text, count=1)[0]
        text = import_pattern.sub("", text)

        for sym in import_symbols:
            if re.search(rf"from faebryk.library.{sym} import {sym} as", text):
                print(f"Warning: skipping {sym} in {path}")
                continue

            text = re.sub(rf"^\s*from faebryk.library.{sym} import {sym}$", "", text)
            text = re.sub(
                rf"^\s*from faebryk.library.{sym} import \(\n\s*{sym},\n\)$", "", text
            )
            text = re.sub(rf"(?<!F\.)\b{sym}\b", f"F.{sym}", text)

        # print(path, import_symbols)
        path.write_text(text)

    for path in refactor_files:
        refactor_file(path)

    # Run ruff
    subprocess.check_call(["ruff", "check", "--fix", root])


if __name__ == "__main__":
    main()
