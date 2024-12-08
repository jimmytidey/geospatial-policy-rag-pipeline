'''
import os,uuid,requests,hashlib
import pandas as pd
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF
from postgres import Postgres

from sherpa import (
    split_pdf,
    sherpa_chunk_pdfs,
    sherpa_fill_in_sections,
    sherpa_coalesce_sections,
)

load_dotenv()

def validate_metadata(metadata: dict) -> dict:
    
    # Validate `category`
    if not isinstance(metadata.get("category"), str) or not metadata["category"].strip():
        raise ValueError("`category` must be a non-empty string.")
    
    # Validate `title`
    if not isinstance(metadata.get("title"), str) or not metadata["title"].strip():
        raise ValueError("`title` must be a non-empty string.")
    
    # Validate `start_year`
    if "start_year" in metadata:
        if not (isinstance(metadata["start_year"], int) or metadata["start_year"] == ""):
            raise ValueError("`start_year` must be an integer or an empty string.")
    
    # Validate `end_year`
    if "end_year" in metadata:
        if not (isinstance(metadata["end_year"], int) or metadata["end_year"] == ""):
            raise ValueError("`end_year` must be an integer or an empty string.")

    
    return metadata

def chunk_pdf(url, metadata):
   
    # download the pdf
    [file_path, file_name] = download_pdf(url,metadata)
    metadata['file'] = file_name

    # pymupdf chunking
    pymupdf_chunks = pymupdf_chunk_pdf(file_path, metadata)
    save_chunks_to_csv(pymupdf_chunks, "pymupdf")
    chunks_csv_to_db("pymupdf")

    # sherpa chunking (by section)
    split_pdf(file_path, 10)
    sherpa_chunks = sherpa_chunk_pdfs(metadata)
    sherpa_chunks = sherpa_fill_in_sections(sherpa_chunks)
    sherpa_chunks = sherpa_coalesce_sections(sherpa_chunks)
    save_chunks_to_csv(sherpa_chunks, "sherpa")
    chunks_csv_to_db("sherpa")

    # compare_chunkings(sherpa_chunks, pymupdf_chunks)


def download_pdf(url, metadata):

    # Download the PDF file
    response = requests.get(url, stream=True)
    document_id = create_document_id(metadata)

    category = metadata.get('category', '')
    lpa = metadata.get('lpa', '')
    neighbourhood = metadata.get('neighbourhood', '')

    # Construct the new file name
    file_name_parts = [category, lpa, neighbourhood, str(document_id)]
    save_name = "_".join(filter(None, file_name_parts)) + ".pdf"

    # Check if the request was successful
    if response.status_code == 200:
        output_path =  os.path.join("files/pdfs", save_name)

        # Open a file in binary write mode and save the content
        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"PDF downloaded and saved as {output_path}.")
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")

    return output_path, save_name


def pymupdf_chunk_pdf(file_path, metadata):
    
    # Partition the PDF into chunks
    document = fitz.open(file_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
   
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)

    output_chunks = []

    for i, chunk in enumerate(chunks):
        local_metadata = dict(metadata)
        local_metadata['id'] = str(uuid.uuid4())
        local_metadata['context_text'] = chunk
        local_metadata['text'] = chunk
        local_metadata['chunker'] = 'pymupdf'
        local_metadata['page'] = ''
        local_metadata['page_name'] = ''
        local_metadata['sections'] = '' 

        output_chunks.append(local_metadata)

    number_of_chunks = len(output_chunks)
    print(f'PyMuPDF chunks created: {number_of_chunks} from {file_path}')         
    return output_chunks
 

def compare_chunkings(sherpa_chunks, pymupdf_chunks): 
    sherpa_count = 0 
    for chunk in sherpa_chunks: 
        sherpa_count += len(chunk['text'].split())

    pymupdf_count = 0
    for chunk in pymupdf_chunks: 
        pymupdf_count += len(chunk['context_text'].split())

    print('Sanity check:')
    print(f"Sherpa chunking has {sherpa_count} words")
    print(f"PyMuPDF chunking has {pymupdf_count} words")
    

def save_chunks_to_csv(chunks, chunker):
    df = pd.DataFrame(chunks)
    df_filled = df.fillna('')
    csv_file_path = os.path.join('files', chunker +'_chunks.csv')
    df_filled.to_csv(csv_file_path, index=False)
    print(f"Data successfully saved to {csv_file_path}")


def chunks_csv_to_db(chunker):
    csv_file_path = os.path.join('files', chunker+'_chunks.csv')
    df = pd.read_csv(csv_file_path)
    df_filled = df.fillna('')
    
    df_filled["start_year"] = df_filled["start_year"].astype(int)
    df_filled["end_year"] = df_filled["end_year"].astype(int)

    document_metatdata = df_filled.iloc[0]
    document_id = create_document(document_metatdata)
    df_filled["document_id"] = document_id  
    df_filled["document_id"] = df_filled["document_id"].astype(str)
 
    chunks = []
    for index, row in df_filled.iterrows():
        metadata_dict = row.to_dict()
        chunk = Document(
            page_content=metadata_dict['context_text'], 
            metadata=metadata_dict
        )
        chunks.append(chunk)

    print('Number of docs saving to db: ', len(chunks))
    connection = os.environ["DATABASE_URL"]
    collection_name = "planning"

    vectorstore = PGVector(
        embeddings=OpenAIEmbeddings(openai_api_key= os.environ["OPENAI_API_KEY"], model="text-embedding-ada-002"),
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )

    vectorstore.add_documents(chunks, ids=[chunk.metadata["id"] for chunk in chunks])

def create_document(metadata):
    pg = Postgres()

    # Create a record for the document in the documents table
    document_id = create_document_id(metadata)
    print(f"Creating document with id: {document_id}")

    insert_query = """
    INSERT INTO documents (
        document_id, category, lpa, neighbourhood, title, url, file, 
        start_year, end_year, council_type, experiment, notes
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        document_id,
        metadata["category"],
        metadata["lpa"],
        metadata["neighbourhood"],
        metadata["title"],
        metadata["url"],
        metadata["file"],
        int(metadata["start_year"]),
        int(metadata["end_year"]),
        metadata["council_type"],
        metadata["experiment"],
        metadata["notes"]   
    )

    filled_query = insert_query % tuple(f"'{str(p)}'" if isinstance(p, str) else str(p) for p in values)

    # Print the filled query
    print(filled_query)

    # Execute the query
    pg.insert(insert_query, values)

    # Check if the document has been  successfully added to the documents table
    result = pg.query("SELECT * FROM documents WHERE document_id = %s", (document_id,))
    if not result:
        raise ValueError(f"Failed to create document with id {document_id}")
    else:
        document_id = result[0]['document_id'] if len(result) > 0 else None
   

    return document_id

def create_document_id(metadata):
    # Create a unique document id
    document_id = hashlib.md5(
        (metadata['title'] +
        str(metadata['start_year']) +
        str(metadata['end_year']) +
        metadata['lpa']).encode('utf-8')
    ).hexdigest()
    return document_id
   

def search(search_term, top_k, filter=None): 
    connection =  os.getenv("DATABASE_URL")
    collection_name = "planning"
   
    vectorstore = PGVector(
        embeddings=OpenAIEmbeddings(openai_api_key= os.environ["OPENAI_API_KEY"], model="text-embedding-ada-002"),
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )
    results = vectorstore.similarity_search_with_score(search_term, k=top_k, filter=filter)
    
    return results
'''