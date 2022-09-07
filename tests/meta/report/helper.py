"""Report helper"""


def recursive_assert(data):
    """Dictionary recursive assert test"""

    for k, v in data.items():
        if isinstance(v, dict):
            recursive_assert(dict(v))
        if isinstance(v, list):
            for e in v:
                recursive_assert(dict(e))
        else:
            assert v or isinstance(v, (int, float, bool)), f"{k} value is missing"
