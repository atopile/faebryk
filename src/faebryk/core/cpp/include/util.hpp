#pragma once

#include <pybind11/stl.h>
#include <sstream>
#include <string>

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