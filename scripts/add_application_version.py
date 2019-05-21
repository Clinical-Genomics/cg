"""Script to load new application versions to status-db"""
import csv
import logging
import sys
from argparse import ArgumentParser
from datetime import datetime

from sqlalchemy import create_engine, MetaData
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)

DESC = """Script to load new application versions to status-db"""

VALID_HEADERS = ['App tag', 'Version', 'Valid from', 'Standard',
                 'Priority', 'Express', 'Research', 'Comment']


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
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table = metadata.tables['application_version']
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

    for row in rows:
        tag = row['App tag']
        query = f'select max(application_version.version), application.tag, application.id \
                from application_version \
                inner join application on application_version.application_id=application.id \
                where application.tag="{tag}"'
        latest_version, app_tag, app_id = engine.execute(query).first()
        if not latest_version:
            latest_version = 0
        if app_tag:
            ins = table.insert().values(
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
                logging.error(error)
    file_handle.close()


def main(file_path, connection_string, sign):
    """Running add_application_version to load application version"""
    add_application_version(file_path, connection_string, sign)


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-f', dest='file_path', required=True,
                        help='Path to csv with apptags.')
    parser.add_argument('-c', dest='connection_string', required=True,
                        help='Connection string to connect with database.')
    parser.add_argument('-s', dest='sign', required=True,
                        help='Signature.')

    args = parser.parse_args()

    main(args.file_path, args.connection_string, args.sign)
