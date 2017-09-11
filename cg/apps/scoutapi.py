# -*- coding: utf-8 -*-
import logging
from typing import List

from pymongo import MongoClient
from scout.adapter.mongo import MongoAdapter
from scout.export.panel import export_panels as scout_export_panels
from scout.load import load_scout

LOG = logging.getLogger(__name__)


class ScoutAPI(MongoAdapter):

    """Interface to Scout."""

    def __init__(self, config):
        client = MongoClient(config['scout']['database'], serverSelectionTimeoutMS=20)
        super(ScoutAPI, self).__init__(client[config['scout']['database_name']])

    def upload(self, data: dict, threshold: int=5, force: bool=False):
        """Load analysis of a new family into Scout."""
        data['rank_score_threshold'] = threshold
        existing_case = self.case(institute_id=data['owner'], display_name=data['family_name'])
        if existing_case:
            if force or data['analysis_date'] > existing_case['analysis_date']:
                LOG.info(f"updating existing Scout case")
                load_scout(self, data, update=True)
            else:
                existing_date = existing_case['analysis_date'].date()
                LOG.warning(f"analysis of case already loaded: {existing_date}")
        else:
            LOG.debug("loading new Scout case")
            load_scout(self, data)

    def export_panels(self, panels: List[str]):
        """Pass through to export of a list of gene panels."""
        return scout_export_panels(self, panels)
