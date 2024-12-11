import os,sys
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))
from postgres import Postgres 

def geo_labels_extract(number_of_records):
    pg = Postgres()

    query = """
        SELECT 
            etc.chunk_id,
			etc.sections,
            etc.text,
            d.lpa,
            d.neighbourhood
        FROM 
            extracted_chunks etc
        JOIN 
            documents d ON etc.document_id = d.document_id
        WHERE 
            etc.chunker = 'sherpa'
            AND (etc.openai_geo_labels IS NULL OR etc.openai_geo_labels = '[]')	
            AND d.is_geocodeable = True
        order by page, block_idx
        LIMIT %s;
    """
    
    # Execute the query, passing number_of_records as the limit
    records = pg.query(query, (number_of_records,))

    return records

def count_records_without_openai_geo_labels():
    pg = Postgres() 
    
    try:
        query = """
            SELECT COUNT(*)
        FROM 
            extracted_chunks etc
        JOIN 
            documents d ON etc.document_id = d.document_id
        WHERE 
            etc.chunker = 'sherpa'
            AND (etc.openai_geo_labels IS NULL OR etc.openai_geo_labels = '[]')
            AND d.is_geocodeable = True;
        """
        result = pg.query(query)
        count = result[0][0]  # Fetch the count
        
        print(f"Number of records without 'openai_labels': {count}")
        return count
    
    except Exception as e:
        print(f"Error: {e}")
        return None
