from sqlalchemy import create_engine, MetaData
import csv
from datetime import datetime
from argparse import ArgumentParser
import logging
import sys

logging.basicConfig(level=logging.INFO)

DESC= """Scrpt to load new application versions to status-db"""

VALID_HEADERS = ['App tag', 'Version', 'Valid from', 'Standard', 'Priority', 'Express', 'Research', 'Comment']

def add_application_version(file_path, conection_string):
    """
    Args:
        file_path:          Path to csv file with heathers: 'App tag', 'Valid from', 'Standard', 
                            'Priority', 'Express', 'Research'
        connection_string: 'mysql+pymysql://<user>:<password>@<hoast>:<port>/cg'
        """
    try:
        engine = create_engine(conection_string)
        connection = engine.connect() 
        metadata = MetaData()
        metadata.reflect(bind=engine)   
        table = metadata.tables['application_version']
    except Exception as e:
        sys.exit(f'Failed to connect: {e}')

    try:
        f = open(file_path)
        rows=csv.DictReader(f, delimiter=',')
    except Exception as e:
        sys.exit(f'Failed read file: {e}')

    if not len(set(rows.fieldnames))==len(rows.fieldnames):
        sys.exit(f'Heades in file are not unique')

    if not set(rows.fieldnames) < set(VALID_HEADERS):
        sys.exit(f'Headers in file are not valid. Should contain the following: {str(VALID_HEADERS)}')
    

    for row in rows:
        tag = row['App tag']
        query = f'select max(application_version.version), application.tag, application.id from application_version inner join application on application_version.application_id=application.id where application.tag="{tag}"'
        latest_version, app_tag, app_id = engine.execute(query).first()
        if app_tag:
            ins = table.insert().values(
                application_id = app_id, 
                version = latest_version + 1, 
                valid_from =datetime.strptime(row['Valid from'], '%Y-%m-%d'),  
                price_standard = row['Standard'], 
                price_priority = row['Priority'], 
                price_express = row['Express'], 
                price_research = row['Research'], 
                created_at = datetime.today())
            try: 
                connection.execute(ins)
                print('hej')
                logging.info(f'adding new version for app tag {app_tag}')
            except Exception as e:
                print('hoj')
                logging.error(e)
    f.close()


def main(args):
    add_application_version(args.file, args.connection_string)


if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('-f', dest = 'file', required=True,
                        help='Path to csv with apptags.')
    parser.add_argument('-c', dest = 'connection_string', required=True,
                        help='Connection string to connect with database.') 
                          
    args = parser.parse_args()

    main(args)     
