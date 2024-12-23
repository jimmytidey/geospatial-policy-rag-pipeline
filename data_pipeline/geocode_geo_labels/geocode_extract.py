import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres

def count_chunks_for_geocoding():
    pg = Postgres()

    query = """
        SELECT COUNT(*)
        FROM extracted_chunks
        JOIN documents ON extracted_chunks.document_id = documents.document_id
        WHERE documents.is_geocodeable = TRUE
        AND extracted_chunks.geocoded = FALSE
        AND extracted_chunks.openai_geo_labels IS NOT NULL
        AND extracted_chunks.openai_geo_labels <> '[]'
        AND NOT extracted_chunks.openai_topic_labels::jsonb ? 'broken_fragment';
    """
    
    # Execute the query, passing number_of_records as the limit
    count = pg.query(query)

    return count[0][0]

def extract_chunks_for_geocoding(number_of_records):
    pg = Postgres()

    query = """
        SELECT 
        	chunk_id, 
			openai_geo_labels,
			openai_topic_labels,
			geocode_string_wide,
			geocode_string_narrow,
			title,
            text,
            sections,
			geom,
			geom_centre_point
        FROM extracted_chunks
        JOIN documents ON extracted_chunks.document_id = documents.document_id
        JOIN geo_boundaries ON documents.geo_boundary_id = geo_boundaries.geo_boundary_id
        WHERE documents.is_geocodeable = TRUE
        AND extracted_chunks.geocoded = FALSE
        AND extracted_chunks.openai_geo_labels IS NOT NULL
        AND extracted_chunks.openai_geo_labels <> '[]'
        AND NOT extracted_chunks.openai_topic_labels::jsonb ? 'broken_fragment'
        LIMIT %s;
    """
    
    # Execute the query, passing number_of_records as the limit
    records = pg.query(query, (number_of_records,))

    return records

def check_location_table_exists():
    pg = Postgres()
    query = """
        CREATE TABLE IF NOT EXISTS public.locations_new
        (
            location_id integer NOT NULL DEFAULT nextval('locations_id_seq'::regclass),
            formatted_address text COLLATE pg_catalog."default" NOT NULL,
            location_name text COLLATE pg_catalog."default" NOT NULL,
            chunk_id character varying COLLATE pg_catalog."default",
            geom geography (Point,4326),
            distance_from_document_geom double precision,
            geolocation_range text COLLATE pg_catalog."default",
            CONSTRAINT locations_new_pkey PRIMARY KEY (location_id),
            CONSTRAINT locations_new_chunk_id_fkey FOREIGN KEY (chunk_id)
                REFERENCES public.extracted_chunks (chunk_id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_locations_new_geom
            ON public.locations_new USING gist
            (geom)
            TABLESPACE pg_default;
    """
    result = pg.query(query)
    return result[0]["exists"]