/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <nanobind/nanobind.h>

namespace nb = nanobind;

// Fix for nanobind new override
template <typename Func, typename Sig = nb::detail::function_signature_t<Func>>
struct new__;

template <typename Func, typename Return, typename... Args>
struct new__<Func, Return(Args...)> {
    std::remove_reference_t<Func> func;

    new__(Func &&f)
      : func((nb::detail::forward_t<Func>)f) {
    }

    template <typename Class, typename... Extra>
    NB_INLINE void execute(Class &cl, const Extra &...extra) {
        nb::detail::wrap_base_new(cl, sizeof...(Args) != 0);

        auto wrapper_cls = [func = (nb::detail::forward_t<Func>)func](nb::handle h,
                                                                      Args... args) {
            return func((nb::detail::forward_t<Args>)args...);
        };
        auto wrapper = [func = (nb::detail::forward_t<Func>)func](Args... args) {
            return func((nb::detail::forward_t<Args>)args...);
        };

        cl.def_static("__new__", std::move(wrapper_cls), nb::arg("cls"), extra...);
        cl.def_static("__new__", std::move(wrapper), extra...);
        cl.def(
            "__init__",
            [](nb::handle, Args...) {
            },
            extra...);
    }
};
template <typename Func> new__(Func &&f) -> new__<Func>;

#define FACTORY(pyclass, newc, ...)                                                     \
    {                                                                                   \
        auto _ = pyclass;                                                               \
        new__(newc).execute(_, ##__VA_ARGS__);                                          \
    }
