import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres 

def geo_labels_extract(number_of_records):
    pg = Postgres()

    query = """
        SELECT id as "id", cmetadata->>'sections' as "title", cmetadata->>'text' as "text"
        FROM langchain_pg_embedding
        WHERE NOT (cmetadata ? 'openai_geo_labels') 
        AND cmetadata->>'experiment' = 'leeds'
        LIMIT %s;
    """
    
    # Execute the query, passing number_of_records as the limit
    records = pg.query(query, (number_of_records,))

    return records

