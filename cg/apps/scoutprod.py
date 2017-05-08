# -*- coding: utf-8 -*-
import logging

import pymongo
from scout.adapter.mongo import MongoAdapter
from scout.adapter.client import get_connection
from scout.export.panel import export_panels
from scout.load import load_scout

log = logging.getLogger(__name__)


def connect(config, app_key='scout'):
    """Connect to the Scout database."""
    uri = "mongodb://{username}:{password}@{host}:{port}/{database}".format(
        username=config[app_key]['username'],
        password=config[app_key]['password'],
        host=config[app_key]['host'],
        port=config[app_key]['port'],
        database=config[app_key]['database'],
    )
    client = get_connection(uri=uri)
    database = client[config[app_key]['database']]
    mongo_adapter = MongoAdapter(database)
    return mongo_adapter


def get_reruns(adapter):
    """Get cases marked to be rerun."""
    return adapter.case_collection.find({'rerun_requested': True})


def add(scout_db, config_data, threshold=5, force=False):
    """Upload variants for an analysis to the database."""
    config_data['rank_score_threshold'] = threshold
    existing_case = scout_db.case(institute_id=config_data['owner'],
                                  display_name=config_data['family'])
    if existing_case:
        if force or config_data['analysis_date'] > existing_case['analysis_date']:
            log.info("Updating existing Scout case")
            load_scout(scout_db, config_data, update=True)
        else:
            existing_date = existing_case['analysis_date'].date()
            log.warning("Analysis of case already added: %s", existing_date)
    else:
        log.info("Adding new case to Scout")
        load_scout(scout_db, config_data)


def report(scout_db, customer_id, family_id, report_path):
    """Link a delivery report with an existing Scout case."""
    case_obj = scout_db.case(institute_id=customer_id, display_name=family_id)
    if case_obj is None:
        log.error("case not found in database")
        return None

    updated_case = scout_db.case_collection.find_one_and_update(
        {'_id': case_obj['_id']},
        {'$set': {'delivery_report': report_path}},
        return_document=pymongo.ReturnDocument.AFTER
    )
    return updated_case
