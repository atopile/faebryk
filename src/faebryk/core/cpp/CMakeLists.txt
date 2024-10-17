cmake_minimum_required(VERSION 3.4...3.18)
project(faebryk_core_cpp)

# Specify the Python version you're using
set(PYBIND11_PYTHON_VERSION 3.12)

set(CMAKE_CXX_STANDARD 20)
message(STATUS "C++ version: ${CMAKE_CXX_COMPILER_VERSION}")

# turn on optimization
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2")

# TODO remove
# enable debug symbols
set(CMAKE_BUILD_TYPE Debug)

add_subdirectory(pybind11)

include_directories(${CMAKE_SOURCE_DIR}/include)

pybind11_add_module(faebryk_core_cpp src/main.cpp)
