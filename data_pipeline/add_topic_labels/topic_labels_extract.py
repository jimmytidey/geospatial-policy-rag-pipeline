import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from postgres import Postgres 

def topic_labels_extract(number_of_records):
    pg = Postgres()

    # count_records_without_openai_labels()

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
            AND (etc.openai_topic_labels IS NULL OR etc.openai_topic_labels = '[]')	
        order by page, block_idx
        LIMIT %s;
    """
    
    records = pg.query(query, (number_of_records,))

    return records


def count_records_without_openai_labels():
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
            AND (etc.openai_topic_labels IS NULL OR etc.openai_topic_labels = '[]');
        """
        result = pg.query(query)
        count = result[0][0]  # Fetch the count
        
        print(f"Number of records without 'openai_topic_labels': {count}")
        return count
    
    except Exception as e:
        print(f"Error: {e}")
        return None