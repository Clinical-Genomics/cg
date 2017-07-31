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
#from housekeeper.store import api as hk_api
import pymongo
import ruamel.yaml
from sqlalchemy.exc import IntegrityError

from cg.apps import lims as lims_app, scoutapi, stats
from cg.constants import PRIORITY_MAP
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
        target_reads = 0
        if 'WIP' not in record.name:
            type_id = record.name[-4]
            number = int(record.name[-3:])
            if type_id == 'R':
                target_reads = number * 1000000
            elif type_id == 'K':
                target_reads = number * 1000
            elif type_id == 'C':
                # expect WGS, how many reads needed to cover genome 1x
                READS_PER_1X = 650000000 / 0.75 / 30
                target_reads = number * READS_PER_1X

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
            'target_reads': target_reads,
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
        data = {
            'internal_id': sample['id'],
            'order': sample['project']['name'],
            'ordered_at': sample['project']['date'],
            'name': sample['name'],
            'sex': sample['sex'],
            'customer': sample['customer'],
            'application': sample['application'],
            'application_version': sample['application_version'],
            'received_at': sample['received'],
            'external': (sample['application'][:3] in ('EXX', 'WGX')),
            'tumour': (sample.get('tumor') == 'yes'),
            'priority': sample['priority'],
        }
        return data

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
        if customer_obj is None:
            log.error(f"unknown customer: {data['customer']}")
            return
        new_record = self.db.add_sample(
            name=data['name'],
            sex=data['sex'] or 'unknown',
            internal_id=data['internal_id'],
            received=data['received_at'],
            order=data['order'],
            external=data['external'],
            tumour=data['tumour'],
        )
        new_record.customer = customer_obj
        new_record.application_version = version_obj
        return new_record

    def records(self):
        samples = self.lims.get_samples()
        count = len(samples)
        with click.progressbar(samples, length=count, label='samples') as progressbar:
            for lims_sample in progressbar:
                sample = validate_sample(self.db, self.lims, lims_sample)
                if sample is None:
                    continue

                data = self.convert(sample)
                new_record = self.status(data)
                if new_record is None:
                    continue
                try:
                    self.db.add_commit(new_record)
                except IntegrityError:
                    log.error(f"duplicate sample: {new_record.to_dict()}")
                    self.db.session.rollback()
                    continue


def validate_sample(db, lims, lims_sample, family=False):
    if not family and db.sample(lims_sample.id) is not None:
        return None
    sample = lims.sample(lims_sample.id)
    if sample['application'] is None:
        log.debug(f"missing application udf: {sample}")
        return None
    elif sample['application'].startswith(('MWG', 'RML', 'MET')):
        return None
    elif sample['customer'] is None:
        log.debug(f"missing customer udf: {sample}")
        return None
    elif family and sample['family'] is None:
        return None

    if family:
        customer_obj = db.customer(sample['customer'])
        if family and db.find_family(customer_obj, sample['family']) is not None:
            return None

        family_samples = lims.get_samples(udf={'customer': sample['customer'],
                                               'familyID': sample['family']})
        return [lims.sample(family_sample.id) for family_sample in family_samples]
    else:
        return sample


class FamilyImporter():

    def __init__(self, db, lims):
        self.db = db
        self.lims = lims

    def convert(self, samples):
        priorities = set((sample['priority'] or 'standard') for sample in samples)
        if len(priorities) == 1:
            priority = priorities.pop()
            if priority not in PRIORITY_MAP:
                log.error(f"incorrect prio: {priority}")
                return None
        else:
            if 'express' in priorities:
                priority = 'express'
            elif 'priority' in priorities:
                priority = 'priority'
            elif 'standard' in priorities:
                priority = 'standard'
            else:
                log.error(f"incorrect prio: {priorities}")
                return None

        panels = set(['OMIM-AUTO'])
        for sample in samples:
            if sample['panels']:
                panels.update(sample['panels'])

        return {
            'customer': samples[0]['customer'],
            'name': samples[0]['family'],
            'panels': list(panels),
            'priority': priority,
            'links': [{
                'sample': sample['name'],
                'father': sample['father'],
                'mother': sample['mother'],
                'status': sample['status'] or 'unknown',
            } for sample in samples]
        }

    def status(self, data):
        customer_obj = self.db.customer(data['customer'])
        family_obj = self.db.add_family(
            name=data['name'],
            priority=data['priority'],
            panels=data['panels'],
        )
        family_obj.customer = customer_obj
        new_records = [family_obj]

        for link_data in data['links']:
            for sample_obj in self.db.find_sample(customer_obj, data['name']):
                link_obj = self.db.relate_sample(
                    family=family_obj,
                    sample=sample_obj,
                    status=link_data['status'],
                    father=(self.db.find_sample(customer_obj, link_data['father']).first() if
                            link_data['father'] else None),
                    mother=(self.db.find_sample(customer_obj, link_data['mother']).first() if
                            link_data['mother'] else None),
                )
                new_records.append(link_obj)
        return new_records

    def records(self):
        # figure out which samples might be linked together
        covered_families = set()
        samples = self.lims.get_samples()
        count = len(samples)
        with click.progressbar(samples, length=count, label='families') as progressbar:
            for lims_sample in progressbar:
                samples = validate_sample(self.db, self.lims, lims_sample, family=True)
                if samples is None:
                    continue

                family_id = f"{samples[0]['customer']}-{samples[0]['family']}"
                if family_id in covered_families:
                    continue
                data = self.convert(samples)
                if data is None:
                    continue
                new_records = self.status(data)
                self.db.add_commit(new_records)
                covered_families.add(family_id)


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


class FlowcellImporter():

    def __init__(self, db, stats):
        self.db = db
        self.stats = stats

    def convert(self, sample):
        return {
            'reads': sum(unaligned.readcounts for unaligned in sample.unaligned),
            'flowcells': [{
                'name': unaligned.demux.flowcell.flowcellname,
                'date': unaligned.demux.flowcell.time,
                'sequencer_type': unaligned.demux.flowcell.hiseqtype,
                'sequencer': unaligned.demux.datasource.machine,
            } for unaligned in sample.unaligned]
        }

    def status(self, sample_obj, data):
        sample_obj.reads = data['reads']
        enough_reads = (sample_obj.reads >
                        sample_obj.application_version.application.expected_reads)
        if enough_reads:
            sample_obj.sequenced_at = max(fc_data['date'] for fc_data in data['flowcells'])

        for flowcell_data in data['flowcells']:
            flowcell_obj = self.db.flowcell(flowcell_data['name'])
            if flowcell_obj is None:
                flowcell_obj = self.db.add_flowcell(
                    name=flowcell_data['name'],
                    date=flowcell_data['date'],
                    sequencer=flowcell_data['sequencer'],
                    sequencer_type=flowcell_data['sequencer_type'],
                )
                self.db.add(flowcell_obj)
            if flowcell_obj not in sample_obj.flowcells:
                sample_obj.flowcells.append(flowcell_obj)

    def records(self):
        query = self.stats.Sample.query
        count = query.count()
        with click.progressbar(query, length=count, label='flowcells') as progressbar:
            for stats_sample in progressbar:
                sample_obj = self.db.sample(stats_sample.lims_id)
                if sample_obj is None:
                    continue
                data = self.convert(stats_sample)
                sample_obj = self.status(sample_obj, data)
                if sample_obj is not None:
                    self.db.commit()


@click.command()
@click.argument('config_file', type=click.File())
def transfer(config_file):
    """Transfer stuff from external interfaces."""
    config = ruamel.yaml.safe_load(config_file)
    status_api = Store(config['database'])

    # admin_api = AdminDatabase(config['cgadmin']['database'])
    # log.info('loading customers')
    # customer_importer = CustomerImporter(status_api, admin_api)
    # customer_importer.records()

    # log.info('loading users')
    # user_importer = UserImporter(status_api, admin_api)
    # user_importer.records()

    # log.info('loading applications')
    # application_importer = ApplicationImporter(status_api, admin_api)
    # application_importer.records()

    # log.info('loading application versions')
    # version_importer = VersionImporter(status_api, admin_api)
    # version_importer.records()

    # scout_api = scoutapi.ScoutAPI(config)
    # log.info('loading panels')
    # panel_importer = PanelImporter(status_api, scout_api)
    # panel_importer.records()

    # lims_api = lims_app.LimsAPI(config)
    # log.info('loading samples')
    # sample_importer = SampleImporter(status_api, lims_api)
    # sample_importer.records()

    # log.info('loading families and links')
    # family_importer = FamilyImporter(status_api, lims_api)
    # family_importer.records()

    stats_api = stats.StatsAPI(config)
    log.info('loading flowcells')
    flowcell_importer = FlowcellImporter(status_api, stats_api)
    flowcell_importer.records()

    # hk_manager = hk_api.manager(config['housekeeper']['old']['database'])
    # log.info('loading analyses')
    # analysis_importer = AnalysisImporter(status_api, hk_manager)
    # analysis_importer.records()


if __name__ == '__main__':
    transfer()
