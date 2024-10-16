# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import pathlib
import subprocess
import sys

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

cpp_dir = pathlib.Path(__file__).parent
pybind11_dir = cpp_dir / "pybind11"
build_dir = cpp_dir / "build"

# check if pybind11 is available
if not pybind11_dir.exists():
    raise RuntimeError("pybind11 not found")

# recompile
# subprocess.run(["rm", "-rf", str(build_dir)], check=True)
subprocess.run(["cmake", "-S", str(cpp_dir), "-B", str(build_dir)], check=True)
subprocess.run(["cmake", "--build", str(build_dir)], check=True)

if not build_dir.exists():
    raise RuntimeError("build directory not found")

# Add the build directory to Python path
sys.path.append(str(cpp_dir / "build"))

import faebryk_core_cpp  # noqa: E402
