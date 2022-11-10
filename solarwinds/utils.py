import re
from typing import Dict, Union


def parse_response(response) -> Union[Dict, None]:
    """Parse a response from SWIS"""
    if response is not None:
        result = response.get("results")
        if len(result) == 0:
            return None
        else:
            return result
    else:
        return None


def sanitize_swdata(swdata) -> str:
    for k, v in swdata.items():
        if isinstance(v, str):
            if re.match(r"^\d+$", v):
                swdata[k] = int(v)
    return swdata


def camel_to_snake(name: str) -> str:
    """https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case"""
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def print_dict(dct):
    return str(dct).replace("{", "").replace("}", "").replace("'", "")
