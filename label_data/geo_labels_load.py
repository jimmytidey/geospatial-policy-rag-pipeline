sql_query = """
        INSERT INTO locations (lat, lng, formatted_address, location_name, chunk_id)
        VALUES (%s, %s, %s, %s, %s)
    """
    
pg.insert(sql_query, (lat, lng, formatted_address, place_name, chunk_id))


query = """
    UPDATE langchain_pg_embedding
    SET cmetadata = jsonb_set(cmetadata, '{geocoding_complete}', 'true'::jsonb)
    WHERE id = %s
    """

pg.insert(query, (record[0],))              