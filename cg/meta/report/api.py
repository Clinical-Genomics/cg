# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import requests
import ruamel.yaml
from cg.meta.report.status_helper import StatusHelper
from jinja2 import Environment, PackageLoader, select_autoescape
from pathlib import Path

from cg.apps.coverage import ChanjoAPI
from cg.apps.lims import LimsAPI
from cg.store import Store, models
from cg.meta.analysis import AnalysisAPI
from cg.meta.report.presenter import Presenter
from cg.meta.report.sample_calculator import SampleCalculator
from cg.apps.scoutapi import ScoutAPI


class ReportAPI:

    def __init__(self, db: Store, lims_api: LimsAPI, chanjo_api: ChanjoAPI, analysis_api:
                 AnalysisAPI, scout_api: ScoutAPI, logger=logging.getLogger(__name__),
                 yaml_loader=ruamel.yaml, path_tool=Path):

        self.db = db
        self.lims = lims_api
        self.chanjo = chanjo_api
        self.analysis = analysis_api
        self.LOG = logger
        self.yaml_loader = yaml_loader
        self.path_tool = path_tool
        self.scout = scout_api

    def create_delivery_report(self, family_id: str) -> str:
        """Generate the html contents of a delivery report."""
        delivery_data = self._get_delivery_data(family_id)
        rendered_report = self._render_delivery_report(delivery_data)
        return rendered_report

    def create_delivery_report_file(self, family_id: str, file_path: Path):
        """Generate a temporary file containing a delivery report."""

        delivery_report = self.create_delivery_report(family_id=family_id)

        file_path.mkdir(parents=True, exist_ok=True)
        delivery_report_file = open(file_path / 'delivery-report.html', 'w')
        delivery_report_file.write(delivery_report)
        delivery_report_file.close()

        return delivery_report_file

    def _get_delivery_data(self, family_id: str) -> dict:
        """Fetch all data needed to render a delivery report."""

        report_data = dict()
        family_obj = self._get_family_from_status(family_id)
        analysis_obj = family_obj.analyses[0] if family_obj.analyses else None

        report_data['family'] = Presenter.process_string(family_obj.name)
        report_data['customer'] = family_obj.customer_id

        report_data['report_version'] = Presenter.process_int(StatusHelper.get_report_version(
            analysis_obj))
        report_data['previous_report_version'] = Presenter.process_int(
            StatusHelper.get_previous_report_version(analysis_obj))

        report_data['customer_obj'] = family_obj.customer
        report_samples = self._fetch_family_samples_from_status_db(family_id)
        report_data['samples'] = report_samples
        panels = self._fetch_panels_from_status_db(family_id)
        report_data['panels'] = Presenter.process_list(panels)
        self._incorporate_lims_data(report_data)
        self._incorporate_lims_methods(report_samples)
        self._incorporate_coverage_data(report_samples, panels)
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
                sample[method_type] = Presenter.process_string(method_name)

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

    def _get_sample_coverage_from_chanjo(self, lims_id: str, genes: list) -> dict:

        """Get coverage data from Chanjo for a sample."""
        return self.chanjo.sample_coverage(lims_id, genes)

    def _incorporate_trending_data(self, report_data: dict, family_id: str):
        """Incorporate trending data into a set of samples."""
        trending_data = self.analysis.get_latest_metadata(family_id=family_id)

        mapped_reads_all_samples = trending_data.get('mapped_reads', {})
        duplicates_all_samples = trending_data.get('duplicates', {})
        analysis_sex_all_samples = trending_data.get('analysis_sex', {})

        for sample in report_data['samples']:
            lims_id = sample['id']

            analysis_sex = analysis_sex_all_samples.get(lims_id)
            sample['analysis_sex'] = Presenter.process_string(analysis_sex)

            mapped_reads = mapped_reads_all_samples.get(lims_id)
            sample['mapped_reads'] = Presenter.process_float_string(mapped_reads, 2)

            duplicates = duplicates_all_samples.get(lims_id)
            sample['duplicates'] = Presenter.process_float_string(duplicates, 1)

        report_data['genome_build'] = Presenter.process_string(trending_data.get('genome_build'))
        report_data['mip_version'] = Presenter.process_string(trending_data.get('mip_version'))

    def _incorporate_coverage_data(self, samples: list, panels: list):
        """Incorporate coverage data from Chanjo for each sample ."""

        genes = self._get_genes_from_scout(panels)

        for sample in samples:
            lims_id = sample['id']

            sample_coverage = self._get_sample_coverage_from_chanjo(lims_id, genes)

            if sample_coverage:
                target_coverage = sample_coverage.get('mean_coverage')
                sample['target_coverage'] = Presenter.process_float_string(target_coverage, 1)
                target_completeness = sample_coverage.get('mean_completeness')
                sample['target_completeness'] = Presenter.process_float_string(
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
            delivery_data_sample['ticket'] = Presenter.process_int(sample.ticket_number)
            delivery_data_sample['status'] = Presenter.process_string(family_sample.status)
            delivery_data_sample['received'] = Presenter.process_datetime(sample.received_at)
            delivery_data_sample['prep_date'] = Presenter.process_datetime(sample.prepared_at)
            delivery_data_sample['sequencing_date'] = Presenter.process_datetime(
                sample.sequenced_at)
            delivery_data_sample['delivery_date'] = Presenter.process_datetime(sample.delivered_at)
            delivery_data_sample['processing_time'] = Presenter.process_int(
                SampleCalculator.calculate_processing_days(sample))
            delivery_data_sample['order_date'] = Presenter.process_datetime(sample.ordered_at)

            delivery_data_sample['million_read_pairs'] = Presenter.process_int(round(sample.reads
                                                                                     / 2000000,
                                                                                     1) if
                                                                               sample.reads else
                                                                               None)

            delivery_data_sample['capture_kit'] = Presenter.process_string(sample.capture_kit)
            delivery_data_sample['bioinformatic_analysis'] = Presenter.process_string(
                sample.data_analysis)

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

            sample['name'] = Presenter.process_string(lims_sample.get('name'))
            sample['sex'] = Presenter.process_string(lims_sample.get('sex'))
            sample['source'] = Presenter.process_string(lims_sample.get('source'))
            sample['application'] = Presenter.process_string(lims_sample.get('application'))
            sample['application_version'] = lims_sample.get('application_version')

    def _get_genes_from_scout(self, panels: list) -> list:
        panel_genes = list()

        for panel in panels:
            panel_genes.extend(self.scout.get_genes(panel))

        panel_gene_ids = [gene.get('hgnc_id') for gene in panel_genes]

        return panel_gene_ids
