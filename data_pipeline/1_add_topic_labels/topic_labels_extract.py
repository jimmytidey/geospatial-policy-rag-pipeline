import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            AND lce.cmetadata->>'experiment' = 'leeds'
            AND lce.cmetadata->>'chunker' = 'sherpa'
            -- Exclude records where a corresponding record in 'locations' has labels already
            AND NOT EXISTS (
                SELECT 1
                FROM locations loc
                WHERE loc.chunk_id = lce.id
                AND loc.openai_labels IS NOT NULL  -- Ensure labels are already set
            )
        ORDER BY 
            RANDOM()
        LIMIT %s;
    """
    
    records = pg.query(query, (number_of_records,))

    return records


def count_records_without_openai_labels():
    pg = Postgres()  # Assuming you have a connection to the database
    
    try:
        with pg.conn.cursor() as cursor:
            # Execute the SQL query to count the records without 'openai_labels'
            query = """
                SELECT COUNT(*)
                FROM langchain_pg_embedding
                WHERE NOT (cmetadata ? 'openai_labels')
                AND cmetadata->>'experiment' = 'leeds'
                AND cmetadata->>'chunker' = 'sherpa';
            """
            cursor.execute(query)
            count = cursor.fetchone()[0]  # Fetch the count
            
            print(f"Number of records without 'openai_labels': {count}")
            return count
    
    except Exception as e:
        print(f"Error: {e}")
        return None