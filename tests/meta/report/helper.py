"""Report helper"""


def recursive_assert(data):
    """Dictionary recursive assert test."""

    for key, value in data.items():
        if isinstance(value, dict):
            recursive_assert(dict(value))
        if isinstance(value, list):
            for element in value:
                recursive_assert(dict(element))
        else:
            assert value or isinstance(value, (int, float, bool)), f"{key} field is missing"
