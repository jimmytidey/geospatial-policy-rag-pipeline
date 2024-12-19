
import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres


def ensure_locations_table_exists():
    pg = Postgres()
    
    query = """
        CREATE TABLE IF NOT EXISTS public.locations_new
        (
            location_id SERIAL PRIMARY KEY,
            formatted_address TEXT NOT NULL,
            location_name TEXT NOT NULL,
            chunk_id VARCHAR,
            geom GEOGRAPHY(Point, 4326),
            distance_from_document_geom DOUBLE PRECISION,
            geocoded_from_point BOOLEAN,
            CONSTRAINT locations_new_chunk_id_fkey 
                FOREIGN KEY (chunk_id)
                REFERENCES public.extracted_chunks (chunk_id) 
                ON DELETE CASCADE
        );

        -- Create spatial index on geom column
        CREATE INDEX IF NOT EXISTS idx_locations_new_geom
            ON public.locations_new USING GIST (geom);
    """
    
    try:
        pg.insert(query)
        print("Successfully created locations_new table")
    except Exception as e:
        print(f"Error creating locations_new table: {e}")