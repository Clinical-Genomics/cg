# -*- coding: utf-8 -*-
import logging
from typing import List

from pymongo import MongoClient
from scout.adapter.mongo import MongoAdapter
from scout.export.panel import export_panels as scout_export_panels
from scout.load import load_scout
from scout.parse.case import parse_case_data

LOG = logging.getLogger(__name__)


class ScoutAPI(MongoAdapter):

    """Interface to Scout."""

    def __init__(self, config):
        client = MongoClient(config['scout']['database'], serverSelectionTimeoutMS=20)
        super(ScoutAPI, self).__init__(client[config['scout']['database_name']])

    def upload(self, data: dict, threshold: int=5, force: bool=False):
        """Load analysis of a new family into Scout."""
        data['rank_score_threshold'] = threshold
        config_data = parse_case_data(config=data)
        existing_case = self.case(institute_id=config_data['owner'],
                                  display_name=config_data['family_name'])
        if existing_case:
            if force or config_data['analysis_date'] > existing_case['analysis_date']:
                LOG.info(f"update existing Scout case")
                load_scout(self, config_data, update=True)
            else:
                existing_date = existing_case['analysis_date'].date()
                LOG.warning(f"analysis of case already loaded: {existing_date}")
        else:
            LOG.debug("load new Scout case")
            load_scout(self, config_data)

    def export_panels(self, panels: List[str]):
        """Pass through to export of a list of gene panels."""
        return scout_export_panels(self, panels)

    def get_gene_panels(self, panel_name, version):
        """ retrieve scout panel objects """
        return gene_panel(self, panel_name, version )
