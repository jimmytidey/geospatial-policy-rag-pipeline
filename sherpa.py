import os,re, glob, uuid
from llmsherpa.readers import LayoutPDFReader
from PyPDF2 import PdfReader, PdfWriter



def split_pdf(file_name,  pages_per_split=400):
    
    temp_directory =  os.path.join("files", "temp")
    file_path = os.path.join("files", file_name)

    # Ensure the output directory exists
    if not os.path.exists(temp_directory):
        os.makedirs(temp_directory)

    # Remove any previous files from the temp directory
    print('Deleting any old temp files')
    pdf_files = glob.glob(os.path.join(temp_directory, '*.pdf'))
    for pdf_file in pdf_files:
        try:
            os.remove(pdf_file)
            print(f"Deleted: {pdf_file}")
        except Exception as e:
            print(f"Failed to delete {pdf_file}. Reason: {e}")

    # Read the downloaded PDF
    
    try:
        reader = PdfReader(file_path)
    except Exception as e:
        raise Exception(f"Failed to read the PDF file: {e}")

    # Splitting the PDF
    total_pages = len(reader.pages)
    print("total pages: ", total_pages)
    for start_page in range(0, total_pages, pages_per_split):
        writer = PdfWriter()
        end_page = min(start_page + pages_per_split, total_pages)

        # Add pages to the new split PDF
        for page_number in range(start_page, end_page):
            writer.add_page(reader.pages[page_number])

        # Save the split PDF
        output_filename = os.path.join(temp_directory, f"{start_page+1}.pdf")
        with open(output_filename, "wb") as output_file:
            writer.write(output_file)

    print(f"PDF split into segments of {pages_per_split} pages in '{temp_directory}'")


def sherpa_chunk_pdfs(metadata):
    temp_directory =  os.path.join("files", "temp")

    files = list_files(temp_directory)
    print("Embedding files: ", files)
    docs = []
    last_page_number = 0 
    last_section = ''
    for file in files: 
        docs.extend(sherpa_chunk_pdf(file, metadata, last_page_number))
        if len(docs)>0:
            last_page_number = docs[-1]['page']
        added_length = len(docs)
        print(f"{added_length} chunks added from {file} ", )
        os.remove(file)
    return docs

def sherpa_chunk_pdf(file, metadata, last_page_number):
    print(f"splitting and embedding file: {file}")
    print()
    llmsherpa_api_url = "http://localhost:5010/api/parseDocument?renderFormat=all"
    pdf_reader = LayoutPDFReader(llmsherpa_api_url)
    print(f"Sending {file} to API")
    try: 
        pdf = pdf_reader.read_pdf(file)
        print(f"{file} analysed successfully")
    except: 
        print("PDF ANALYSIS FAILED - bad pdf?")
        return []
    
    output_chunks = []
    
    for index, chunk in enumerate(pdf.chunks()):
        local_metadata = dict(metadata)
        local_metadata['id'] = str(uuid.uuid4())
        html = chunk.to_html(include_children=True, recurse=True)
        local_metadata['text'] = re.sub('<[^<]+?>', ' ', html)
        local_metadata['sections'] = chunk.parent_text()
        local_metadata['context_text'] = local_metadata['sections'] + " " + local_metadata['text']
        local_metadata['level'] = chunk.level 
        local_metadata['block_idx'] = chunk.block_idx
        local_metadata['page'] = last_page_number + chunk.page_idx 
        local_metadata['chunker'] = 'sherpa'
        local_metadata['notes'] = ''
        local_metadata['coalesced_with'] = ''
        headings = split_string_to_dict(local_metadata['sections'])
        local_metadata.update(headings)
        
        output_chunks.append(local_metadata)

    number_of_chunks = len(output_chunks)
    print(f'Sherpa chunks created: {number_of_chunks} from {file}')       
    return(output_chunks)

def sherpa_fill_in_sections(chunks):
    chunk_copy_over_count = 0
    for index, chunk in enumerate(chunks): 
        
        if chunk['sections'] == '' and index > 0:
            chunk['sections'] = chunks[index-1]['sections']
            chunk['notes'] = 'Section information inferred from previous chunk'
            print(f"Section information inferred from previous chunk {chunk['text']}")
            headings = split_string_to_dict(chunk['sections'])
            chunk.update(headings)
            chunk_copy_over_count += 1

    return chunks

def sherpa_coalesce_sections(chunks):
    coalesced_chunks = []
    for index, chunk in enumerate(chunks): 
        if 'added' not in chunk: # if the chunk has not been added to the coalesced chunks
            coalesced_chunk = dict(chunk)
            if len(chunks)-(index)> 10: look_forward = 10 
            else: look_forward = len(chunks)-index
            for i in range(1, look_forward): # try to coalesce up to 10 chunks forward
                
                coalesced_chunk_length = len(coalesced_chunk['context_text'].split()) + len(chunks[index+i]['context_text'].split())
                if coalesced_chunk_length <800:  # check if coalesced chunk will be too long 
                    
                    if chunks[index+i]['sections'] == chunk['sections']: # check the chunk has the same section
                        coalesced_chunk['context_text'] += " " + chunks[index+i]['text'] # add the text to the chunk
                        coalesced_chunk['text'] += " " + chunks[index+i]['text'] # add the text to the chunk
                        chunks[index+i]['added'] = True # mark the chunk as added
                        if 'coalesced_with' not in coalesced_chunk:
                            coalesced_chunk['coalesced_with'] = chunks[index+i]['text'] 
                        else:
                            coalesced_chunk['coalesced_with'] += ', \n' + chunks[index+i]['text'] 
            coalesced_chunks.append(coalesced_chunk)       
                    
    return coalesced_chunks

def split_string_to_dict(input_string):
    parts = input_string.split(">")
    dictionary = {}
    for index, part in enumerate(parts):
        dictionary["heading_level_" + str(index)] = part.strip()  # Assuming you want to remove leading/trailing whitespaces
    return dictionary

def list_files(path):   
    files = glob.glob(os.path.join(path, "*.pdf"))
    sorted_files = sorted(files, key=lambda x: int(x.split('/')[-1].split('.')[0]))
    return sorted(sorted_files) 