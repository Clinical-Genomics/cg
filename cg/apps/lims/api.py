# -*- coding: utf-8 -*-
import datetime as dt
import logging

from genologics.entities import Sample, Process
from genologics.lims import Lims
from dateutil.parser import parse as parse_date

from cg.exc import LimsDataError
from .constants import PROP2UDF, MASTER_STEPS_UDFS
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

        step_names_udfs = MASTER_STEPS_UDFS['received_step']
        received_dates = []

        for process_type in step_names_udfs:
            artifacts = self.get_artifacts(process_type=process_type, samplelimsid=lims_id)

            for artifact in artifacts:
                udf_key = step_names_udfs[process_type]
                if artifact.parent_process and artifact.parent_process.udf.get(udf_key):
                    received_dates.append((artifact.parent_process.date_run,
                                           artifact.parent_process.udf.get(udf_key)))

        sorted_dates = self.sort_dates_by_date_run_descending(received_dates)
        received_date = self.most_recent_date(sorted_dates)

        return received_date

    def get_prepared_date(self, lims_id: str) -> dt.datetime:
        """Get the date when a sample was prepared in the lab."""

        step_names_udfs = MASTER_STEPS_UDFS['prepared_step']
        prepared_dates = []

        for process_type in step_names_udfs:
            artifacts = self.get_artifacts(process_type=process_type, samplelimsid=lims_id)

            for artifact in artifacts:
                prepared_dates.append(parse_date(artifact.parent_process.date_run))

        sorted_dates = self.sort_dates_by_date_run_descending(prepared_dates)
        prepared_date = self.most_recent_date(sorted_dates)

        return prepared_date

    def get_delivery_date(self, lims_id: str) -> dt.date:
        """Get delivery date for a sample."""

        step_names_udfs = MASTER_STEPS_UDFS['delivery_step']
        delivered_dates = []

        for process_type in step_names_udfs:
            artifacts = self.get_artifacts(process_type=process_type, samplelimsid=lims_id,
                                           type='Analyte')

            for artifact in artifacts:
                udf_key = step_names_udfs[process_type]
                if artifact.parent_process and artifact.parent_process.udf.get(udf_key):
                    delivered_dates.append((artifact.parent_process.date_run,
                                            artifact.parent_process.udf.get(udf_key)))

        sorted_dates = self.sort_dates_by_date_run_descending(delivered_dates)

        if len(sorted_dates) > 1:
            log.warning("multiple delivery artifacts found for: %s, lims_id")

        delivered_date = self.most_recent_date(sorted_dates)

        return delivered_date

    def get_sequenced_date(self, lims_id: str) -> dt.date:
        """Get the date when a sample was sequenced."""

        step_names_udfs = MASTER_STEPS_UDFS['sequenced_step']
        sequenced_dates = []

        for process_type in step_names_udfs:
            artifacts = self.get_artifacts(process_type=process_type, samplelimsid=lims_id)

            for artifact in artifacts:
                udf_key = step_names_udfs[process_type]
                if artifact.parent_process and artifact.parent_process.udf.get(udf_key):
                    sequenced_dates.append((artifact.parent_process.date_run,
                                            artifact.parent_process.udf.get(udf_key)))
                if artifact.parent_process and process_type == 'AUTOMATED - NovaSeq Run':
                    sequenced_dates.append((artifact.parent_process.date_run,
                                            artifact.parent_process.date_run))

        sorted_dates = self.sort_dates_by_date_run_descending(sequenced_dates)

        if len(sorted_dates) > 1:
            log.warning("multiple sequence artifacts found for: %s", lims_id)

        sequenced_date = self.most_recent_date(sorted_dates)

        return sequenced_date

    def capture_kit(self, lims_id: str) -> str:
        """Get capture kit for a LIMS sample."""

        step_names_udfs = MASTER_STEPS_UDFS['capture_kit_step']
        capture_kits = set()

        lims_sample = Sample(self, id=lims_id)
        capture_kit = lims_sample.udf.get('Capture Library version')
        if capture_kit and capture_kit != 'NA':
            return capture_kit
        else:
            for process_type in step_names_udfs:
                artifacts = self.get_artifacts(
                    samplelimsid=lims_id,
                    process_type=process_type,
                    type='Analyte'
                )
                udf_key = step_names_udfs[process_type]
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

        step_names_udfs = MASTER_STEPS_UDFS['prep_method_step']

        return self.get_methods(step_names_udfs, lims_id)

    def get_sequencing_method(self, lims_id: str) -> str:
        """Get the sequencing method."""

        step_names_udfs = MASTER_STEPS_UDFS['get_sequencing_method_step']

        return self.get_methods(step_names_udfs, lims_id)

    def get_delivery_method(self, lims_id: str) -> str:
        """Get the delivery method."""

        step_names_udfs = MASTER_STEPS_UDFS['get_delivery_method_step']

        return self.get_methods(step_names_udfs, lims_id)

    def get_processing_time(self, lims_id):
        received_at = self.get_received_date(lims_id)
        delivery_date = self.get_delivery_date(lims_id)
        if received_at and delivery_date:
            return delivery_date - received_at

    @staticmethod
    def sort_dates_by_date_run_descending(dates: list):
        """
        Sort dates by parent process attribute date_run in descending order.

        Parameters:
            dates (list): a list of tuples in the format (date_run, date)

        Returns:
            sorted list of tuples
        """
        return sorted(dates, key=lambda date_tuple: date_tuple[0], reversed=True)

    @staticmethod
    def most_recent_date(dates: list):
        """
        Gets the most recent date from a list of dates sorted by date_run

        Parameters:
            dates (list): a list of tuples in the format (date_run, date), sorted by date_run
            descending

        Returns:
            The date in the first tuple in dates
        """
        date_run_index = 0
        date_index = 1

        return dates[date_run_index][date_index] if dates else None

    def get_methods(self, step_names_udfs, lims_id):
        """
        Gets the method, method number and method version for a given list of stop names
        """
        methods = []
        method_index = 0
        method_number_index = 1
        method_version_index = 2

        method_name = method_number = None
        for process_name in step_names_udfs:
            artifacts = self.get_artifacts(process_type=process_name, samplelimsid=lims_id)
            if artifacts:
                udf_key_number = step_names_udfs[process_name]['method_number']
                udf_key_version = step_names_udfs[process_name]['method_version']
                artifact = artifacts[0]
                date_run = artifact.parent_process.date_run
                method_number = artifact.parent_process.udf.get(udf_key_number)
                method_version = artifact.parent_process.udf.get(udf_key_version)
                methods.append((date_run, method_number, method_version))

        sorted_methods = sorted(methods, key=lambda x: x[0], reversed=True)

        if sorted_methods:
            method = sorted_methods[method_index]
            method_number = method[method_number_index]
            method_version = method[method_version_index]

        if method_number is None:
            return None

        method_name = AM_METHODS.get(method_number)
        return f"{method_number}:{method_version} - {method_name}"
