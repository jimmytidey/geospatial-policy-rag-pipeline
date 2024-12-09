import psycopg2, sys,os, json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres 


def topic_labels_load(chunk_id, labels, ):
    """
    Adds an array of labels to the 'labels' key in the cmetadata JSON column for a given record.
    If the 'labels' key does not exist, it will create it and add the new labels.

    :param record_id: The unique id of the record (assumed to be the primary key)
    :param labels: A list of labels (Python array) to add
    """

    pg=Postgres()
    
    try:       
        # Convert the Python list to a JSON array string
        labels_json = json.dumps(labels)
        
        # Update the cmetadata JSON field by creating the 'labels' key or appending to it if it already exists
     
        update_query = """
        UPDATE extracted_chunks
        SET openai_topic_labels = %s
        WHERE chunk_id = %s;
        """
        # Executing the query, dynamically passing the JSON path as well
        pg.insert(update_query, (labels_json, chunk_id))
        print(f"Labels {labels} added to record with ID {chunk_id}.")

    except psycopg2.Error as e:
        print(f"Error updating labels: {e}")
        pg.conn.rollback()