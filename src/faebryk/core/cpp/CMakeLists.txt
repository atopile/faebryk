cmake_minimum_required(VERSION 3.4...3.18)
project(faebryk_core_cpp)

# Specify the Python version you're using
set(PYBIND11_PYTHON_VERSION 3.12)

add_subdirectory(pybind11)

pybind11_add_module(faebryk_core_cpp src/main.cpp)
