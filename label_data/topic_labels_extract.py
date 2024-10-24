import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres 

def topic_labels_extract(number_of_records):
    pg = Postgres()

    query = """
        SELECT id, cmetadata->>'neighbourhood' as neighbourhood, cmetadata->>'block_idx' as block_idx, cmetadata->>'sections' as sections, cmetadata->>'text' as text
        FROM langchain_pg_embedding
        WHERE NOT (cmetadata ? 'openai_labels') 
        AND cmetadata->>'experiment' = 'leeds'
        AND cmetadata->>'chunker' = 'sherpa'
        ORDER BY RANDOM()
        LIMIT %s;
    """
    
    records = pg.query(query, (number_of_records,))

    return records