import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres
from data_pipeline.geocode_geo_labels.geocode_utils import ensure_locations_table_exists

import json


def load_locations(locations):
    """
    Save a list of location dictionaries to the database in one transaction.
    """
    ensure_locations_table_exists()
    pg = Postgres()

    conn = pg.create_conn()  # Create a database connection
    try:
        with conn:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO public.geocoded_location_mentions (
                        chunk_id, 
                        geocode_success,
                        api_result_rank,
                        geocode_strategy,         
                        formatted_address, 
                        openai_geo_label, 
                        geocode_string, 
                        geom, 
                        bounding_box, 
                        bounding_box_area,
                        distance_from_document_geom, 
                        document_geom_type, 
                        types, 
                        google_place_id,
                        raw_result
                    )
                    VALUES (
                        %s, 
                        %s,
                        %s,
                        %s,
                        %s, 
                        %s, 
                        %s,
                        ST_GeographyFromText(%s), 
                        ST_GeographyFromText(%s), 
                        %s, 
                        %s, 
                        %s,
                        %s::jsonb,  
                        %s, 
                        %s::jsonb
                    );
                """
                for location in locations:
                    geom_wkt = location['geom'].wkt if location['geom'] else None
                    bbox_wkt = location['bounding_box'].wkt if location['bounding_box'] else None

                    cursor.execute(query, (
                        location['chunk_id'],
                        location['geocode_success'],
                        
                        location['api_result_rank'],
                        location['geocode_strategy'],
                        location['formatted_address'],
                        location['openai_geo_label'],
                        location['geocode_string'],
                        geom_wkt,
                        bbox_wkt,
                        location['bounding_box_area'],
                        location['distance_from_document_geom'],
                        location['document_geom_type'],
                        json.dumps(location['types']),  
                        location['google_place_id'],
                        json.dumps(location['raw_result'])
                    ))
        conn.commit()  # Commit the transaction if all inserts succeed
    except Exception as e:
        print(f"Error inserting locations: {e}")
        conn.rollback()  # Roll back the transaction if an error occurs
    finally:
        conn.close()  # Ensure the connection is always closed

