import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres 

def geo_labels_extract(number_of_records):
    pg = Postgres()

    count_records_without_openai_geo_labels()

    query = """
        SELECT id as "id", cmetadata->>'sections' as "title", cmetadata->>'text' as "text"
        FROM langchain_pg_embedding
        WHERE NOT (cmetadata ? 'openai_geo_labels') 
        AND cmetadata->>'experiment' = 'leeds'
        AND cmetadata->>'chunker' = 'sherpa'
        LIMIT %s;
    """    
    
    # Execute the query, passing number_of_records as the limit
    records = pg.query(query, (number_of_records,))

    return records


def count_records_without_openai_geo_labels():
    pg = Postgres() 
    
    try:
        with pg.conn.cursor() as cursor:
            query = """
                SELECT COUNT(*)
                FROM langchain_pg_embedding
                WHERE NOT (cmetadata ? 'openai_geo_labels')
                AND cmetadata->>'experiment' = 'leeds'
                AND cmetadata->>'chunker' = 'sherpa';
            """
            cursor.execute(query)
            count = cursor.fetchone()[0]  # Fetch the count
            
            print(f"Number of records without 'openai_geo_labels': {count}")
            return count
    
    except Exception as e:
        print(f"Error: {e}")
        return None
