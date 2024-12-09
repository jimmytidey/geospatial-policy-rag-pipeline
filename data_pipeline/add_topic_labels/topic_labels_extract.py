import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from postgres import Postgres 

def topic_labels_extract(number_of_records):
    pg = Postgres()

    count_records_without_openai_labels()

    query = """
        SELECT 
            lce.id, 
            lce.cmetadata->>'neighbourhood' AS neighbourhood, 
            lce.cmetadata->>'block_idx' AS block_idx, 
            lce.cmetadata->>'sections' AS sections, 
            lce.cmetadata->>'text' AS text
        FROM 
            langchain_pg_embedding lce
        WHERE 
            NOT (lce.cmetadata ? 'openai_labels')  -- Exclude records with 'openai_labels' in cmetadata
            
            AND lce.cmetadata->>'chunker' = 'sherpa'
        ORDER BY 
            RANDOM()
        LIMIT %s;
    """
    
    records = pg.query(query, (number_of_records,))

    return records


def count_records_without_openai_labels():
    pg = Postgres() 
    
    try:
        query = """
            SELECT COUNT(*)
            FROM langchain_pg_embedding
            WHERE NOT (cmetadata ? 'openai_labels')
            AND cmetadata->>'chunker' = 'sherpa';
        """
        result = pg.query(query)
        count = result[0][0]  # Fetch the count
        
        print(f"Number of records without 'openai_labels': {count}")
        return count
    
    except Exception as e:
        print(f"Error: {e}")
        return None