import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres 
import json

def geo_labels_load(chunk_id, location_records):
    
    pg = Postgres()

    conn = pg.create_conn()

    try:
        with conn.cursor() as cursor:
            # Begin transaction
            cursor.execute("BEGIN;")
            
            # Check if a location with this chunk_id already exists (only once)
            check_query = """
                SELECT 1 FROM locations WHERE chunk_id = %s LIMIT 1;
            """
            cursor.execute(check_query, (chunk_id,))
            result = cursor.fetchone()
            
            if result:
                # If a location with this chunk_id exists, fail the transaction
                raise Exception(f"Location with chunk_id {chunk_id} already exists.")
            
            # Prepare a list to hold all the location names
            place_names = []

            # Loop through each location record (no need to check chunk_id again)
            for location_record in location_records:
                lat = location_record['lat']
                lng = location_record['lng']
                formatted_address = location_record['formatted_address']
                place_name = location_record['location_name']
                
                # Add the location name to the place_names list
                place_names.append(place_name)
                
                # Insert into 'locations' table
                locations_query = """
                    INSERT INTO locations (geom, formatted_address, location_name, chunk_id)
                    VALUES (ST_MakePoint(%s, %s), %s, %s, %s);
                """
                
                cursor.execute(locations_query, (lat, lng, formatted_address, place_name, chunk_id))
            
            # Convert the place_names list to a JSON array
            place_names_json = json.dumps(place_names)

            # Update the langchain_pg_embedding table with the JSON array of place names
            chunks_query = """
                UPDATE langchain_pg_embedding
                SET cmetadata = jsonb_set(cmetadata, '{openai_geo_labels}', %s::jsonb)
                WHERE id = %s
            """
           
            cursor.execute(chunks_query, (place_names_json, chunk_id))
            
            # Commit the transaction after processing all records
            cursor.execute("COMMIT;")
            print(f"Successfully added {len(location_records)} locations for chunk_id {chunk_id}.")

    except Exception as e:
        # Rollback the transaction in case of an error
        conn.rollback()
        print(f"Transaction failed, rolled back changes. Error: {e}")

    finally:
        conn.commit()  # Ensure the connection is committed or rolled back properly
