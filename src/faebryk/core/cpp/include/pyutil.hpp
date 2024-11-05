/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <nanobind/nanobind.h>

namespace nb = nanobind;

namespace pyutil {

inline bool isinstance(nb::object obj, nb::type_object type) {
    // Call the Python isinstance function
    nb::object isinstance_func = nb::module_::import_("builtins").attr("isinstance");
    return bool(isinstance_func(obj, type));
}

} // namespace pyutil
