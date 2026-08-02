from __future__ import annotations

from importlib import metadata


DISTRIBUTION_NAME = "comptext-phone-agent"


def application_version() -> str:
    try:
        return metadata.version(DISTRIBUTION_NAME)
    except metadata.PackageNotFoundError:
        return "0+unknown"
