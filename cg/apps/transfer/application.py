# -*- coding: utf-8 -*-
import click


class ApplicationImporter():

    def __init__(self, db, admin):
        self.db = db
        self.admin = admin

    @staticmethod
    def convert(record):
        return {
            'tag': record.name,
            'category': {
                'Microbial': 'mic',
                'Panel': 'tga',
                'Whole exome': 'wes',
                'Whole genome': 'wgs',
            }.get(record.category),
            'created_at': record.created_at,
            'minimum_order': record.minimum_order,
            'sequencing_depth': record.sequencing_depth,
            'sample_amount': record.sample_amount,
            'sample_volume': record.sample_volume,
            'sample_concentration': record.sample_concentration,
            'priority_processing': record.priority_processing,
            'turnaround_time': record.turnaround_time,
            'updated_at': record.last_updated,
            'comment': record.comment,

            'description': record.versions[0].description if record.versions else 'MISSING',
            'is_accredited': record.versions[0].is_accredited if record.versions else False,
            'percent_kth': record.versions[0].percent_kth if record.versions else None,
            'limitations': record.versions[0].limitations if record.versions else None,
        }

    def status(self, data):
        record = self.db.Application(**data)
        return record

    def records(self):
        query = self.admin.ApplicationTag
        count = query.count()
        with click.progressbar(query, length=count, label='applications') as progressbar:
            for admin_record in progressbar:
                data = self.convert(admin_record)
                if not self.db.application(data['tag']):
                    new_record = self.status(data)
                    self.db.add(new_record)
        self.db.commit()
