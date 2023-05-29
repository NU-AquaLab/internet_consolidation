import os, sys
import logging
import datetime
from psycopg2 import Error

current = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current)

from db import Database


def insert_table_ca_analysis(aggregated_results, current_year):
    db = Database.get_instance()
    if db is None:
        logging.warning("cannot connect to dao")
        return -1
    cnx = db.connection
    cursor = db.cursor

    for country_code, values in aggregated_results.items():
        # construct insertion clause
        add_ca_analysis_record = "INSERT INTO ca_analysis (country_code, ocsp, https, " \
                                 "third, critically_dependent, most_popular_ca, create_time, " \
                                 "update_time, gen_year, consolidation) " \
                                 "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (country_code, gen_year) " \
                                 "DO UPDATE SET ocsp = EXCLUDED.ocsp, https = EXCLUDED.https," \
                                 "third = EXCLUDED.third, " \
                                 "critically_dependent = EXCLUDED.critically_dependent," \
                                 "most_popular_ca = EXCLUDED.most_popular_ca, " \
                                 "update_time = EXCLUDED.update_time, consolidation = EXCLUDED.consolidation"

        data_ca_record = (
            country_code, values['OCSP'], values['HTTPS'], values['third'], values['criticallyDependent'],
            values['mostpopularCA'], datetime.datetime.now(), datetime.datetime.now(),
            current_year, values['consolidation'])
        try:
            cursor.execute(add_ca_analysis_record, data_ca_record)
        except (Exception, Error) as err:
            logging.warning("execute error: ", err, " with ca record", data_ca_record)
            continue
    try:
        cnx.commit()
    except (Exception, Error) as err:
        logging.warning("Something is wrong with your user name or password", err)
        return -1

    cursor.close()
    cnx.close()
    return


def get_ca_record_by_country_code_website(cnx, country_code, website):
    if cnx is None:
        logging.warning("cannot connect to dao")
        return -1
    cursor = cnx.cursor()

    query = ("SELECT * FROM ca "
             "WHERE country_code = %s and website_name = %s")

    cursor.execute(query, (country_code, website))
    records = cursor.fetchmany(1000)
    return records


def get_ca_record_by_country_code(cnx, country_code):
    if cnx is None:
        logging.warning("cannot connect to dao")
        return -1
    cursor = cnx.cursor()

    query = ("SELECT * FROM ca "
             "WHERE country_code = %s")

    param = (country_code,)

    cursor.execute(query, param)
    records = cursor.fetchmany(1000)
    return records


if __name__ == '__main__':
    cnx = init_db()
    cursor = cnx.cursor()
    cursor.execute("select * from ca")
    for i in cursor:
        print(i)
