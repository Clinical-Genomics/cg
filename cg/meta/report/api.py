# -*- coding: utf-8 -*-
import logging

from datetime import datetime
from jinja2 import Environment, PackageLoader, select_autoescape

from cg.apps import lims
from cg.store import Store

LOG = logging.getLogger(__name__)


class ReportAPI:

    def __init__(self, db: Store, lims_api: lims.LimsAPI):
        self.db = db
        self.lims = lims_api

    def generate_qc_data(self, case_data):
        """Generate qc data report."""
        delivery_data = dict(case_data)

        delivery_data['today'] = datetime.today().date()
        print(delivery_data['today'])
        delivery_data['customer'] = self.db.Customer.filter_by(internal_id=case_data[
            'customer']).first()
        used_applications = set()

        for sample in delivery_data['samples']:
            used_applications.add((sample['app_tag'], sample['app_tag_version']))
            sample['project'] = sample['project'].split()[0]

            lims_id = sample['internal_id']

            if all(sample.get(date_key) for date_key in ['received_at', 'delivery_date']):

                processing_time = self.lims.get_processing_time(lims_id)
                sample['processing_time'] = processing_time.days

            # figure out methods used
            method_types = ['prep', 'sequencing', 'delivery']
            for method_type in method_types:
                get_method = getattr(self.lims, f"get_{method_type}method")
                method_name = get_method(sample['internal_id'])
                if method_name:
                    sample['methods'].append(method_name)
                    # sample[method_type] = method_obj

        versions = []

        for apptag_id, apptag_version in used_applications:

            application = self.db.Application.filter_by(tag=apptag_id).first()
            print(self.db.Application.filter_by(is_accredited=False).first())
            application_id = application.id
            is_accredited = application.is_accredited
            version = self.db.ApplicationVersion\
                .filter_by(application_id=application_id, version=apptag_version).first()

            if version:
                versions.append(version)

        delivery_data['apptags'] = versions
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
        template_out = template.render(**qc_data)
        print("2.10")
        return template_out
