import sys,os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres
from data_pipeline.geocode_geo_labels.geocode_utils import ensure_locations_table_exists

def count_labels_for_geocoding():
    pg = Postgres()

    ensure_locations_table_exists()

    query = """
        SELECT 
            COUNT(DISTINCT ec.chunk_id || '|' || geo_label::TEXT) AS unique_count
        FROM extracted_chunks ec
        CROSS JOIN LATERAL jsonb_array_elements_text(ec.openai_geo_labels) AS geo_label
        LEFT JOIN geocoded_location_mentions ln 
            ON ec.chunk_id = ln.chunk_id
            AND geo_label::TEXT = ln.openai_geo_label
        WHERE 
            ec.openai_geo_labels IS NOT NULL
            AND ec.openai_geo_labels <> '[]'
            AND NOT ec.openai_topic_labels::jsonb ? 'broken_fragment'
            AND ln.chunk_id IS NULL;
    """
    
    # Execute the query, passing number_of_records as the limit
    count = pg.query(query)

    return count[0][0]

def extract_labels_for_geocoding(number_of_records):
    pg = Postgres()

    query = """
        SELECT DISTINCT
            ec.chunk_id,
            geo_label::TEXT AS openai_geo_label,
            ec.openai_topic_labels,
            doc.geocode_string_wide,
            doc.geocode_string_narrow,
            doc.title,
            ec.text,
            ec.sections,
            geo.geom,
            doc.geom_centre_point
        FROM extracted_chunks_test ec
        CROSS JOIN LATERAL jsonb_array_elements_text(ec.openai_geo_labels) AS geo_label
        JOIN documents doc ON ec.document_id = doc.document_id
        JOIN geo_boundaries geo ON doc.geo_boundary_id = geo.geo_boundary_id
        LEFT JOIN geocoded_location_mentions ln 
            ON ec.chunk_id = ln.chunk_id
            AND geo_label::TEXT = ln.openai_geo_label
        WHERE 
            doc.is_geocodeable = TRUE
            AND ec.geocoded = FALSE
            AND ec.openai_geo_labels IS NOT NULL
            AND ec.openai_geo_labels <> '[]'
            AND NOT ec.openai_topic_labels::jsonb ? 'broken_fragment'
            AND ln.chunk_id IS NULL
        LIMIT %s
    """
    
    # Execute the query, passing number_of_records as the limit
    records = pg.query(query, (number_of_records,))

    return records
