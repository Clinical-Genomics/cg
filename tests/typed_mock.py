from dataclasses import dataclass
from typing import Generic, TypeVar, cast
from unittest.mock import Mock, create_autospec

T = TypeVar("T")


@dataclass(frozen=True)
class TypedMock(Generic[T]):
    as_mock: Mock
    as_type: T


def create_typed_mock(klass: type[T], **kwargs) -> TypedMock[T]:
    instance = create_autospec(klass, instance=True, **kwargs)
    return TypedMock(as_mock=instance, as_type=cast(T, instance))
