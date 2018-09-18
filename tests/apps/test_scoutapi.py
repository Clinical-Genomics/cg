# -*- coding: utf-8 -*-
import datetime as dt

from cg.apps import scoutapi


def test_get_processing_time_for_values(scout_api: scoutapi):
    # GIVEN panel does not exist in scout database

    # WHEN calling get_genes
    result = scout_api.get_genes(panel_id='dummypanel', version=None)

    # THEN
    assert result is None
