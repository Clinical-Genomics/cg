# -*- coding: utf-8 -*-
import logging
from typing import List

from pymongo import MongoClient
from scout.adapter.mongo import MongoAdapter
from scout.export.panel import export_panels as scout_export_panels
from scout.load import load_scout

log = logging.getLogger(__name__)


class ScoutAPI(MongoAdapter):

    def __init__(self, config):
        client = MongoClient(config['scout']['database'], serverSelectionTimeoutMS=20)
        super(ScoutAPI, self).__init__(client[config['scout']['database_name']])

    def upload(self, data: dict, threshold: int=5, force: bool=False):
        """Load analysis of a new family into Scout."""
        data['rank_score_threshold'] = threshold
        existing_case = self.case(institute_id=data['owner'], display_name=data['family'])
        if existing_case:
            if force or data['analysis_date'] > existing_case['analysis_date']:
                log.info(f"updating existing Scout case")
                load_scout(self, data, update=True)
            else:
                existing_date = existing_case['analysis_date'].date()
                log.warning(f"analysis of case already loaded: {existing_date}")
        else:
            log.debug("loading new Scout case")
            load_scout(self, data)

    def export_panels(self, panels: List[str]):
        return scout_export_panels(self, panels)
