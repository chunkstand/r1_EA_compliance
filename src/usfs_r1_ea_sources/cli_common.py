from __future__ import annotations

import json


def print_summary(summary: dict) -> None:
    print(json.dumps(summary, indent=2, sort_keys=True))


def normalized_timeout(value: float | None) -> float | None:
    if value is not None and value <= 0:
        return None
    return value
