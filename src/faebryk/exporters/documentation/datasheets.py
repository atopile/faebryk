# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from pathlib import Path

import requests

import faebryk.library._F as F
from faebryk.core.module import Module

logger = logging.getLogger(__name__)


def export_datasheets(
    app: Module,
    path: Path = Path("build/documentation/datasheets"),
    overwrite: bool = False,
):
    """
    Export all datasheets of all modules (that have a datasheet defined)
    of the given application.
    """
    # Create directories if they don't exist
    path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Exporting datasheets to: {path}")
    for m in app.get_children_modules(types=Module):
        if not m.has_trait(F.has_datasheet):
            continue
        url = m.get_trait(F.has_datasheet).get_datasheet()
        if url:
            filename = type(m).__name__ + ".pdf"
            file_path = path / filename
            if file_path.exists() and not overwrite:
                logger.info(
                    f"Datasheet for {m.get_full_name(types=False)} already exists, skipping download"  # noqa: E501
                )
                continue
            success = _download_datasheet(url, file_path)
            logger.info(
                f"Downloaded datasheet for {m.get_full_name(types=False)}: {'\033[92mOK\033[0m' if success else '\033[91mFAILED\033[0m'}"  # noqa: E501
            )


def _download_datasheet(url: str, path: Path) -> bool:
    """
    Download the datasheet of the given module and save it to the given path.
    """
    if not url.endswith(".pdf"):
        logger.warning(f"Datasheet URL {url} is probably not a PDF")
        return False
    if not url.startswith(("http://", "https://")):
        logger.warning(f"Datasheet URL {url} is probably not a valid URL")
        return False

    try:
        user_agent_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"  # noqa: E501
        }
        response = requests.get(url, headers=user_agent_headers)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to download datasheet from {url}: {e}")
        return False

    try:
        path.write_bytes(response.content)
    except Exception as e:
        logger.error(f"Failed to save datasheet to {path}: {e}")
        return False

    return True
