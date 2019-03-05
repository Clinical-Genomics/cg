# -*- coding: utf-8 -*-
import datetime as dt
import logging

from genologics.entities import Sample, Process
from genologics.lims import Lims
from dateutil.parser import parse as parse_date

from cg.exc import LimsDataError
from .constants import PROP2UDF
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
        lims_artifacts = self.get_artifacts(process_type='CG002 - Reception Control',
                                            samplelimsid=lims_id)
        for artifact in lims_artifacts:
            udf_key = 'date arrived at clinical genomics'
            if artifact.parent_process and artifact.parent_process.udf.get(udf_key):
                return artifact.parent_process.udf.get(udf_key)

    def get_prepared_date(self, lims_id: str) -> dt.datetime:
        """Get the date when a sample was prepared in the lab."""
        process_type = 'CG002 - Aggregate QC (Library Validation)'
        artifacts = self.get_artifacts(process_type=process_type, samplelimsid=lims_id)
        if artifacts:
            return parse_date(artifacts[0].parent_process.date_run)

    def get_delivery_date(self, lims_id: str) -> dt.date:
        """Get delivery date for a sample."""
        artifacts = self.get_artifacts(samplelimsid=lims_id, process_type='CG002 - Delivery',
                                       type='Analyte')
        if len(artifacts) == 1:
            return artifacts[0].parent_process.udf.get('Date delivered')
        elif len(artifacts) == 0:
            return None
        else:
            log.warning(f"multiple delivery artifacts found for: {lims_id}")
            return min(artifact.parent_process.udf['Date delivered'] for artifact in artifacts)

    def get_sequenced_date(self, lims_id: str) -> dt.date:
        """Get the date when a sample was sequenced."""
        process_types = ['CG002 - Illumina Sequencing (Illumina SBS)',
                         'CG002 - Illumina Sequencing (HiSeq X)']

        for process_type in process_types:
            lims_artifacts = self.get_artifacts(process_type=process_type, samplelimsid=lims_id)

            if len(lims_artifacts) == 0:
                continue  # continue in case the artifacts are in the other process_type
            elif len(lims_artifacts) == 1:
                return lims_artifacts[0].parent_process.udf.get('Finish Date')  # return date immediately if only one artifact is found
            else:
                log.warning(f"multiple sequence artifacts found for: {lims_id}")
                sequence_dates = [artifact.parent_process.udf.get('Finish Date') for artifact in lims_artifacts
                                  if artifact.parent_process.udf.get('Finish Date') is not None]
                if len(sequence_dates) == 0:
                    break  # nothing sequenced, break out and return None
                else:
                    return min(sequence_dates)

        return None  # if nothing is found just return None

    def capture_kit(self, lims_id: str) -> str:
        """Get capture kit for a LIMS sample."""
        lims_sample = Sample(self, id=lims_id)
        capture_kit = lims_sample.udf.get('Capture Library version')
        if capture_kit and capture_kit != 'NA':
            return capture_kit
        else:
            artifacts = self.get_artifacts(
                samplelimsid=lims_id,
                process_type='CG002 - Hybridize Library  (SS XT)',
                type='Analyte'
            )
            udf_key = 'SureSelect capture library/libraries used'
            capture_kits = set(artifact.parent_process.udf.get(udf_key) for artifact in artifacts)
            if len(capture_kits) == 1:
                return capture_kits.pop()
            else:
                message = f"Capture kit error: {lims_sample.id} | {capture_kits}"
                raise LimsDataError(message)

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
        process_names = [
            'CG002 - End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free '
            'DNA)',
            'CG002 - Hybridize Library  (SS XT)',
        ]
        method_name = method_number = None
        for process_name in process_names:
            arts = self.get_artifacts(process_type=process_name, samplelimsid=lims_id)
            if arts:
                prep_artifact = arts[0]
                method_number = prep_artifact.parent_process.udf.get('Method document')
                method_version = (
                        prep_artifact.parent_process.udf.get('Method document version') or
                        prep_artifact.parent_process.udf.get('Method document versio')
                )
                break

        if method_number is None:
            return None

        method_name = AM_METHODS.get(method_number)
        return f"{method_number}:{method_version} - {method_name}"

    def get_sequencing_method(self, lims_id: str) -> str:
        """Get the sequencing method."""
        process_names = [
            'CG002 - Cluster Generation (HiSeq X)',
            'CG002 - Cluster Generation (Illumina SBS)',
        ]
        method_number = method_version = None
        for process_name in process_names:
            arts = self.get_artifacts(process_type=process_name, samplelimsid=lims_id)
            if arts:
                prep_artifact = arts[0]
                method_number = (
                        prep_artifact.parent_process.udf.get('Method') or
                        prep_artifact.parent_process.udf.get('Method Document 1')
                )
                method_version = (
                        prep_artifact.parent_process.udf.get('Version') or
                        prep_artifact.parent_process.udf.get('Document 1 Version')
                )
                break

        if method_number is None:
            return None

        method_name = AM_METHODS.get(method_number)
        return f"{method_number}:{method_version} - {method_name}"

    def get_delivery_method(self, lims_id: str) -> str:
        """Get the delivery method."""
        process_name = 'CG002 - Delivery'
        arts = self.get_artifacts(process_type=process_name, samplelimsid=lims_id)
        if arts:
            prep_artifact = arts[0]
            method_number = prep_artifact.parent_process.udf.get('Method Document')
            method_version = prep_artifact.parent_process.udf.get('Method Version')
        else:
            return None

        method_name = AM_METHODS.get(method_number)
        return f"{method_number}:{method_version} - {method_name}"
