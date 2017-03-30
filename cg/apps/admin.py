# -*- coding: utf-8 -*-
from cgadmin.store import api
from cgadmin.report.core import export_report


def connect(config):
    """Connect to the admin database."""
    admin_db = api.connect(config['cgadmin']['database'])
    return admin_db


def map_apptags(admin_db, apptags):
    """Map application tags with latest versions."""
    apptag_map = {}
    for apptag_id in apptags:
        latest_version = api.latest_version(admin_db, apptag_id)
        apptag_map[apptag_id] = latest_version.version
    return apptag_map


def customer(admin_db, customer_id):
    """Get a customer record from the database."""
    return admin_db.Customer.filter_by(customer_id=customer_id).first()
