from typing import Any


class DictContaining:
    """Argument matcher, like `ANY`, that equals any dict containing the given key-value pairs.

    Extra keys in the compared dict are ignored.

    Example:
        mock.assert_called_once_with(file_path=ANY, content=DictContaining({"key": "value"}))
    """

    def __init__(self, expected: dict[str, Any] | None = None, **kwargs: Any):
        self.expected: dict[str, Any] = {**(expected or {}), **kwargs}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, dict):
            return False
        return all(key in other and other[key] == value for key, value in self.expected.items())

    def __repr__(self) -> str:
        return f"DictContaining({self.expected!r})"


class DictNotContaining:
    """Argument matcher, like `ANY`, that equals any dict containing none of the given key-value pairs.

    A key may be present as long as its value differs from the given one. When several pairs are
    given, none of them may be present.

    Example:
        mock.assert_called_once_with(file_path=ANY, content=DictNotContaining({"key": "value"}))
    """

    def __init__(self, unexpected: dict[str, Any] | None = None, **kwargs: Any):
        self.unexpected: dict[str, Any] = {**(unexpected or {}), **kwargs}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, dict):
            return False
        return not any(
            key in other and other[key] == value for key, value in self.unexpected.items()
        )

    def __repr__(self) -> str:
        return f"DictNotContaining({self.unexpected!r})"
