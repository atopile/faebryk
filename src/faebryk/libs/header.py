# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


import black


def get_header():
    return (
        "# This file is part of the faebryk project\n"
        "# SPDX-License-Identifier: MIT\n"
    )


def formatted_file_contents(file_contents: str) -> str:
    return black.format_str(file_contents, mode=black.Mode())
