# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


class has_datasheet_defined(has_datasheet.impl()):
    def __init__(self, datasheet: str) -> None:
        super().__init__()
        self.datasheet = datasheet

    def get_datasheet(self) -> str:
        return self.datasheet
