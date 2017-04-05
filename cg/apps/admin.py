# -*- coding: utf-8 -*-
from cgadmin.store import api
from cgadmin.report.core import export_report as export_report_api


class Application(api.AdminDatabase):

    """Admin database API.

    Args:
        config (dict): CLI config object
    """

    def __init__(self, config):
        super(Application, self).__init__(config['cgadmin']['database'])

    def map_apptags(self, apptags):
        """Map application tags with latest versions.

        Args:
            admin_db (sqlservice.SQLClient)
        """
        apptag_map = {}
        for apptag_id in apptags:
            latest_version = self.latest_version(apptag_id)
            apptag_map[apptag_id] = latest_version.version
        return apptag_map

    def customer(self, customer_id):
        """Get a customer record from the database."""
        return self.Customer.filter_by(customer_id=customer_id).first()

    def export_report(self, case_data):
        """Pass-through to the original API function."""
        return export_report_api(self, case_data)
