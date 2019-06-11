# -*- coding: utf-8 -*-
import datetime as dt
import logging

from genologics.entities import Sample, Process
from genologics.lims import Lims
from dateutil.parser import parse as parse_date

from cg.exc import LimsDataError
from .constants import PROP2UDF, MASTER_STEPS
from .order import OrderHandler

# fixes https://github.com/Clinical-Genomics/servers/issues/30
import requests_cache
requests_cache.install_cache(backend='memory')

SEX_MAP = {'F': 'female', 'M': 'male', 'Unknown': 'unknown', 'unknown': 'unknown'}
REV_SEX_MAP = {value: key for key, value in SEX_MAP.items()}
AM_METHODS = {
    '1464': 'Automated TruSeq DNA PCR-free library preparation method',
    '1317': 'HiSeq X Sequencing method at Clinical Genomics',
    '1383': 'MIP analysis for Whole genome and Exome',
    '1717': 'NxSeq® AmpFREE Low DNA Library Kit (Lucigen)',
    '1060': 'Raw data delivery',
    '1036': 'HiSeq 2500 Rapid Run sequencing',
    '1314': 'Automated SureSelect XT Target Enrichment for Illumina sequencing',
    '1518': '200 ng input Manual SureSelect XT Target Enrichment',
    '1079': 'Manuel SureSelect XT Target Enrichment for Illumina sequencing',
}
log = logging.getLogger(__name__)


class LimsAPI(Lims, OrderHandler):

    def __init__(self, config):
        lconf = config['lims']
        super(LimsAPI, self).__init__(lconf['host'], lconf['username'], lconf['password'])

    def sample(self, lims_id: str):
        """Fetch a sample from the LIMS database."""
        lims_sample = Sample(self, id=lims_id)
        data = self._export_sample(lims_sample)
        return data

    def samples_in_pools(self, pool_name, projectname):
        return self.get_samples(udf={"pool name": str(pool_name)}, projectname=projectname)

    def _export_project(self, lims_project):
        return {
            'id': lims_project.id,
            'name': lims_project.name,
            'date': parse_date(lims_project.open_date) if lims_project.open_date else None,
        }

    def _export_sample(self, lims_sample):
        """Get data from a LIMS sample."""
        udfs = lims_sample.udf
        data = {
            'id': lims_sample.id,
            'name': lims_sample.name,
            'project': self._export_project(lims_sample.project),
            'family': udfs.get('familyID'),
            'customer': udfs.get('customer'),
            'sex': SEX_MAP.get(udfs.get('Gender'), None),
            'father': udfs.get('fatherID'),
            'mother': udfs.get('motherID'),
            'source': udfs.get('Source'),
            'status': udfs.get('Status'),
            'panels': udfs.get('Gene List').split(';') if udfs.get('Gene List') else None,
            'priority': udfs.get('priority'),
            'received': self.get_received_date(lims_sample.id),
            'application': udfs.get('Sequencing Analysis'),
            'application_version': (int(udfs['Application Tag Version']) if
                                    udfs.get('Application Tag Version') else None),
            'comment': udfs.get('comment'),
        }
        return data

    def _export_artifact(self, lims_artifact):
        """Get data from a LIMS artifact."""
        return {
            'id': lims_artifact.id,
            'name': lims_artifact.name,
        }

    def get_received_date(self, lims_id: str) -> str:
        """Get the date when a sample was received."""

        step_names = MASTER_STEPS['received_step']
        received_dates = []

        for process_type in step_names:
            artifacts = self.get_artifacts(process_type=process_type, samplelimsid=lims_id)

            for artifact in artifacts:
                udf_key = 'date arrived at clinical genomics'
                if artifact.parent_process and artifact.parent_process.udf.get(udf_key):
                    received_dates.append((artifact.parent_process.date_run,
                                           artifact.parent_process.udf.get(udf_key)))

        sorted_dates = sorted(received_dates, key=lambda x: x[0])

        return sorted_dates[-1][1] if len(sorted_dates) > 0 else None

    def get_prepared_date(self, lims_id: str) -> dt.datetime:
        """Get the date when a sample was prepared in the lab."""

        step_names = MASTER_STEPS['prepared_step']
        prepared_dates = []

        for process_type in step_names:
            artifacts = self.get_artifacts(process_type=process_type, samplelimsid=lims_id)

            for artifact in artifacts:
                prepared_dates.append(parse_date(artifact.parent_process.date_run))

        sorted_dates = sorted(prepared_dates)

        return sorted_dates[-1] if len(sorted_dates) > 0 else None

    def get_delivery_date(self, lims_id: str) -> dt.date:
        """Get delivery date for a sample."""

        step_names = MASTER_STEPS['delivery_step']
        delivered_dates = []

        for process_type in step_names:
            artifacts = self.get_artifacts(process_type=process_type, samplelimsid=lims_id,
                                           type='Analyte')

            for artifact in artifacts:
                udf_key = 'Date delivered'
                if artifact.parent_process and artifact.parent_process.udf.get(udf_key):
                    delivered_dates.append((artifact.parent_process.date_run,
                                            artifact.parent_process.udf.get(udf_key)))

        sorted_dates = sorted(delivered_dates, key=lambda x: x[0])

        if len(sorted_dates) > 0:
            log.warning(f"multiple delivery artifacts found for: {lims_id}")

        return sorted_dates[-1][1] if len(sorted_dates) > 0 else None

    def get_sequenced_date(self, lims_id: str) -> dt.date:
        """Get the date when a sample was sequenced."""

        step_names = MASTER_STEPS['sequenced_step']
        sequenced_dates = []

        for process_type in step_names:
            artifacts = self.get_artifacts(process_type=process_type, samplelimsid=lims_id)

            for artifact in artifacts:
                udf_key = 'Finish Date'
                if artifact.parent_process and artifact.parent_process.udf.get(udf_key):
                    sequenced_dates.append((artifact.parent_process.date_run,
                                            artifact.parent_process.udf.get(udf_key)))
                if artifact.parent_process and process_type == 'AUTOMATED - NovaSeq Run':
                    sequenced_dates.append((artifact.parent_process.date_run,
                                            artifact.parent_process.date_run))

        sorted_dates = sorted(sequenced_dates, key=lambda x: x[0])

        if len(sorted_dates) > 0:
            log.warning(f"multiple sequence artifacts found for: {lims_id}")

        return sorted_dates[-1][1] if len(sorted_dates) > 0 else None

    def capture_kit(self, lims_id: str) -> str:
        """Get capture kit for a LIMS sample."""

        step_names = MASTER_STEPS['capture_kit_step']
        capture_kits = set()

        lims_sample = Sample(self, id=lims_id)
        capture_kit = lims_sample.udf.get('Capture Library version')
        if capture_kit and capture_kit != 'NA':
            return capture_kit
        else:
            for process_type in step_names:
                artifacts = self.get_artifacts(
                    samplelimsid=lims_id,
                    process_type=process_type,
                    type='Analyte'
                )
                udf_key = 'SureSelect capture library/libraries used'
                capture_kits = capture_kits.union(set(artifact.parent_process.udf.get(udf_key) for
                                                      artifact in artifacts))
                if len(capture_kits) == 1:
                    continue
                else:
                    message = f"Capture kit error: {lims_sample.id} | {capture_kits}"
                    raise LimsDataError(message)

        return capture_kits.pop()

    def get_samples(self, *args, map_ids=False, **kwargs):
        """Bypass to original method."""
        lims_samples = super(LimsAPI, self).get_samples(*args, **kwargs)
        if map_ids:
            lims_map = {lims_sample.name: lims_sample.id for lims_sample in lims_samples}
            return lims_map
        else:
            return lims_samples

    def family(self, customer: str, family: str):
        """Fetch information about a family of samples."""
        filters = {'customer': customer, 'familyID': family}
        lims_samples = self.get_samples(udf=filters)
        samples_data = [self._export_sample(lims_sample) for lims_sample in lims_samples]
        # get family level data
        family_data = {'family': family, 'customer': customer, 'samples': []}
        priorities = set()
        panels = set()

        for sample_data in samples_data:
            priorities.add(sample_data['priority'])
            if sample_data['panels']:
                panels.update(sample_data['panels'])
            family_data['samples'].append(sample_data)

        if len(priorities) == 1:
            family_data['priority'] = priorities.pop()
        elif 'express' in priorities:
            family_data['priority'] = 'express'
        elif 'priority' in priorities:
            family_data['priority'] = 'priority'
        elif 'standard' in priorities:
            family_data['priority'] = 'standard'
        else:
            raise LimsDataError(f"unable to determine family priority: {priorities}")

        family_data['panels'] = list(panels)
        return family_data

    def process(self, process_id: str) -> Process:
        """Get LIMS process."""
        return Process(self, id=process_id)

    def process_samples(self, lims_process: Process):
        """Retrieve LIMS input samples from a process."""
        for lims_artifact in lims_process.all_inputs():
            for lims_sample in lims_artifact.samples:
                yield lims_sample.id

    def update_sample(self, lims_id: str, sex=None, application: str=None,
                      target_reads: int=None):
        """Update information about a sample."""
        lims_sample = Sample(self, id=lims_id)
        if sex:
            lims_gender = REV_SEX_MAP.get(sex)
            if lims_gender:
                lims_sample.udf[PROP2UDF['sex']] = lims_gender
        if application:
            lims_sample.udf[PROP2UDF['application']] = application
        if isinstance(target_reads, int):
            lims_sample.udf[PROP2UDF['target_reads']] = target_reads
        lims_sample.put()

    def get_prep_method(self, lims_id: str) -> str:
        """Get the library preparation method."""

        step_names = MASTER_STEPS['prep_method_step']
        prep_methods = []

        method_name = method_number = None
        for process_name in step_names:
            arts = self.get_artifacts(process_type=process_name, samplelimsid=lims_id)
            if arts:
                prep_artifact = arts[0]
                date_run = prep_artifact.parent_process.date_run
                method_number = prep_artifact.parent_process.udf.get('Method document')
                method_version = (
                        prep_artifact.parent_process.udf.get('Method document version') or
                        prep_artifact.parent_process.udf.get('Method document versio')
                )
                prep_methods.append((date_run, method_number, method_version))

        sorted_methods = sorted(prep_methods, key=lambda x: x[0])

        prep_method = sorted_methods[-1]
        method_number = prep_method[1]
        method_version = prep_method[2]

        if method_number is None:
            return None

        method_name = AM_METHODS.get(method_number)
        return f"{method_number}:{method_version} - {method_name}"

    def get_sequencing_method(self, lims_id: str) -> str:
        """Get the sequencing method."""

        step_names = MASTER_STEPS['get_sequencing_method_step']
        seq_methods = []

        method_number = method_version = None
        for process_name in step_names:
            arts = self.get_artifacts(process_type=process_name, samplelimsid=lims_id)
            if arts:
                prep_artifact = arts[0]
                date_run = prep_artifact.parent_process.date_run
                method_number = (
                        prep_artifact.parent_process.udf.get('Method') or
                        prep_artifact.parent_process.udf.get('Method Document 1')
                )
                method_version = (
                        prep_artifact.parent_process.udf.get('Version') or
                        prep_artifact.parent_process.udf.get('Document 1 Version')
                )
                seq_methods.append((date_run, method_number, method_version))

        sorted_methods = sorted(seq_methods, key=lambda x: x[0])

        seq_method = sorted_methods[-1]
        method_number = seq_method[1]
        method_version = seq_method[2]
        method_name = AM_METHODS.get(method_number)

        if method_number is None:
            return None

        return f"{method_number}:{method_version} - {method_name}"

    def get_delivery_method(self, lims_id: str) -> str:
        """Get the delivery method."""

        step_names = MASTER_STEPS['get_delivery_method_step']
        deliver_methods = []

        for process_name in step_names:
            arts = self.get_artifacts(process_type=process_name, samplelimsid=lims_id)
            if arts:
                prep_artifact = arts[0]
                date_run = prep_artifact.parent_process.date_run
                method_number = prep_artifact.parent_process.udf.get('Method Document')
                method_version = prep_artifact.parent_process.udf.get('Method Version')
                deliver_methods.append((date_run, method_number, method_version))

        sorted_methods = sorted(deliver_methods, key=lambda x: x[0])

        deliver_method = sorted_methods[-1]
        method_number = deliver_method[1]
        method_version = deliver_method[2]
        method_name = AM_METHODS.get(method_number)

        if method_number is None:
            return None

        return f"{method_number}:{method_version} - {method_name}"

    def get_processing_time(self, lims_id):
        received_at = self.get_received_date(lims_id)
        delivery_date = self.get_delivery_date(lims_id)
        if received_at and delivery_date:
            return delivery_date - received_at
