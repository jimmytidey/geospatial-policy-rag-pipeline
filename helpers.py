import os,uuid,requests,glob
import pandas as pd
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF

from sherpa import (
    split_pdf,
    sherpa_chunk_pdfs,
    sherpa_fill_in_sections,
    sherpa_coalesce_sections,
)


def chunk_pdf(url, file_name, metadata):
   
    # download the pdf
    download_pdf(url, file_name)

    # pymupdf chunking
    pymupdf_chunks = pymupdf_chunk_pdf(file_name, metadata)
    save_chunks_to_csv(pymupdf_chunks, "pymupdf")
    chunks_csv_to_db("pymupdf")

    # sherpa chunking (by section)
    split_pdf(file_name, 10)
    sherpa_chunks = sherpa_chunk_pdfs(metadata)
    sherpa_chunks = sherpa_fill_in_sections(sherpa_chunks)
    sherpa_chunks = sherpa_coalesce_sections(sherpa_chunks)
    save_chunks_to_csv(sherpa_chunks, "sherpa")
    chunks_csv_to_db("sherpa")

    compare_chunkings(sherpa_chunks, pymupdf_chunks)



def download_pdf(url, save_name):

    # Download the PDF file
    response = requests.get(url, stream=True)

    # Check if the request was successful
    if response.status_code == 200:
        output_path =  os.path.join("files", save_name)

        # Open a file in binary write mode and save the content
        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"PDF downloaded and saved as {output_path}.")
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")

    return output_path


def pymupdf_chunk_pdf(file_name, metadata):
    
    # Partition the PDF into chunks
    pdf_path =  os.path.join("files", file_name)

    document = fitz.open(pdf_path)
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
    print(f'PyMuPDF chunks created: {number_of_chunks} from {pdf_path}')         
    return output_chunks
 

def compare_chunkings(sherpa_chunks, pymupdf_chunks): 
    sherpa_count = 0 
    for chunk in sherpa_chunks: 
        sherpa_count += len(chunk['text'].split())

    pymupdf_count = 0
    for chunk in pymupdf_chunks: 
        pymupdf_count += len(chunk['context_text'].split())

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
    chunks = []
    for index, row in df_filled.iterrows():
        chunk =  Document(
            page_content=row['context_text'],
            metadata=row,
        )
        chunks.append(chunk)

    print('Number of docs saving to db: ', len(chunks))
    connection = os.environ["DATABASE_URL"]
    collection_name = "planning"

    vectorstore = PGVector(
        embeddings=OpenAIEmbeddings(model="text-embedding-ada-002"),
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )

    vectorstore.add_documents(chunks, ids=[chunk.metadata["id"] for chunk in chunks])
   

def search(search_term, top_k, filter=None): 
    DATABASE_URL = os.environ["DATABASE_URL"]
    connection = DATABASE_URL
    collection_name = "planning"
   
    vectorstore = PGVector(
        embeddings=OpenAIEmbeddings(model="text-embedding-ada-002"),
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )
    results = vectorstore.similarity_search(search_term, k=top_k, filter=filter)
    
    return results
