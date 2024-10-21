# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import functools
import json
import logging
import os
import textwrap
from dataclasses import dataclass
from typing import List

from pint import DimensionalityError
from supabase import Client, create_client
from supabase.client import ClientOptions

from faebryk.core.module import Module

# TODO: replace with API-specific data model
from faebryk.libs.picker.jlcpcb.jlcpcb import Component, MappingParameterDB
from faebryk.libs.picker.lcsc import LCSC_NoDataException, LCSC_PinmapException
from faebryk.libs.picker.picker import PickError
from faebryk.libs.util import try_or

logger = logging.getLogger(__name__)


class ApiError(Exception): ...


class ApiNotConfiguredError(ApiError): ...


def check_compatible_parameters(
    module: Module, component: Component, mapping: list[MappingParameterDB]
) -> bool:
    """
    Check if the parameters of a component are compatible with the module
    """
    # TODO: serialize the module and check compatibility in the backend

    params = component.get_params(mapping)
    param_matches = [
        try_or(
            lambda: p.is_subset_of(getattr(module, m.param_name)),
            default=False,
            catch=DimensionalityError,
        )
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

    return False


@dataclass(frozen=True, eq=True)
class FootprintCandidate:
    footprint: str
    pin_count: int


@dataclass(frozen=True, eq=True)
class BaseParams:
    footprint_candidates: List[FootprintCandidate]
    qty: int

    def __hash__(self):
        return hash(
            (
                json.dumps(self.footprint_candidates, default=lambda o: o.__dict__),
                self.qty,
            )
        )


@dataclass(frozen=True, eq=True)
class ResistorParams(BaseParams):
    resistances: List[float]

    def __hash__(self):
        return hash((super().__hash__(), json.dumps(self.resistances)))


@dataclass(frozen=True, eq=True)
class CapacitorParams(BaseParams):
    capacitances: List[float]

    def __hash__(self):
        return hash((super().__hash__(), json.dumps(self.capacitances)))


@dataclass(frozen=True, eq=True)
class InductorParams(BaseParams):
    inductances: List[float]

    def __hash__(self):
        return hash((super().__hash__(), json.dumps(self.inductances)))


@dataclass(frozen=True, eq=True)
class TVSParams(BaseParams):
    def __hash__(self):
        return super().__hash__()


@dataclass(frozen=True, eq=True)
class DiodeParams(BaseParams):
    max_currents: List[float]
    reverse_working_voltages: List[float]

    def __hash__(self):
        return hash(
            (
                super().__hash__(),
                json.dumps(self.max_currents),
                json.dumps(self.reverse_working_voltages),
            )
        )


@dataclass(frozen=True, eq=True)
class LEDParams(BaseParams):
    def __hash__(self):
        return super().__hash__()


@dataclass(frozen=True, eq=True)
class MOSFETParams(BaseParams):
    def __hash__(self):
        return super().__hash__()


@dataclass(frozen=True, eq=True)
class LDOParams(BaseParams):
    def __hash__(self):
        return super().__hash__()


@dataclass(frozen=True, eq=True)
class LCSCParams:
    lcsc: int


@dataclass(frozen=True, eq=True)
class ManufacturerPartParams:
    manufacturer_name: str
    mfr: str
    qty: int


class ApiClient:
    @dataclass
    class Config:
        # TODO: add defaults
        enable: bool = os.getenv("FBRK_PICKER", "").lower() == "api"
        api_url: str | None = os.getenv("FBRK_API_URL")
        api_key: str | None = os.getenv("FBRK_API_KEY")

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
                raise ApiNotConfiguredError("API URL and API key must be set")

    @functools.lru_cache(maxsize=None)
    def fetch_parts(self, method: str, params: BaseParams) -> list[Component]:
        if self._client is None:
            raise ApiNotConfiguredError("API client is not initialized")

        response = self._client.rpc(method, params.__dict__).execute()
        return [Component(**part) for part in response.data]

    def fetch_resistors(self, params: ResistorParams) -> list[Component]:
        return self.fetch_parts("find_resistors", params)

    def fetch_capacitors(self, params: CapacitorParams) -> list[Component]:
        return self.fetch_parts("find_capacitors", params)

    def fetch_inductors(self, params: InductorParams) -> list[Component]:
        return self.fetch_parts("find_inductors", params)

    def fetch_tvs(self, params: TVSParams) -> list[Component]:
        return self.fetch_parts("find_tvs", params)

    def fetch_diodes(self, params: DiodeParams) -> list[Component]:
        return self.fetch_parts("find_diodes", params)

    def fetch_leds(self, params: LEDParams) -> list[Component]:
        return self.fetch_parts("find_leds", params)

    def fetch_mosfets(self, params: MOSFETParams) -> list[Component]:
        return self.fetch_parts("find_mosfets", params)

    def fetch_ldos(self, params: LDOParams) -> list[Component]:
        return self.fetch_parts("find_ldos", params)
