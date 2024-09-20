# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
import unittest

from faebryk.core.core import Namespace
from faebryk.core.node import Node
from faebryk.libs.library import L

logger = logging.getLogger(__name__)


class TestBasicLibrary(unittest.TestCase):
    def test_load_library(self):
        import faebryk.library._F  # noqa: F401

    def test_symbol_types(self):
        import faebryk.library._F as F

        symbols = {
            k: v
            for k, v in vars(F).items()
            if not k.startswith("_")
            and (not isinstance(v, type) or not issubclass(v, (Node, Namespace)))
            # allow once wrappers for type generators
            and not getattr(v, "_is_once_wrapper", False)
        }
        self.assertFalse(symbols, f"Found unexpected symbols: {symbols}")

    def test_imports(self):
        import faebryk.library._F as F
        from faebryk.core.trait import Trait, TraitImpl

        # get all symbols in F
        symbols = {
            k: v
            for k, v in vars(F).items()
            if not k.startswith("_")
            and isinstance(v, type)
            and issubclass(v, Node)
            # check if constructor has no args & no varargs
            and (
                v.__init__.__code__.co_argcount == 1
                and not v.__init__.__code__.co_flags & 0x04
            )
            # no trait base
            and (not issubclass(v, Trait) or issubclass(v, TraitImpl))
        }
        import signal

        TIMEOUT = 5  # Set timeout to 5 seconds

        def timeout_handler(signum, frame):
            raise TimeoutError("Function call timed out")

        for k, v in symbols.items():
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(TIMEOUT)

            try:
                logger.info(f"TESTING {k} {'-' * 50}")
                v()
            except TimeoutError:
                self.fail(f"Execution of {k} timed out after {TIMEOUT} seconds")
            except L.AbstractclassError:
                pass
            except Exception as e:
                self.fail(f"Failed to instantiate {k}: {e}")
            finally:
                signal.alarm(0)  # Disable the alarm


if __name__ == "__main__":
    unittest.main()
