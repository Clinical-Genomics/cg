from dataclasses import dataclass
from typing import Generic, TypeVar, cast
from unittest.mock import Mock, create_autospec

T = TypeVar("T")


@dataclass(frozen=True)
class TypedMock(Generic[T]):
    as_mock: Mock
    as_type: T


def create_typed_mock(klass: type[T], **kwargs) -> TypedMock[T]:
    """Create a mock with a given type as specification.

    Returns a TypedMock instance containing type-hinted references to the
    created mock as both the provided type and as a mock to help type
    checkers correctly infer the types as needed.

    Args:
        klass: The type to use as the mock specification.
        **kwargs: Additional keyword arguments to pass to the mock constructor.

    Returns:
        TypedMock[T]: A typed mock instance wrapping the created mock.

    Example:
        >>> mock_service = create_typed_mock(MyService, some_attribute=42)
        >>> mock_service.as_type.some_method()  # Type checker sees MyService
        >>> mock_service.as_mock.assert_called_once()  # Access mock methods
    """
    instance = create_autospec(klass, instance=True, **kwargs)
    return TypedMock(as_mock=instance, as_type=cast(T, instance))
