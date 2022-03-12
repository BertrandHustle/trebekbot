import json


def string_is_json(input_string: str) -> bool:
    """
    checks whether any string is valid json
    :param input_string: string to check whether is valid json
    :return: bool
    """
    try:
        return bool(json.loads(input_string))
    except json.decoder.JSONDecodeError:
        return False
