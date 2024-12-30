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

    def create_conn(self):
        conn = self.db_pool.getconn()
        return conn

    def insert(self, query, params=None):
       
        try:
            # Get a connection from the pool
            conn = self.db_pool.getconn()
            cursor = conn.cursor()
            
            # Execute the query
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)
            
            # Commit the transaction
            conn.commit()
        
        except psycopg2.Error as e:
            # Print detailed error message
            print(f"Database error: {e.pgerror}")
            print(f"SQL state: {e.pgcode}")
            print(f"Query: {query}")
            if params:
                print(f"Parameters: {params}")
        
        finally:
            # Ensure the cursor and connection are closed or returned to the pool
            if cursor:
                cursor.close()
            if conn:
                self.db_pool.putconn(conn)
            

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
    
    def return_connection(self):
        conn = self.db_pool.getconn()
        return conn
