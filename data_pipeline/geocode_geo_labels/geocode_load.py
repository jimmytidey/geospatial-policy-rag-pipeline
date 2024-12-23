import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres
import json


def load_locations(locations):
    ensure_locations_table_exists()

    pg = Postgres()
    conn = pg.return_connection()
    with conn:
        with conn.cursor() as cur:

            for location in locations:
                load_location_query(location, cur)

            query_mark_chunk_as_geocoded = """
                UPDATE public.extracted_chunks
                SET geocoded = TRUE
                WHERE chunk_id = %s;
            """

            cur.execute(query_mark_chunk_as_geocoded, (locations[0]['chunk_id'],))



def load_location_query(location, cursor):
    # Convert Shapely objects to WKT format
    geom_wkt = location['geom'].wkt if location['geom'] else None
    bbox_wkt = location['bounding_box'].wkt if location['bounding_box'] else None
    query = """
        INSERT INTO public.locations_new (
            chunk_id, 
            formatted_address, 
            openai_geo_label, 
            geocode_string, 
            geom, 
            bounding_box, 
            bounding_box_area,
            distance_from_document_geom, 
            document_geom_type, 
            types, 
            raw_result
        )
        VALUES (
            %s, %s, %s, %s, 
            ST_GeographyFromText(%s), 
            ST_GeographyFromText(%s), 
            %s, %s, %s, 
            %s::jsonb, %s::jsonb
        );
    """

    # Execute the query with parameter substitution
    cursor.execute(query, (
        location['chunk_id'],
        location['formatted_address'],
        location['openai_geo_label'],
        location['geocode_string'],
        geom_wkt,
        bbox_wkt,
        location['bounding_box_area'],
        location['distance_from_document_geom'],
        location['document_geom_type'],
        json.dumps(location['types']),  # Convert types to JSON string
        json.dumps(location['raw_result'])  # Convert raw_result to JSON string
    ))



def ensure_locations_table_exists():
    pg = Postgres()

    query = """
        CREATE TABLE IF NOT EXISTS public.locations_new
        (
            location_id SERIAL PRIMARY KEY,
            chunk_id VARCHAR(255),
            formatted_address TEXT NOT NULL,
            openai_geo_label TEXT NOT NULL,
            geocode_string TEXT NOT NULL,
            geom GEOGRAPHY(Point, 4326),
            bounding_box GEOGRAPHY(Polygon, 4326),
            bounding_box_area DOUBLE PRECISION,
            distance_from_document_geom DOUBLE PRECISION,
            document_geom_type TEXT NOT NULL,
            types JSONB,
            raw_result JSONB,
            
            CONSTRAINT locations_new_chunk_id_fkey 
                FOREIGN KEY (chunk_id)
                REFERENCES public.extracted_chunks (chunk_id) 
                ON DELETE CASCADE
        );

        -- Create spatial index on geom column
        CREATE INDEX IF NOT EXISTS idx_locations_new_geom
            ON public.locations_new USING GIST (geom);

        -- Create spatial index on bounding_box column
        CREATE INDEX IF NOT EXISTS idx_locations_new_bbox
            ON public.locations_new USING GIST (bounding_box);

        -- Add index on foreign key
        CREATE INDEX IF NOT EXISTS idx_locations_new_chunk_id
            ON public.locations_new (chunk_id);
    """
    
    try:
        pg.insert(query)
        
    except Exception as e:
        print(f"Error creating locations_new table: {e}")