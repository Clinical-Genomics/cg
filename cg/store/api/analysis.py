# -*- coding: utf-8 -*-
import datetime as dt
import logging

from cg.apps import tb, hk
from cg.exc import AnalysisNotFinishedError
from cg.store import Store


class StoreHandler:
    """Methods related to storing data in the store."""

    def __init__(self, status: Store, hk_api: hk.HousekeeperAPI,
                 tb_api: tb.TrailblazerAPI,
                 logger=logging.getLogger(
                     __name__)):
        self.status = status
        self.tb_api = tb_api
        self.hk_api = hk_api
        self.LOG = logger

    def store_analysis(self, config_stream):
        new_analysis = self._gather_files_and_bundle_in_housekeeper(config_stream)
        self.status.add_commit(new_analysis)

    def _gather_files_and_bundle_in_housekeeper(self, config_stream
                                                ):
        try:
            bundle_data = self.tb_api.add_analysis(config_stream)
        except AnalysisNotFinishedError as error:
            self.LOG.error(error.message)
            raise Exception

        try:
            results = self.hk_api.add_bundle(bundle_data)
            if results is None:
                self.LOG.warning('analysis version already added')
                raise Exception
            bundle_obj, version_obj = results
        except FileNotFoundError as error:
            self.LOG.error(f"missing file: {error.args[0]}")
            raise Exception

        family_obj = self.status.family(bundle_obj.name)
        self._reset_action_from_running_on_family(family_obj)
        new_analysis = self._add_new_complete_analysis_record(bundle_data, family_obj,
                                                              version_obj)
        version_date = version_obj.created_at.date()
        self.LOG.info(f"new bundle added: {bundle_obj.name}, version {version_date}")
        self._include_files_in_housekeeper(bundle_obj, version_obj)

        return new_analysis

    def _include_files_in_housekeeper(self, bundle_obj, version_obj):
        try:
            self.hk_api.include(version_obj)
        except self.hk_api.VersionIncludedError as error:
            self.LOG.error(error.message)
            raise Exception
        self.hk_api.add_commit(bundle_obj, version_obj)

    def _add_new_complete_analysis_record(self, bundle_data, family_obj, version_obj):

        pipeline = family_obj.links[0].sample.data_analysis
        pipeline = pipeline if pipeline else 'mip'  # TODO remove this default from here

        new_analysis = self.status.add_analysis(
            pipeline=pipeline,
            version=bundle_data['pipeline_version'],
            started_at=bundle_data['created'],
            completed_at=dt.datetime.now(),
            primary=len(family_obj.analyses) == 0,
        )
        new_analysis.family = family_obj
        return new_analysis

    @staticmethod
    def _reset_action_from_running_on_family(family_obj):
        family_obj.action = None
