# -*- coding: utf-8 -*-
import click
import pymongo


class PanelImporter():

    def __init__(self, db, scout):
        self.db = db
        self.scout = scout

    @staticmethod
    def convert(record):
        return {
            'name': record['display_name'],
            'abbrev': record['panel_name'],
            'customer': record['institute'],
            'version': record['version'],
            'date': record['date'],
            'genes': len(record['genes']),
        }

    def status(self, data):
        customer_obj = self.db.customer(data['customer'])
        new_record = self.db.add_panel(
            name=data['name'],
            abbrev=data['abbrev'],
            version=data['version'],
            date=data['date'],
            genes=data['genes'],
        )
        new_record.customer = customer_obj
        return new_record

    def records(self):
        panel_names = self.scout.panel_collection.find().distinct('panel_name')
        count = len(panel_names)
        with click.progressbar(panel_names, length=count, label='panels') as progressbar:
            for panel_name in progressbar:
                scout_record = (self.scout.panel_collection
                                          .find({'panel_name': panel_name})
                                          .sort('version', pymongo.DESCENDING)[0])
                data = self.convert(scout_record)
                if self.db.panel(data['abbrev']) is None:
                    new_record = self.status(data)
                    self.db.add(new_record)
        self.db.commit()
