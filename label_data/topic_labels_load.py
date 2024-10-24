import psycopg2, sys,os, json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres 


def topic_labels_load(record_id, labels, label_type):
    """
    Adds an array of labels to the 'labels' key in the cmetadata JSON column for a given record.
    If the 'labels' key does not exist, it will create it and add the new labels.

    :param record_id: The unique id of the record (assumed to be the primary key)
    :param labels: A list of labels (Python array) to add
    """

    pg=Postgres()
    
    try:
        with pg.conn.cursor() as cursor:
            # Convert the Python list to a JSON array string
            labels_json = json.dumps(labels)
            
            
            # Update the cmetadata JSON field by creating the 'labels' key or appending to it if it already exists
            
            json_path = '{' + label_type + '}'

            query = """
                UPDATE langchain_pg_embedding
                SET cmetadata = jsonb_set(
                    cmetadata,
                    %s,
                    (COALESCE(cmetadata->%s, '[]'::jsonb) || %s::jsonb),
                    true
                )
                WHERE id = %s;
            """

            # Executing the query, dynamically passing the JSON path as well
            cursor.execute(query, (json_path, label_type, labels_json, record_id))
            
            # Commit the transaction
            pg.conn.commit()
            
            print(f"Labels {labels} with {label_type} added to record with ID {record_id}.")

    except psycopg2.Error as e:
        print(f"Error updating labels: {e}")
        pg.conn.rollback()