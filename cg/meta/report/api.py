# -*- coding: utf-8 -*-
import logging

from datetime import datetime
import ruamel.yaml
from jinja2 import Environment, PackageLoader, select_autoescape
from click import Path

from cg.apps.tb import TrailblazerAPI
from cg.meta.deliver.api import DeliverAPI
from cg.apps.lims import LimsAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


class ReportAPI:

    def __init__(self, db: Store, lims_api: LimsAPI, tb_api: TrailblazerAPI, deliver_api:
    DeliverAPI):
        self.db = db
        self.lims = lims_api
        self.tb = tb_api
        self.deliver = deliver_api

    def collect_delivery_data(self, customer: str, family: str):

        delivery_data = self.lims.family(customer, family)
        delivery_data = self.generate_qc_data(delivery_data)

        # call trailblazer to get trending data
        trending_data = self.get_trending(family=family)

        delivery_data += trending_data

        return delivery_data

    def generate_qc_data(self, case_data):
        """Generate qc data report."""
        delivery_data = dict(case_data)

        delivery_data['today'] = datetime.today()
        delivery_data['customer'] = self.db.Customer.filter_by(internal_id=case_data[
            'customer']).first()
        used_applications = set()

        for sample in delivery_data['samples']:

            used_applications.add((sample['application'], sample['application_version']))
            sample['project'] = sample['project'].split()[0]
            lims_id = sample['id']

            delivery_date = self.lims.get_delivery_date(lims_id)
            if delivery_date:
                sample['delivery_date'] = delivery_date

                processing_time = self.lims.get_processing_time(lims_id)
                if processing_time:
                    sample['processing_time'] = processing_time.days

            # figure out methods used
            method_types = ['prep_method', 'sequencing_method', 'delivery_method']
            for method_type in method_types:
                get_method = getattr(self.lims, f"get_{method_type}")
                method_name = get_method(lims_id)
                if method_name:
                    # sample['methods'].append(method_name)
                    sample[method_type] = method_name

        versions = []
        applications = []

        for apptag_id, apptag_version in used_applications:

            application = self.db.Application.filter_by(tag=apptag_id).first()
            application_id = application.id
            is_accredited = application.is_accredited
            version = self.db.ApplicationVersion \
                .filter_by(application_id=application_id, version=apptag_version).first()

            if version:
                versions.append(version)

            if application:
                applications.append(application)

        delivery_data['applications'] = applications
        delivery_data['accredited'] = is_accredited
        return delivery_data

    @staticmethod
    def render_qc_report(qc_data):
        env = Environment(
            loader=PackageLoader('cg', 'meta/report/templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        print("2.9")
        template = env.get_template('report.html')
        print("2.10")
        template_out = template.render(**qc_data)
        print("2.11")
        return template_out

    def _get_latest_raw_file(self, family: str, tag: str) -> str:
        analysis_file_path = self.deliver.get_post_analysis_files(family=family,
                                                                  version=False, tag=tag).first()
        analysis_file_raw = self._open_file(analysis_file_path)
        return analysis_file_raw

    @staticmethod
    def _open_file(file_path):
        return ruamel.yaml.safe_load(Path(file_path).open())

    def get_trending(self, family: str) -> dict:
        """Get the sample info path for an analysis."""

        # mip_config_raw (dict): raw YAML input from MIP analysis config file
        mip_config_raw = self._get_latest_raw_file(family=family, tag='mip-config')

        # qcmetrics_raw (dict): raw YAML input from MIP analysis qc metric file
        qcmetrics_raw = self._get_latest_raw_file(family=family, tag='qcmetrics')

        # sampleinfo_raw (dict): raw YAML input from MIP analysis qc sample info file
        sampleinfo_raw = self._get_latest_raw_file(family=family, tag='sampleinfo')

        trending = self.tb.get_trending(mip_config_raw=mip_config_raw,
                                        qcmetrics_raw=qcmetrics_raw,
                                        sampleinfo_raw=sampleinfo_raw)

        return trending
