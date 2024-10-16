# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
import os
import textwrap
from dataclasses import dataclass

from supabase import Client, create_client
from supabase.client import ClientOptions

import faebryk.library._F as F
from faebryk.core.core import Module

# TODO: replace with API-specific data model
from faebryk.libs.picker.jlcpcb.jlcpcb import Component, MappingParameterDB
from faebryk.libs.picker.lcsc import LCSC_NoDataException, LCSC_PinmapException
from faebryk.libs.picker.picker import PickError

logger = logging.getLogger(__name__)


class ApiError(Exception): ...


def get_footprint_candidates(module: Module) -> list[dict] | None:
    if module.has_trait(F.has_footprint_requirement):
        return [
            {"footprint": footprint, "pin_count": pin_count}
            for footprint, pin_count in module.get_trait(
                F.has_footprint_requirement
            ).get_footprint_requirement()
        ]
    return None


def check_compatible_parameters(
    module: Module, component: Component, mapping: list[MappingParameterDB]
) -> bool:
    """
    Check if the parameters of a component are compatible with the module
    """
    # TODO: serialize the module and check compatibility in the backend

    params = component.get_params(mapping)
    param_matches = [
        p.is_subset_of(getattr(module.PARAMs, m.param_name))
        for p, m in zip(params, mapping)
    ]

    if not (is_compatible := all(param_matches)):
        logger.debug(
            f"Component {component.lcsc} doesn't match: "
            f"{[p for p, v in zip(params, param_matches) if not v]}"
        )

    return is_compatible


def try_attach(
    cmp: Module, parts: list[Component], mapping: list[MappingParameterDB], qty: int
) -> bool:
    failures = []
    for part in parts:
        if not check_compatible_parameters(cmp, part, mapping):
            continue

        try:
            part.attach(cmp, mapping, qty, allow_TBD=False)
            return True
        except (ValueError, Component.ParseError) as e:
            failures.append((part, e))
        except LCSC_NoDataException as e:
            failures.append((part, e))
        except LCSC_PinmapException as e:
            failures.append((part, e))

    if failures:
        fail_str = textwrap.indent(
            "\n" + f"{'\n'.join(f'{c}: {e}' for c, e in failures)}", " " * 4
        )

        raise PickError(
            f"Failed to attach any components to module {cmp}: {len(failures)}"
            f" {fail_str}",
            cmp,
        )


class ApiClient:
    @dataclass
    class Config:
        # TODO: add defaults
        enable: str = os.getenv("FBRK_PICKER", "").lower() == "api"
        api_url: str = os.getenv("FBRK_API_URL")
        api_key: str = os.getenv("FBRK_API_KEY")

    config = Config()
    _client: Client | None = None

    def __init__(self):
        if self.config.enable:
            if self.config.api_url and self.config.api_key:
                self._client = create_client(
                    self.config.api_url,
                    self.config.api_key,
                    options=ClientOptions(
                        postgrest_client_timeout=10,
                        storage_client_timeout=10,
                        schema="public",
                    ),
                )
            else:
                raise ApiError("API URL and API key must be set")

    def fetch_parts(self, method: str, params: dict) -> list[Component]:
        response = self._client.rpc(method, params).execute()
        return [Component(**part) for part in response.data]
