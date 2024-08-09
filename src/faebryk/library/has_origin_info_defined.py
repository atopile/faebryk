# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


from faebryk.library.has_origin_info import has_origin_info


class has_origin_info_defined(has_origin_info.impl()):
    def __init__(self, origin_info: has_origin_info.OriginInfo) -> None:
        super().__init__()
        self.origin_info = origin_info

    def get_origin(self) -> has_origin_info.OriginInfo:
        return self.origin_info
