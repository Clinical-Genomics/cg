# -*- coding: utf-8 -*-
import logging

import pymongo
from pymongo import MongoClient

from scout.adapter import MongoAdapter
from scout.export.panel import export_panels

APP_KEY = 'scout'
log = logging.getLogger(__name__)


def connect(config, app_key=APP_KEY):
    """Connect to the Scout database."""
    client = MongoClient(config[app_key]['host'], config[app_key]['port'])
    db = client[config[app_key]['database']]
    db.authenticate(config[app_key]['username'], config[app_key]['password'])
    return db


def connect_adapter(config):
    """Connect the Scout Mongo adapter."""
    mongo_adapter = MongoAdapter()
    mongo_adapter.connect_to_database(
        database=config['scout']['database'],
        host=config['scout']['host'],
        port=config['scout']['port'],
        username=config['scout']['username'],
        password=config['scout']['password']
    )
    return mongo_adapter


def get_case(db, case_id):
    """Get a case from Scout."""
    return db.case.find_one({'_id': case_id})


def get_reruns(db):
    """Get cases marked to be rerun."""
    return db.case.find({'rerun_requested': True})


def add(config_path):
    """Upload variants for an analysis to the database."""
    pass


def report(scout_db, customer_id, family_id, report_path):
    """Link a delivery report with an existing Scout case."""
    case_obj = scout_db.case(customer_id, family_id)
    if case_obj is None:
        log.error("case not found in database")
        return None

    case_obj[''] = report_path
    updated_case = scout_db.case_collection.find_one_and_update({
        '_id': case_obj['_id']
    }, {
        '$set': {
            'delivery_report': report_path
        }
    }, return_document=pymongo.ReturnDocument.AFTER)
    return updated_case
