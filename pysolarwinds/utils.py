"""Miscellaneous utilities."""
from typing import Optional


def parse_response(response: list) -> Optional[dict]:
    """Parse a response from SWIS."""
    if response:
        result = response.get("results")
        if len(result) == 0:
            return None
        else:  # noqa: RET505
            return result
    else:
        return None
