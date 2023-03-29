"""Tests for the BaseHandle class."""
from typing import Type

import pytest
from dataclasses import astuple

from alchy import Query, ModelBase

from cg.store.api.base import BaseHandler


@pytest.mark.parametrize("table", astuple(BaseHandler()))
def test__get_query(base_store, table: Type[ModelBase]):
    """Tests the _get_query function for all attributes of BaseHandler ie tables in the database."""
    assert isinstance(base_store._get_query(table=table), Query)
