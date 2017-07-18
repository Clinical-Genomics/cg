# -*- coding: utf-8 -*-
"""
USER                          => DONE (import scout later)
CUSTOMER                      => DONE (handle AMSystems manually)
FAMILY                        => DONE (curate duplicates later)
SAMPLE                        => DONE (do, handle genotype results later)
FAMILY-SAMPLE                 => DONE (do)
FLOWCELL + FLOWCELL-SAMPLE    => cgstats (kenny)
ANALYSIS                      => housekeeper
APPLICATION                   => DONE (handle clinicalgenomics.se manually)
APPLICATION-VERSION           => DONE (do)
PANEL                         => DONE
"""

import datetime as dt
import logging

from cgadmin.store.api import AdminDatabase
import click
from housekeeper.store import api as hk_api
import pymongo
import ruamel.yaml

from cg.apps import lims as lims_app, scoutapi
from cg.store import Store

log = logging.getLogger(__name__)


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


class CustomerImporter():

    def __init__(self, db, admin):
        self.db = db
        self.admin = admin

    @staticmethod
    def convert(customer):
        return {
            'internal_id': customer.customer_id,
            'name': customer.name,
            'scout_access': customer.scout_access,
            'agreement_date': (dt.datetime.combine(customer.agreement_date, dt.time()) if
                               customer.agreement_date else None),
            'agreement_registration': customer.agreement_registration,
            'invoice_address': customer.invoice_address,
            'invoice_reference': customer.invoice_reference,
            'organisation_number': customer.organisation_number,
            'project_account_ki': customer.project_account_ki,
            'project_account_kth': customer.project_account_kth,
            'uppmax_account': customer.uppmax_account,

            'primary_contact': (customer.primary_contact.email if
                                customer.primary_contact else None),
            'delivery_contact': (customer.delivery_contact.email if
                                 customer.delivery_contact else None),
            'invoice_contact': (customer.invoice_contact.email if
                                customer.invoice_contact else None),
        }

    def status(self, data):
        record = self.db.Customer(**data)
        return record

    def records(self):
        query = self.admin.Customer
        count = query.count()
        with click.progressbar(query, length=count, label='customers') as progressbar:
            for admin_record in progressbar:
                data = self.convert(admin_record)
                if not self.db.customer(data['internal_id']):
                    new_record = self.status(data)
                    self.db.add(new_record)
        self.db.commit()


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


class UserImporter():

    def __init__(self, db, admin):
        self.db = db
        self.admin = admin

    @staticmethod
    def convert(record):
        return {
            'name': record.name,
            'email': record.email,
            'admin': record.is_admin,
            'customer': record.customers[0].customer_id if record.customers else 'cust999',
        }

    def status(self, data):
        customer_obj = self.db.customer(data['customer'])
        new_record = self.db.User(
            email=data['email'],
            name=data['name'],
            admin=data['admin'],
        )
        new_record.customer = customer_obj
        return new_record

    def records(self):
        query = self.admin.User
        count = query.count()
        with click.progressbar(query, length=count, label='users') as progressbar:
            for admin_record in progressbar:
                data = self.convert(admin_record)
                if not self.db.user(data['email']):
                    new_record = self.status(data)
                    self.db.add(new_record)
        self.db.commit()


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


@click.command()
@click.argument('config_file', type=click.File())
def transfer(config_file):
    """Transfer stuff from external interfaces."""
    config = ruamel.yaml.safe_load(config_file)

    status_api = Store(config['database'])
    admin_api = AdminDatabase(config['cgadmin']['database'])
    log.info('loading customers')
    customer_importer = CustomerImporter(status_api, admin_api)
    customer_importer.records()

    log.info('loading users')
    user_importer = UserImporter(status_api, admin_api)
    user_importer.records()

    log.info('loading applications')
    application_importer = ApplicationImporter(status_api, admin_api)
    application_importer.records()

    log.info('loading application versions')
    version_importer = VersionImporter(status_api, admin_api)
    version_importer.records()

    scout_api = scoutapi.ScoutAPI(config)
    log.info('loading panels')
    panel_importer = PanelImporter(status_api, scout_api)
    panel_importer.records()

    lims_api = lims_app.LimsAPI(config)
    log.info('loading samples, families, and links')
    sample_importer = SampleImporter(status_api, lims_api)
    sample_importer.records()

    hk_manager = hk_api.manager(config['housekeeper']['old']['database'])
    log.info('loading analyses')
    analysis_importer = AnalysisImporter(status_api, hk_manager)
    analysis_importer.records()


if __name__ == '__main__':
    transfer()
