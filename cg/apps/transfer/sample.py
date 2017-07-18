# -*- coding: utf-8 -*-
import logging

import click

log = logging.getLogger(__name__)


class SampleImporter():

    def __init__(self, db, lims):
        self.db = db
        self.lims = lims

    def convert(self, sample):
        return {
            'internal_id': sample['id'],
            'order': sample['project']['name'],
            'name': sample['name'],
            'sex': sample['sex'],
            'customer': sample['customer'],
            'application': sample['application'],
            'application_version': sample['application_version'],
            'received_at': sample['received'],
            'link': {
                'father': sample['father'],
                'mother': sample['mother'],
                'status': sample['status'],
            },
            'family': {
                'name': sample['family'],
                'panels': sample['panels'],
                'priority': sample['priority'],
            }
        }

    def status(self, data):
        application_obj = self.db.application(data['application'])
        if application_obj is None:
            log.error(f"unknown application: {data['application']}")
            return
        version_no = data['application_version'] or 1
        version_obj = self.db.application_version(application_obj, version_no)
        if version_obj is None:
            log.error(f"unknown application version: {application_obj.tag} - {version_no}")
            return
        customer_obj = self.db.customer(data['customer'])
        family_obj = self.db.find_family(customer_obj, data['family']['name'])
        if family_obj is None:
            family_obj = self.db.add_family(
                name=data['family']['name'],
                priority=data['family']['priority'] or 'standard',
                panels=data['family']['panels'] or ['OMIM-AUTO']
            )
            family_obj.customer = customer_obj
        new_record = self.db.add_sample(
            name=data['name'],
            sex=data['sex'] or 'unknown',
            internal_id=data['internal_id'],
            received=data['received_at'],
            order=data['order'],
        )
        new_record.customer = customer_obj
        new_record.application_version = version_obj
        link_obj = self.db.relate_sample(
            family=family_obj,
            sample=new_record,
            status=data['link']['status'] or 'unknown',
            father=(self.db.find_sample(customer_obj, data['link']['father']) if
                    data['link']['father'] else None),
            mother=(self.db.find_sample(customer_obj, data['link']['mother']) if
                    data['link']['mother'] else None),
        )
        return [new_record, link_obj, family_obj]

    def records(self):
        samples = self.lims.get_samples()
        count = len(samples)
        with click.progressbar(samples, length=count, label='samples') as progressbar:
            for lims_sample in progressbar:
                if self.db.sample(lims_sample.id) is None:
                    sample = self.lims.sample(lims_sample.id)

                    if sample['application'] is None:
                        log.error(f"missing application: {sample}")
                        continue
                    elif sample['customer'] is None:
                        log.error(f"missing customer: {sample}")
                        continue
                    elif sample['application'].startswith(('MWG', 'RML', 'MET')):
                        continue
                    elif sample['family'] is None:
                        log.error(f"missing family name: {sample}")
                        continue

                    data = self.convert(sample)
                    customer_obj = self.db.customer(data['customer'])
                    existing_sample = self.db.find_sample(customer_obj, data['name'])
                    if existing_sample:
                        log.error(f"found existing sample: {existing_sample.to_dict()}")
                        continue

                    new_records = self.status(data)
                    if new_records is None:
                        continue
                    self.db.add_commit(new_records)
