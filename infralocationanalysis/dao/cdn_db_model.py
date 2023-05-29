import os, sys
import logging
import datetime
from psycopg2 import Error

current = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current)

from db import Database


def insert_table_cdn_analysis(aggregated_results, current_year):
    db = Database.get_instance()
    if db is None:
        logging.warning("cannot connect to dao")
        return

    cnx = db.connection
    cursor = db.cursor

    for country_code, values in aggregated_results.items():
        # construct insertion clause
        add_cdn_analysis_record = "INSERT INTO cdn_analysis (country_code, third_party_reliance, critical_dependency," \
                                 "redundant, multiple_third_party, third_private, create_time, update_time, " \
                                 "gen_year, consolidation) " \
                                 "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (country_code, gen_year) " \
                                 "DO UPDATE SET third_party_reliance = EXCLUDED.third_party_reliance, " \
                                 "critical_dependency = EXCLUDED.critical_dependency," \
                                 "redundant = EXCLUDED.redundant, " \
                                 "multiple_third_party = EXCLUDED.multiple_third_party," \
                                 "third_private = EXCLUDED.third_private, " \
                                 "update_time = EXCLUDED.update_time, " \
                                 "consolidation = EXCLUDED.consolidation"

        data_cdn_record = (
            country_code, values['ThirdParty'], values['critical_dependency'], values['redundant'],
            values['multipleThirdParty'], values['thirdndPrivate'],
            datetime.datetime.now(), datetime.datetime.now(),
            current_year, values['consolidation'])
        try:
            cursor.execute(add_cdn_analysis_record, data_cdn_record)
        except (Exception, Error) as err:
            logging.warning("execute error: ", err, " with cdn record", data_cdn_record)
            continue
    try:
        cnx.commit()
    except (Exception, Error) as err:
        logging.warning("Something is wrong with sql", err)

    cursor.close()
    cnx.close()
    return


def get_cdn_record_by_country_code_website(cnx, country_code, website):
    if cnx is None:
        logging.warning("cannot connect to dao")
        return -1
    cursor = cnx.cursor()

    query = ("SELECT * FROM cdn "
             "WHERE country_code = %s and website_name = %s")

    cursor.execute(query, (country_code, website))
    records = cursor.fetchmany(1000)
    return records


def get_cdn_record_by_country_code(cnx, country_code):
    if cnx is None:
        logging.warning("cannot connect to dao")
        return -1
    cursor = cnx.cursor()

    query = ("SELECT * FROM cdn "
             "WHERE country_code = %s")

    param = (country_code,)

    cursor.execute(query, param)
    records = cursor.fetchmany(500)
    return records


if __name__ == '__main__':
    cnx = init_db()
    cursor = cnx.cursor()
    cursor.execute("select * from cdn")
    for i in cursor:
        print(i)
    cnx.close()
