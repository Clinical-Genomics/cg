# -*- coding: utf-8 -*-
import click


class VersionImporter():

    def __init__(self, db, admin):
        self.db = db
        self.admin = admin

    @staticmethod
    def convert(record):
        return {
            'application': record.apptag.name,
            'version': record.version,
            'valid': record.valid_from,
            'prices': {
                'standard': record.price_standard,
                'priority': record.price_priority,
                'express': record.price_express,
                'research': record.price_research,
            },
            'comment': record.comment,
            'updated_at': record.last_updated,
        }

    def status(self, data):
        application_obj = self.db.application(data['application'])
        new_record = self.db.add_version(
            version=data['version'],
            valid=data['valid'],
            prices=data['prices'],
            comment=data['comment'],
        )
        new_record.application = application_obj
        new_record.updated_at = data['updated_at'] if data['updated_at'] else new_record.updated_at
        return new_record

    def records(self):
        query = self.admin.ApplicationTagVersion
        count = query.count()
        with click.progressbar(query, length=count, label='versions') as progressbar:
            for admin_record in progressbar:
                data = self.convert(admin_record)
                application_obj = self.db.application(data['application'])
                if not self.db.application_version(application_obj, data['version']):
                    new_record = self.status(data)
                    self.db.add(new_record)
        self.db.commit()
