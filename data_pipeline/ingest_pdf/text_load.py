import sys,os, hashlib
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from postgres import Postgres 




# Function to save data
def save_chunks_to_db(chunks, document_id):
    
    pg = Postgres()
    
    ensure_extracted_chunks_table_setup()

    for chunk in chunks:
        chunk_id = create_chunk_id(document_id, chunk["context_text"])
        data = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "text": chunk["text"],
            "sections": chunk["sections"],
            "context_text": chunk["context_text"],
            "level": chunk["level"],
            "block_idx": chunk["block_idx"],
            "page": chunk["page"],
            "chunker": chunk["chunker"],
            "notes": chunk["notes"],
            "coalesced_with": chunk["coalesced_with"],
            "embedding": chunk["embedding"]  # Ensure this is a list/tuple of floats
        }
     
        insert_query = """
            INSERT INTO extracted_chunks (
                chunk_id, document_id, text, sections, context_text, level, block_idx, page, chunker, 
                notes, coalesced_with, embedding
            ) VALUES (
                %(chunk_id)s, %(document_id)s, %(text)s, %(sections)s, %(context_text)s, %(level)s, 
                %(block_idx)s, %(page)s, %(chunker)s, %(notes)s, %(coalesced_with)s, %(embedding)s
            ) ON CONFLICT (chunk_id) DO NOTHING;
        """

        pg.insert(insert_query, data)



def create_document(metadata, document_id):
    
    pg = Postgres()
    ensure_documents_table_setup()

    results = pg.query(f"SELECT * FROM documents WHERE document_id = '{document_id}'")

    if results:
        print(f"Document with id {document_id} already exists")
        return

    # Create a record for the document in the documents table
    print(f"Creating document with id: {document_id}")

    insert_query = """
        INSERT INTO documents (
            document_id, category, sub_category, lpa, neighbourhood, title, url, file, 
            start_year, end_year, council_type, experiment, notes, geom_centre_point
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        """

    
    values = (
        document_id,
        metadata["category"],
        metadata["sub_category"],
        metadata["lpa"],
        metadata["neighbourhood"],
        metadata["title"],
        metadata["url"],
        metadata["file"],
        int(metadata["start_year"]),
        int(metadata["end_year"]),
        metadata["council_type"],
        metadata["experiment"],
        metadata["notes"],
        metadata.get("lng"),  # Longitude
        metadata.get("lat")   # Latitude
    )




    # Execute the query
    pg.insert(insert_query, values)


def ensure_extracted_chunks_table_setup():

    pg = Postgres()

    # Create the extension for vector data
    create_extension_query = "CREATE EXTENSION IF NOT EXISTS vector;"

    create_table_query = """
        CREATE TABLE IF NOT EXISTS extracted_chunks (
            chunk_id TEXT PRIMARY KEY, -- Primary Key ensures chunk_id is unique
            document_id TEXT REFERENCES documents(document_id) ON DELETE CASCADE, -- Foreign Key
            text TEXT,
            sections TEXT,
            openai_geo_labels JSONB, -- New column for geo labels
            openai_topic_labels JSONB, -- New column for topic labels	
            context_text TEXT,
            level INT,
            block_idx INT,
            page INT,
            chunker TEXT,
            notes TEXT,
            coalesced_with TEXT,
            embedding VECTOR(1536) -- Vector type for 1536-dimensional vectors
        );
    """
    
    # Create the vector index for fast similarity search
    create_index_query = """
    CREATE INDEX IF NOT EXISTS embedding_idx 
    ON extracted_chunks USING ivfflat (embedding) WITH (lists = 100);
    """
    
    # Run all queries sequentially
    pg.insert(create_extension_query)  # Ensure pgvector extension is enabled
    pg.insert(create_table_query)      # Create the table if it doesn't exist
    pg.insert(create_index_query)      # Create the index if it doesn't exist

def ensure_documents_table_setup():
    # SQL query to create the documents table

    pg = Postgres()

    install_extension_query = "CREATE EXTENSION IF NOT EXISTS postgis;"
    pg.insert(install_extension_query)

    create_table_query = """
    CREATE TABLE IF NOT EXISTS documents (
        document_id TEXT UNIQUE, -- Ensures document_id is unique
        category TEXT,
        sub_category TEXT,
        lpa TEXT,
        neighbourhood TEXT,
        title TEXT,
        url TEXT,
        file TEXT,
        start_year INT,
        end_year INT,
        council_type TEXT,
        experiment TEXT,
        notes TEXT,
        is_geocodeable BOOLEAN, 
        geocode_stirng_wide TEXT,
        geocode_string_narrow TEXT,
        geom_centre_point GEOGRAPHY(Point, 4326)
        geocoded BOOLEAN DEFAULT FALSE;
    );
    """
    # Execute the query using your pg.insert() function
    pg.insert(create_table_query)


def create_chunk_id(document_id, text):
    # Create a unique document id
    chunk_id = hashlib.md5(
        (document_id + text).encode('utf-8')
    ).hexdigest()
    return chunk_id

