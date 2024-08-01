import _ast
import ast
import inspect
import re
from pathlib import Path

import black
import typer


def main(file: Path):
    # get all classes that are subclasses of AST in _ast.pyi
    ast_clses = set(
        name
        for name, _ in inspect.getmembers(
            _ast, lambda x: inspect.isclass(x) and issubclass(x, ast.AST)
        )
    )

    # convert file to ast
    tree = ast.parse(file.read_text())
    out = ast.dump(tree)

    # use ast namespace
    out = f"import ast\n{out}"
    for name in ast_clses:
        out = out.replace(f"{name}(", f"ast.{name}(")

    out = black.format_str(out, mode=black.FileMode())
    # remove ctx=
    out = re.sub(r",[ \n\t]*ctx=ast.(Load|Store)\(\)", "", out)

    print(out)


if __name__ == "__main__":
    typer.run(main)
