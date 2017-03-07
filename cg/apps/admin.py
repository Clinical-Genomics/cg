# -*- coding: utf-8 -*-
from cgadmin.store import api


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
