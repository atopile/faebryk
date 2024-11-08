/* This file is part of the faebryk project
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <cxxabi.h>
#include <memory>
#include <string>

namespace util {

template <typename T> std::string get_type_name(const T *obj) {
    int status;
    std::unique_ptr<char, void (*)(void *)> demangled_name(
        abi::__cxa_demangle(typeid(*obj).name(), nullptr, nullptr, &status), std::free);
    return demangled_name ? demangled_name.get() : "unknown type";
}

template <typename T> std::string get_type_name(const std::shared_ptr<T> &obj) {
    return get_type_name(obj.get());
}

// TODO not really used
template <typename T> inline std::string str_vec(const std::vector<T> &vec) {
    std::stringstream ss;
    ss << "[";
    for (size_t i = 0; i < vec.size(); ++i) {
        // if T is string just put it into stream directly
        if constexpr (std::is_same_v<T, std::string>) {
            ss << '"' << vec[i] << '"';
        } else {
            ss << vec[i].str();
        }
        if (i < vec.size() - 1) {
            ss << ", ";
        }
    }
    ss << "]";
    return ss.str();
}

} // namespace util
