# -*- coding: utf-8 -*-
import pytest

from cg.store import Store


@pytest.yield_fixture(scope='function')
def store() -> Store:
    _store = Store(uri='sqlite://')
    _store.create_all()
    yield _store
    _store.drop_all()
