import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres


def ensure_locations_table_exists():
    pg = Postgres()

    query = """
        CREATE TABLE IF NOT EXISTS public.geocoded_location_mentions
        (
            location_id SERIAL PRIMARY KEY,
            chunk_id VARCHAR(255),
            geocode_success BOOLEAN,
            api_result_rank INTEGER,
            geocode_strategy TEXT,
            formatted_address TEXT,
            openai_geo_label TEXT,
            geocode_string TEXT ,
            geom GEOGRAPHY(Point, 4326),
            bounding_box GEOGRAPHY(Polygon, 4326),
            bounding_box_area DOUBLE PRECISION,
            distance_from_document_geom DOUBLE PRECISION,
            document_geom_type TEXT ,
            types JSONB,
            google_place_id VARCHAR(255),
            raw_result JSONB,
            
            CONSTRAINT geocoded_location_mentions_chunk_id_fkey 
                FOREIGN KEY (chunk_id)
                REFERENCES public.extracted_chunks (chunk_id) 
                ON DELETE CASCADE
        );

        -- Create spatial index on geom column
        CREATE INDEX IF NOT EXISTS idx_geocoded_location_mentions_geom
            ON public.geocoded_location_mentions USING GIST (geom);

        -- Create spatial index on bounding_box column
        CREATE INDEX IF NOT EXISTS idx_geocoded_location_mentions_bbox
            ON public.geocoded_location_mentions USING GIST (bounding_box);

        -- Add index on foreign key
        CREATE INDEX IF NOT EXISTS idx_geocoded_location_mentions_chunk_id
            ON public.geocoded_location_mentions (chunk_id);
    """
    
    try:
        pg.insert(query)
        
    except Exception as e:
        print(f"Error creating geocoded_location_mentions table: {e}")