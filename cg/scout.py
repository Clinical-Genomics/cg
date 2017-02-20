# -*- coding: utf-8 -*-
from pymongo import MongoClient

APP_KEY = 'scout'


def connect(config, app_key=APP_KEY):
    """Connect to the Scout database."""
    client = MongoClient(config[app_key]['host'], config[app_key]['port'])
    db = client[config[app_key]['database']]
    db.authenticate(config[app_key]['username'], config[app_key]['password'])
    return db


def get_case(db, case_id):
    """Get a case from Scout."""
    return db.case.find_one({'_id': case_id})


def get_reruns(db):
    """Get cases marked to be rerun."""
    return db.case.find({'rerun_requested': True})
