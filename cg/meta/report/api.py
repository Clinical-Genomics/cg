# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import requests
import ruamel.yaml
from jinja2 import Environment, PackageLoader, select_autoescape
from pathlib import Path

from cg.apps.tb import TrailblazerAPI
from cg.apps.coverage import ChanjoAPI
from cg.meta.deliver.api import DeliverAPI
from cg.apps.lims import LimsAPI
from cg.store import Store, models
from cg.meta.analysis import AnalysisAPI


class ReportAPI:

    def __init__(self, db: Store, lims_api: LimsAPI, tb_api: TrailblazerAPI, deliver_api:
    DeliverAPI, chanjo_api: ChanjoAPI, analysis_api: AnalysisAPI, logger=logging.getLogger(
        __name__), yaml_loader=ruamel.yaml, path_tool=Path):
        self.db = db
        self.lims = lims_api
        self.tb = tb_api
        self.deliver = deliver_api
        self.chanjo = chanjo_api
        self.analysis = analysis_api
        self.LOG = logger
        self.yaml_loader = yaml_loader
        self.path_tool = path_tool

    def create_delivery_report(self, customer_id: str, family_id: str) -> str:
        """Generate the html contents of a delivery report."""
        delivery_data = self._get_delivery_data(customer_id, family_id)
        rendered_report = self._render_delivery_report(delivery_data)
        return rendered_report

    def create_delivery_report_file(self, customer_id: str, family_id: str, file_path:
    Path):
        """Generate a temporary file containing a delivery report."""

        delivery_report = self.create_delivery_report(customer_id=customer_id,
                                                      family_id=family_id)

        delivery_report_file = open(file_path / 'delivery-report.html', 'w')
        delivery_report_file.write(delivery_report)
        delivery_report_file.close()

        return delivery_report_file

    def _get_delivery_data(self, customer_id: str, family_id: str) -> dict:
        """Fetch all data needed to render a delivery report."""

        report_data = dict()
        family_obj = self._get_family_from_status(family_id)
        report_data['family'] = ReportAPI._present_string(family_obj.name)
        report_data['customer'] = customer_id
        report_data['customer_obj'] = self._get_customer_from_status_db(customer_id)
        report_samples = self._fetch_family_samples_from_status_db(family_id)
        report_data['samples'] = report_samples
        report_data['panels'] = self._fetch_panels_from_status_db(family_id)
        self._incorporate_lims_data(report_data)
        self._incorporate_lims_methods(report_samples)
        self._incorporate_delivery_date_from_lims(report_samples)
        self._incorporate_processing_time_from_lims(report_samples)
        self._incorporate_coverage_data(report_samples)
        self._incorporate_trending_data(report_data, family_id)

        report_data['today'] = datetime.today()
        application_data = self._get_application_data_from_status_db(report_samples)
        report_data.update(application_data)
        return report_data

    def _get_family_from_status(self, family_id: str) -> models.Family:
        """Fetch a family object from the status database."""
        return self.db.family(family_id)

    def _incorporate_lims_methods(self, samples: list):
        """Fetch the methods used for preparation, sequencing and delivery of the samples."""

        for sample in samples:
            lims_id = sample['id']
            method_types = ['prep_method', 'sequencing_method', 'delivery_method']
            for method_type in method_types:
                get_method = getattr(self.lims, f"get_{method_type}")
                method_name = get_method(lims_id)
                sample[method_type] = ReportAPI._present_string(method_name)

    def _incorporate_delivery_date_from_lims(self, samples: list):
        """Fetch and add the delivery date from LIMS for each sample."""

        for sample in samples:
            lims_id = sample['id']
            delivery_date = self.lims.get_delivery_date(lims_id)
            sample['delivery_date'] = ReportAPI._present_date(delivery_date)

    def _incorporate_processing_time_from_lims(self, samples: list):
        """Fetch and add the the processing time in days from LIMS for each sample."""

        for sample in samples:
            lims_id = sample['id']
            processing_time = self.lims.get_processing_time(lims_id)
            if processing_time:
                sample['processing_time'] = processing_time.days

    def _get_customer_from_status_db(self, internal_customer_id: str) -> models.Customer:
        """Fetch the customer object from the status database that has the given internal_id."""
        return self.db.Customer.filter_by(internal_id=internal_customer_id).first()

    @staticmethod
    def _render_delivery_report(report_data: dict) -> str:
        """Render and return report data on the report Jinja template."""

        env = Environment(
            loader=PackageLoader('cg', 'meta/report/templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template('report.html')
        template_out = template.render(**report_data)
        return template_out

    def _get_sample_coverage_from_chanjo(self, lims_id: str) -> dict:
        """Get coverage data from Chanjo for a sample."""
        return self.chanjo.sample_coverage(lims_id)

    def _incorporate_trending_data(self, report_data: dict, family_id: str):
        """Incorporate trending data into a set of samples."""
        trending_data = self.analysis.get_latest_data(family_id=family_id)

        mapped_reads_all_samples = trending_data.get('mapped_reads', {})
        duplicates_all_samples = trending_data.get('duplicates', {})
        analysis_sex_all_samples = trending_data.get('analysis_sex', {})

        for sample in report_data['samples']:
            lims_id = sample['id']

            analysis_sex = analysis_sex_all_samples.get(lims_id)
            sample['analysis_sex'] = ReportAPI._present_string(analysis_sex)

            mapped_reads = mapped_reads_all_samples.get(lims_id)
            sample['mapped_reads'] = ReportAPI._present_float_string(mapped_reads, 2)

            duplicates = duplicates_all_samples.get(lims_id)
            sample['duplicates'] = ReportAPI._present_float_string(duplicates, 1)

        report_data['genome_build'] = ReportAPI._present_string(trending_data.get('genome_build'))
        report_data['mip_version'] = ReportAPI._present_string(trending_data.get('mip_version'))

    @staticmethod
    def _present_float_string(float_str: str, precision: int) -> str:
        """Make a float value presentable for the delivery report."""
        if float_str:
            presentable_value = str(round(float(float_str), precision))
        else:
            presentable_value = 'N/A'

        return presentable_value

    @staticmethod
    def _present_string(string: str) -> str:
        """Make a string value presentable for the delivery report."""
        if string and len(string) > 0:
            presentable_value = string
        else:
            presentable_value = 'N/A'

        return presentable_value

    @staticmethod
    def _present_date(a_date: datetime.date) -> str:
        """Make an date value presentable for the delivery report."""
        if a_date:
            presentable_value = str(a_date)
        else:
            presentable_value = 'N/A'

        return presentable_value

    @staticmethod
    def _present_int(integer: int) -> str:
        """Make an integer value presentable for the delivery report."""
        if integer:
            presentable_value = str(integer)
        else:
            presentable_value = 'N/A'

        return presentable_value

    @staticmethod
    def _present_set(a_set: set) -> str:
        """Make a set presentable for the delivery report."""
        if a_set:
            presentable_value = ', '.join(str(s) for s in a_set)
        else:
            presentable_value = 'N/A'

        return presentable_value

    def _incorporate_coverage_data(self, samples: list):
        """Incorporate coverage data from Chanjo for each sample ."""
        for sample in samples:
            lims_id = sample['id']

            sample_coverage = self._get_sample_coverage_from_chanjo(lims_id)

            if sample_coverage:
                target_coverage = sample_coverage.get('mean_coverage')
                sample['target_coverage'] = ReportAPI._present_float_string(target_coverage, 1)
                target_completeness = sample_coverage.get('mean_completeness')
                sample['target_completeness'] = ReportAPI._present_float_string(
                    target_completeness, 2)
            else:
                self.LOG.warning(f'No coverage could be calculated for: {lims_id}')

    def _fetch_family_samples_from_status_db(self, family_id: str) -> list:
        """Incorporate data from the status database for each sample ."""

        delivery_data_samples = list()
        family_samples = self.db.family_samples(family_id)

        for family_sample in family_samples:
            sample = family_sample.sample
            delivery_data_sample = dict()
            delivery_data_sample['id'] = sample.internal_id
            delivery_data_sample['ticket'] = ReportAPI._present_int(sample.ticket_number)
            delivery_data_sample['status'] = ReportAPI._present_string(family_sample.status)

            if sample.reads:
                delivery_data_sample['million_read_pairs'] = round(sample.reads / 2000000, 1)
            else:
                delivery_data_sample['million_read_pairs'] = 'N/A'

            delivery_data_samples.append(delivery_data_sample)

        return delivery_data_samples

    def _get_application_data_from_status_db(self, samples: list) -> dict:
        """Fetch application data including accreditation status for all samples."""
        application_data = dict()
        used_applications = set()

        for sample in samples:
            used_applications.add((sample['application'], sample['application_version']))

        applications = []
        accreditations = []
        for apptag_id, apptag_version in used_applications:

            application_is_accredited = False

            application = self.db.application(tag=apptag_id)

            if application:
                application_is_accredited = application.is_accredited
                applications.append(application)

            accreditations.append(application_is_accredited)

        application_data['application_objs'] = applications
        application_data['accredited'] = all(accreditations)
        return application_data

    def _fetch_panels_from_status_db(self, family_id: str) -> list:
        """fetch data from the status database for each panels ."""
        family = self.db.family(family_id)

        panels = family.panels
        panels = ReportAPI._present_set(panels)

        return panels

    def _incorporate_lims_data(self, report_data: dict):
        """Incorporate data from LIMS for each sample ."""
        for sample in report_data.get('samples'):
            lims_id = sample['id']

            try:
                lims_sample = self.lims.sample(lims_id)
            except requests.exceptions.HTTPError as e:
                lims_sample = dict()
                self.LOG.info(f"could not fetch sample {lims_id} from LIMS: {e}")

            sample['name'] = ReportAPI._present_string(lims_sample.get('name'))
            sample['sex'] = ReportAPI._present_string(lims_sample.get('sex'))
            sample['source'] = ReportAPI._present_string(lims_sample.get('source'))
            sample['application'] = ReportAPI._present_string(lims_sample.get('application'))
            sample['application_version'] = lims_sample.get('application_version')
            sample['received'] = ReportAPI._present_date(lims_sample.get('received'))
