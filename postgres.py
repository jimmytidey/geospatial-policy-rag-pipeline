import psycopg2,os
class Postgres:

    def __init__(self):
        try:
            DATABASE_URL = os.environ["DATABASE_URL"]
            self.conn = psycopg2.connect(DATABASE_URL, sslmode="require")

        except psycopg2.Error as e:
            print("Error:", e)

    def query(self, query):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            self.conn.close()
            return results

        except psycopg2.Error as e:
            print("Error:", e)

    def insert_text_fragments(self, batch):

        try:
            cursor = self.conn.cursor()
            insert_query = "INSERT INTO text_fragments (plain_text, full_text, metadata, vector, filename, hash) VALUES (%s, to_tsvector('english', %s), %s, %s, %s, %s)"     
            #interpolated_query = cursor.mogrify(insert_query, (text, text, json.dumps(metadata), vector, filename, hash))
            #print("Interpolated SQL query:", interpolated_query.decode("utf-8"))  
            extras.execute_batch(cursor, insert_query, batch)
            self.conn.commit()
            cursor.close()

        except psycopg2.Error as e:
            print("Error:", e)

    def close(self):
        self.conn.close()
