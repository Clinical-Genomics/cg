# -*- coding: utf-8 -*-
from pymongo import MongoClient

from scout.adapter import MongoAdapter
from scout.export.panel import export_panels

APP_KEY = 'scout'


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
