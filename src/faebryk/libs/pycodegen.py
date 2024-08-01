# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
import re
from typing import Callable, Iterable, TypeVar

logger = logging.getLogger(__name__)


def sanitize_name(raw):
    sanitized = raw
    # braces
    sanitized = sanitized.replace("(", "")
    sanitized = sanitized.replace(")", "")
    sanitized = sanitized.replace("[", "")
    sanitized = sanitized.replace("]", "")
    # seperators
    sanitized = sanitized.replace(".", "_")
    sanitized = sanitized.replace(",", "_")
    sanitized = sanitized.replace("/", "_")
    # special symbols
    sanitized = sanitized.replace("'", "")
    sanitized = sanitized.replace("*", "")
    sanitized = sanitized.replace("^", "p")
    sanitized = sanitized.replace("#", "h")
    sanitized = sanitized.replace("ϕ", "phase")
    sanitized = sanitized.replace("π", "pi")
    sanitized = sanitized.replace("&", "and")
    # inversion
    sanitized = sanitized.replace("~", "n")
    sanitized = sanitized.replace("{", "")
    sanitized = sanitized.replace("}", "")

    sanitized = sanitized.replace("->", "to")
    sanitized = sanitized.replace("<-", "from")
    # arithmetics
    sanitized = sanitized.replace(">", "gt")
    sanitized = sanitized.replace("<", "lt")
    sanitized = sanitized.replace("=", "eq")
    sanitized = sanitized.replace("+", "plus")
    sanitized = sanitized.replace("-", "minus")

    # rest
    def handle_unknown_invalid_symbold(match):
        logger.warning(
            "Replacing unknown invalid symbol {} in {} with _".format(
                match.group(0), raw
            )
        )
        return "_"

    sanitized = re.sub(r"[^a-zA-Z_0-9]", handle_unknown_invalid_symbold, sanitized)

    if re.match("^[a-zA-Z_]", sanitized) is None:
        sanitized = "_" + sanitized

    if re.match("^[a-zA-Z_]+[a-zA-Z_0-9]*$", sanitized) is not None:
        return sanitized

    to_escape = re.findall("[^a-zA-Z_0-9]", sanitized)
    if len(to_escape) > 0:
        return None, to_escape

    return sanitized


T = TypeVar("T")


def gen_repeated_block(func: Callable[[T], str], generator: Iterable[T]) -> str:
    lines = list(map(func, generator))

    if not lines:
        lines = ["pass"]

    return gen_block("\n".join(lines))


def gen_block(payload: str):
    return f"#__MARK_BLOCK_BEGIN\n{payload}\n#__MARK_BLOCK_END"


def fix_indent(text: str) -> str:
    from textwrap import dedent

    indent_stack = [""]

    out_lines = []
    for line in text.splitlines():
        if "#__MARK_BLOCK_BEGIN" in line:
            indent_stack.append(line.removesuffix("#__MARK_BLOCK_BEGIN"))
        elif "#__MARK_BLOCK_END" in line:
            indent_stack.pop()
        else:
            out_lines.append(indent_stack[-1] + line)

    return dedent("\n".join(out_lines))
