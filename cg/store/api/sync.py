"""Sync functionality"""

import logging
import sys
from datetime import datetime

import xlrd
from cg.store import Store


def sync_applications(store: Store, excel_path: str, prep_category: str, sign: str, sheet_name:
                      str, tag_column: int, activate: bool, inactivate: bool):
    """
    Syncs all applications from the specified excel file
    Args:
        :param inactivate:          Inactivate tags not found in the orderform
        :param activate:            Activate archived tags found in the orderform
        :param sheet_name:          (optional) name of sheet where the applications can be found
        :param tag_column:          (optional) zero-based column where the application tags can be
        found
        :param prep_category:       prep_category to sync
        :param store:               status database store
        :param excel_path:          Path to orderform excel file
        :param sign:                Signature of user running the script
        """

    orderform_application_tags = []

    for raw_row in get_raw_data_from_xl(excel_path, sheet_name, tag_column):
        tag = get_tag_from_raw_application(raw_row, tag_column)
        logging.info('Found: %s in orderform', tag)
        orderform_application_tags.append(tag)

    if not orderform_application_tags:
        logging.error('No applications found in column %s (zero-based), exiting', tag_column)
        sys.exit()

    for orderform_application_tag in orderform_application_tags:
        application_obj = store.application(tag=orderform_application_tag)

        if not application_obj:
            logging.error(f'Application %s was not found', orderform_application_tag)
            sys.exit()

        if application_obj.prep_category != prep_category:
            logging.error('%s prep_category, expected: %s was: %s', orderform_application_tag,
                          prep_category, application_obj.prep_category)
            sys.exit()

        if application_obj.is_archived:
            if activate:
                application_obj.comment = \
                    f'{application_obj.comment}\n{str(datetime.now())[:-10]}' \
                    f'Application un-archived by {sign}'
                application_obj.is_archived = False
                logging.info('Un-archiving %s', application_obj)
            else:
                logging.warning('%s is marked as archived but is used in the orderform, consider '
                                'activating it', application_obj)
        else:
            logging.info('%s is already active, no need to activate it', application_obj)

    all_active_apps_for_category = store.applications(category=prep_category,
                                                      archived=False)

    for active_application in all_active_apps_for_category:
        if active_application.tag not in orderform_application_tags:
            if inactivate:
                active_application.is_archived = True
                active_application.comment = f'{active_application.comment}' \
                    f'\n{str(datetime.now())[:-10]} ' \
                    f'Application archived by {sign}'
                logging.info('Archiving %s', active_application)
            else:
                logging.warning('%s is marked as active but is not used in the orderform, '
                                'consider archiving it', active_application)
        else:
            logging.info('%s was found in orderform tags, no need to archive it',
                         active_application)

    if not activate and not inactivate:
        logging.info('no change mode requested, rolling back transaction')
        store.rollback()
    else:
        logging.info('all applications successfully synced, committing transaction')
        store.commit()


def get_tag_from_raw_application(raw_data, column: int):
    """Gets the application tag from a raw xl application record"""
    return raw_data[column]


def get_raw_data_from_xl(excel_path, sheet_name, tag_column):
    """Get raw data from the xl file"""
    workbook = get_workbook_from_xl(excel_path)
    data_sheet = workbook.sheet_by_name(sheet_name)
    return get_raw_data_from_xlsheet(data_sheet, tag_column)


def get_workbook_from_xl(excel_path):
    """Get the workbook from the xl file"""
    return xlrd.open_workbook(excel_path)


def get_datemode_from_xl(excel_path):
    """"Returns the datemode of of the workbook in the specified xl"""
    workbook = xlrd.open_workbook(excel_path)
    return workbook.datemode


def no_more_applications(row, tag_column):
    """Returns if there are no more app-tags found"""
    return get_tag_from_raw_application(row, tag_column).value == ''


def get_raw_data_from_xlsheet(version_sheet, tag_column):
    """Get the relevant rows from an price sheet."""
    raw_data = []

    for row in version_sheet.get_rows():
        if no_more_applications(row, tag_column):
            break

        values = [str(cell.value) for cell in row]
        raw_data.append(values)

    return raw_data
