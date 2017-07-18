# -*- coding: utf-8 -*-
import click
from housekeeper.store import api as hk_api


class AnalysisImporter():

    def __init__(self, db, hk_manager):
        self.db = db
        self.hk_manager = hk_manager

    @staticmethod
    def convert(record):
        return {
            'pipeline': record.pipeline,
            'version': record.pipeline_version,
            'analyzed': record.analyzed_at,
            'primary': record.case.runs[0] == record,
            'family': record.case.family_id,
            'customer': record.case.customer,
        }

    def _get_family(self, data):
        """Get related family."""
        customer_obj = self.db.customer(data['customer'])
        family_obj = self.db.find_family(customer_obj, data['family'])
        return family_obj

    def status(self, data):
        family_obj = self._get_family(data)
        new_record = self.db.add_analysis(
            pipeline=data['pipeline'],
            version=data['version'],
            analyzed=data['analyzed'],
            primary=data['primary'],
        )
        new_record.family = family_obj
        return new_record

    def records(self):
        query = hk_api.runs()
        count = query.count()
        with click.progressbar(query, length=count, label='analyses') as progressbar:
            for record in progressbar:
                data = self.convert(record)
                family_obj = self._get_family(data)
                if not self.db.analysis(family_obj, data['analyzed']):
                    new_record = self.status(data)
                    self.db.add(new_record)
        self.db.commit()
