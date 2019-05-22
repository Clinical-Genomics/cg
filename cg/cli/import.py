"""Cli commands for importing data into the status database"""
import csv
import logging
import sys
from datetime import datetime

import click
from sqlalchemy import create_engine, MetaData
from sqlalchemy.exc import SQLAlchemyError
import xlrd

from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group('set')
@click.pass_context
def import_cmd(context):
    """Import information into the database."""
    context.obj['status'] = Store(context.obj['database'])


@import_cmd.command('application-version')
@click.option('-e', dest='excel_path', required=True,
              help='Path to excel with apptag versions.')
# @click.option('-c', dest='connection_string', required=True,
#               help='Connection string to connect with database.')
@click.option('-s', dest='sign', required=True,
              help='Signature.')
@click.pass_context
def application_version(context, excel_path,  # connecion_string,
                        sign):
    """Running add_application_version to import application version"""
    # add_application_version(file_path, connection_string, sign)
    _add_application_version(context, excel_path, sign)


DESC = """Script to load new application versions to status-db"""

VALID_HEADERS = ['App tag', 'Version', 'Valid from', 'Standard',
                 'Priority', 'Express', 'Research', 'Comment']


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


def _add_application_version(context, excel_path, sign):
    """
    Args:
        :param excel_path:          Path to excel file with headers: 'App tag', 'Valid from',
                                   'Standard', 'Priority', 'Express', 'Research'
        :param sign:               Signature of user running the script
        """

    workbook = xlrd.open_workbook(excel_path)
    version_sheet = workbook.sheet_by_name('')
    raw_versions = _get_relevant_rows(version_sheet)

    for raw_version in raw_versions:
        tag = raw_version['App tag']
        app_tag = context.obj['status'].application(tag).tag
        latest_version = context.obj['status'].latest_version(tag).version or 0
        app_id = context.obj['status'].application(tag).id

        if not app_tag:
            sys.exit('Failed to find app_tag: %s' % app_tag)

        logging.info('adding new version for app tag %s', app_tag)
        context.obj['status'].add_version(
            application_id=app_id,
            version=latest_version + 1,
            valid_from=datetime.strptime(raw_version['Valid from'], '%Y-%m-%d'),
            price_standard=raw_version['Standard'],
            price_priority=raw_version['Priority'],
            price_express=raw_version['Express'],
            price_research=raw_version['Research'],
            comment='Added by %s' % sign,
            created_at=datetime.today()
        )

    context.obj['status'].commit()


def __add_application_version(context, file_path, sign):
    """
    Args:
        :param file_path:          Path to csv file with heathers: 'App tag', 'Valid from',
                                   'Standard', 'Priority', 'Express', 'Research'
        :param connection_string:  'mysql+pymysql://<user>:<password>@<host>:<port>/cg'
        :param sign:               Signature of user running the script
        """

    # TO-DO: we should import from an excel file instead of csv
    #  so that the user has fewer actions to do to perform an import

    try:
        file_handle = open(file_path)
        rows = csv.DictReader(file_handle, delimiter=',')
    except IOError as error:
        sys.exit('Failed read file: %s' % error)

    if not len(set(rows.fieldnames)) == len(rows.fieldnames):
        sys.exit('Headers in file are not unique')

    if not set(rows.fieldnames) < set(VALID_HEADERS):
        sys.exit('Headers in file are not valid. Should contain: %s' % (str(VALID_HEADERS)))

    # check that all applications exist before inserting any prices
    for row in rows:
        tag = row['App tag']
        app_tag = context.obj['status'].application(tag)

        if not app_tag:
            sys.exit('Failed to find app_tag: %s' % app_tag)

    for row in rows:
        tag = row['App tag']
        app_tag = context.obj['status'].application(tag).tag
        latest_version = context.obj['status'].latest_version(tag).version
        app_id = context.obj['status'].application(tag).id

        if not latest_version:
            latest_version = 0

        logging.info('adding new version for app tag %s', app_tag)
        context.obj['status'].add_version(
            application_id=app_id,
            version=latest_version + 1,
            valid_from=datetime.strptime(row['Valid from'], '%Y-%m-%d'),
            price_standard=row['Standard'],
            price_priority=row['Priority'],
            price_express=row['Express'],
            price_research=row['Research'],
            comment='Added by %s' % sign,
            created_at=datetime.today()
        )

    context.obj['status'].commit()
    file_handle.close()


def add_application_version(file_path, connection_string, sign):
    """
    Args:
        :param file_path:          Path to csv file with heathers: 'App tag', 'Valid from',
                                   'Standard', 'Priority', 'Express', 'Research'
        :param connection_string:  'mysql+pymysql://<user>:<password>@<host>:<port>/cg'
        :param sign:               Signature of user running the script
        """

    try:
        engine = create_engine(connection_string)
        connection = engine.connect()
        MetaData().reflect(bind=engine)
    except SQLAlchemyError as error:
        sys.exit('Failed to connect: %s' % error)

    try:
        file_handle = open(file_path)
        rows = csv.DictReader(file_handle, delimiter=',')
    except IOError as error:
        sys.exit('Failed read file: %s' % error)

    if not len(set(rows.fieldnames)) == len(rows.fieldnames):
        sys.exit('Headers in file are not unique')

    if not set(rows.fieldnames) < set(VALID_HEADERS):
        sys.exit('Headers in file are not valid. Should contain: %s' % (str(VALID_HEADERS)))

    # check that all applications exist before inserting any prices
    for row in rows:
        tag = row['App tag']
        query = f'select application.tag \
                from application_version \
                inner join application on application_version.application_id=application.id \
                where application.tag="{tag}"'
        app_tag = engine.execute(query).first()

        if not app_tag:
            sys.exit('Failed to find app_tag: %s' % app_tag)

    for row in rows:
        tag = row['App tag']
        query = f'select max(application_version.version), application.tag, application.id \
                from application_version \
                inner join application on application_version.application_id=application.id \
                where application.tag="{tag}"'
        latest_version, app_tag, app_id = engine.execute(query).first()
        if not latest_version:
            latest_version = 0

        ins = MetaData().tables['application_version'].insert().values(
            application_id=app_id,
            version=latest_version + 1,
            valid_from=datetime.strptime(row['Valid from'], '%Y-%m-%d'),
            price_standard=row['Standard'],
            price_priority=row['Priority'],
            price_express=row['Express'],
            price_research=row['Research'],
            comment='Added by %s' % sign,
            created_at=datetime.today())
        try:
            connection.execute(ins)
            logging.info('adding new version for app tag %s', app_tag)
        except SQLAlchemyError as error:
            sys.exit(error)

    file_handle.close()
