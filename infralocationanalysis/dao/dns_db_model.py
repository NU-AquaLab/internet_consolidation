import os, sys
import logging
import datetime
from psycopg2 import Error

current = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current)

from db import Database


def insert_table_dns_analysis(aggregated_results, current_year):
    db = Database.get_instance()
    if db is None:
        logging.warning("cannot connect to dao")
        return -1
    cnx = db.connection
    cursor = db.cursor

    for country_code, values in aggregated_results.items():
        # construct insertion clause
        add_dns_analysis_record = "INSERT INTO dns_analysis (country_code, third_party_reliance, third_private, " \
                                  "redundant, critically_dependant, create_time, update_time, " \
                                  "gen_year, consolidation) " \
                                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) " \
                                  "ON CONFLICT (country_code, gen_year)" \
                                  "DO UPDATE SET third_party_reliance = EXCLUDED.third_party_reliance, " \
                                  "third_private = EXCLUDED.third_private, " \
                                  "redundant = EXCLUDED.redundant, " \
                                  "critically_dependant = EXCLUDED.critically_dependant, " \
                                  "update_time = EXCLUDED.update_time, consolidation = EXCLUDED.consolidation"

        data_dns_analysis_record = (
            country_code, values['3rdPartyReliance'], values['3rdndPrivate'], values['redundant'],
            values['criticallyDependant'], datetime.datetime.now(), datetime.datetime.now(), current_year,
            values['consolidation'])
        try:
            cursor.execute(add_dns_analysis_record, data_dns_analysis_record)
        except (Exception, Error) as err:
            logging.warning("execute error: ", err, " with dns analysis record", data_dns_analysis_record)
            continue
    try:
        cnx.commit()
    except (Exception, Error) as err:
        logging.warning("Something is wrong with your user name or password", err)
        return -1

    return cursor.lastrowid


def get_dns_record_by_country_code_website(cnx, country_code, website):
    if cnx is None:
        logging.warning("cannot connect to dao")
        return -1
    cursor = cnx.cursor()

    query = ("SELECT * FROM dns "
             "WHERE country_code = %s and website_name = %s")

    cursor.execute(query, (country_code, website))
    records = cursor.fetchmany(1000)
    return records


def get_dns_record_by_country_code(cnx, country_code):
    if cnx is None:
        logging.warning("cannot connect to dao")
        return -1
    cursor = cnx.cursor()

    query = ("SELECT * FROM dns "
             "WHERE country_code = %s")

    param = (country_code,)

    cursor.execute(query, param)
    records = cursor.fetchmany(500)
    return records


if __name__ == '__main__':
    cnx = Database.get_instance()
    cursor = cnx.cursor()
    cursor.execute("select * from dns_analysis limit 10")
    for i in cursor:
        print(i)
