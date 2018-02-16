# -*- coding: utf-8 -*-
import logging

from datetime import datetime

from cg.apps.tb import TrailblazerAPI
from jinja2 import Environment, PackageLoader, select_autoescape

from cg.apps.lims import LimsAPI
from cg.store import Store

LOG = logging.getLogger(__name__)


class ReportAPI:

    def __init__(self, db: Store, lims_api: LimsAPI, tb_api: TrailblazerAPI):
        self.db = db
        self.lims = lims_api
        self.tb = tb_api

    def collect_delivery_data(self, customer: str, family:str):

        delivery_data = self.lims.family(customer, family)
        delivery_data = self.generate_qc_data(delivery_data)
        # call trailblazer to get qc data
        #tb_data = self.tb.get_sampleinfo()


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
            version = self.db.ApplicationVersion\
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
