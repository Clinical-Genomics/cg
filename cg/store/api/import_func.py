import logging
from datetime import datetime

import xlrd


def _get_relevant_rows(version_sheet):
    """Get the relevant rows from an price sheet."""
    raw_versions = []
    first_row = True

    for row in version_sheet.get_rows():
        if row[0].value == '':
            break

        if first_row:
            header_row = [cell.value for cell in row]
            first_row = False
        else:
            values = [str(cell.value) for cell in row]
            version_dict = dict(zip(header_row, values))
            raw_versions.append(version_dict)

    return raw_versions


def prices_are_same(integer_price: int, float_price: float):
    return integer_price == int(round(float(float_price)))


def versions_are_same(version_obj: models.ApplicationVersion, raw_version: dict, datemode: int):

    #TODO: test with price fixture and database model
    return version_obj.application.tag == raw_version['App tag'] and \
           version_obj.valid_from == datetime(*xlrd.xldate_as_tuple(float(raw_version['Valid '
                                                                                      'from']),
                                                                    datemode)) and \
            prices_are_same(version_obj.price_standard, raw_version['Standard']) and \
            prices_are_same(version_obj.price_standard, raw_version['Priority']) and \
            prices_are_same(version_obj.price_standard, raw_version['Express']) and \
            prices_are_same(version_obj.price_standard, raw_version['Research'])


def _versions_are_same(first_version_obj, second_version_obj):

    # print(first_version_obj.to_dict(application=False))
    # print(second_version_obj.to_dict(application=False))

    # print(first_version_obj.application.tag, second_version_obj.application.tag)
    # print(first_version_obj.valid_from, second_version_obj.valid_from)
    # print(first_version_obj.price_standard, second_version_obj.price_standard)
    # print(first_version_obj.price_priority, second_version_obj.price_priority)
    # print(first_version_obj.price_express, second_version_obj.price_express)
    # print(first_version_obj.price_research, second_version_obj.price_research)

    return first_version_obj.application.tag == second_version_obj.application.tag and \
           first_version_obj.valid_from == second_version_obj.valid_from and \
           first_version_obj.price_standard == int(round(float(
        second_version_obj.price_standard))) \
           and \
           first_version_obj.price_priority == int(round(float(second_version_obj.price_priority))) and \
           first_version_obj.price_express == int(round(float(second_version_obj.price_express))) and \
           first_version_obj.price_research == int(round(float(second_version_obj.price_research)))


def application_version(store, excel_path, sign):
    """
    Args:
        :param store:               status database store
        :param excel_path:          Path to excel file with headers: 'App tag', 'Valid from',
                                   'Standard', 'Priority', 'Express', 'Research'
        :param sign:               Signature of user running the script
        """

    workbook = xlrd.open_workbook(excel_path)
    version_sheet = workbook.sheet_by_index(0)
    raw_versions = _get_relevant_rows(version_sheet)

    for raw_version in raw_versions:
        tag = raw_version['App tag']
        application_obj = store.application(tag)

        if not application_obj:
            logging.error('Failed to find application! Rolling back transaction. Please manually '
                          'add application: %s' % tag)
            continue
        #   store.rollback()
        #    sys.exit('Failed to find application! Rolling back transaction. Please manually add '
        #             'application: %s' % tag)

        app_tag = application_obj.tag
        latest_version = store.latest_version(tag)

        if versions_are_same(store.latest_version(tag), raw_version, workbook.datemode):
            logging.info('skipping redundant new version for app tag %s', app_tag)
            continue

        logging.info('adding to transaction new version for app tag %s', app_tag)
        new_version = store.add_version(
            application=application_obj,
            version=latest_version.version + 1 if latest_version else 1,
            valid_from=datetime(*xlrd.xldate_as_tuple(float(raw_version['Valid from']),
                                                      workbook.datemode)),
            prices={'standard': raw_version['Standard'],
                    'priority': raw_version['Priority'],
                    'express': raw_version['Express'],
                    'research': raw_version['Research']},
            comment='Added by %s' % sign
        )

        if _versions_are_same(latest_version, new_version):
            logging.info('skipping redundant new version for app tag %s', app_tag)
            store.delete(new_version)

    logging.info('all app tags added successfully to transaction, committing transaction')
    store.commit()
