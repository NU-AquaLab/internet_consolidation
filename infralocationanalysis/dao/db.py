import logging
import psycopg2
from psycopg2 import Error


class Database:
    __instance = None

    @staticmethod
    def get_instance():
        if Database.__instance is None:
            Database()
        return Database.__instance

    def __init__(self):
        if Database.__instance is not None:
            raise Exception("Database connection already exists!")
        else:
            try:
                self.connection = psycopg2.connect(
                    database="aqualab",
                    user="postgres",
                    password="AquaLab0205",
                    host="database-2.cucymth0owxk.us-east-1.rds.amazonaws.com",
                    port="5432"
                )
                self.cursor = self.connection.cursor()
                Database.__instance = self
                logging.info("Database connection successful!")
            except (Exception, Error) as e:
                logging.error("Error connecting to the database:", e)

    def close_connection(self):
        self.connection.close()
        logging.info("Database connection closed.")
