# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


import logging

import pytest

from faebryk.libs.logging import setup_basic_logging


# TODO does not work
@pytest.fixture(scope="package", autouse=True)
def setup_logging():
    setup_basic_logging()
    logging.info("Setup logging")
    yield
