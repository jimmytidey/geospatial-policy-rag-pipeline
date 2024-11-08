import psycopg2,os
from dotenv import load_dotenv
from psycopg2.extras import DictCursor
from psycopg2 import pool, extras

class Postgres:

    def __init__(self):
      
        DATABASE_URL = os.environ["DATABASE_URL"]
        self.db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL  # Pass the URL as the DSN (Data Source Name)
        )            

    def insert(self, query, params=None):
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)
            
            conn.commit()
            cursor.close()
            self.db_pool.putconn(conn) 

        except psycopg2.Error as e:
            print("Error:", e)

    def query(self, query, params=None):
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor(cursor_factory=DictCursor)

            if params is None:
                cursor.execute(query)
            else:   
                cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            self.db_pool.putconn(conn)
            return results

        except psycopg2.Error as e:
            print("Error:", e)