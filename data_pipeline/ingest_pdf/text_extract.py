import os,re, glob, uuid, requests, hashlib
from llmsherpa.readers import LayoutPDFReader
from PyPDF2 import PdfReader, PdfWriter

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
    
    # Validate `lat` and `lng`
    lat = metadata.get("lat")
    lng = metadata.get("lng")

    if lat is not None or lng is not None:
        # Both must be empty strings or both must be floats/integers
        if (lat == "" and lng == ""):
            pass  # Valid if both are empty strings
        elif (lat == "" or lng == ""):
            raise ValueError("Both `lat` and `lng` must be empty strings or valid floats/integers.")
        elif not isinstance(lat, (float, int)):
            raise ValueError("`lat` must be a float or an integer.")
        elif not isinstance(lng, (float, int)):
            raise ValueError("`lng` must be a float or an integer.")

    return metadata


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

    return output_path, save_name, document_id


def split_pdf(file_path, pages_per_split=400):
    
    temp_directory =  os.path.join("files", "temp")

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
        print(f"Saving pages {start_page+1} to {end_page} to a new PDF")
        output_filename = os.path.join(temp_directory, f"{start_page+1}.pdf")


        print(f"***Output filename: {output_filename}")

        # Check if the folder exists
        if os.path.exists(temp_directory):
            # Check if the script has write permission
            if os.access(temp_directory, os.W_OK):
                print(f"Write permission is granted for: {temp_directory}")
            else:
                print(f"Write permission is NOT granted for: {temp_directory}")
        else:
            print(f"The folder does not exist: {temp_directory}")

        try:
            with open(output_filename, "wb") as output_file:
                writer.write(output_file)
        except Exception as e:
            print(f"Failed to save PDF segment {start_page+1}-{end_page}: {e}")

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
    llmsherpa_api_url = "http://127.0.0.1:5010//api/parseDocument?renderFormat=all"
    pdf_reader = LayoutPDFReader(llmsherpa_api_url)
    print(f"Sending {file} to API")
    try: 
        pdf = pdf_reader.read_pdf(file)
        print(f"{file} analysed successfully")
    except: 
        print("PDF ANALYSIS FAILED - is the chunking server running? Is this a valid PDF?")
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

def list_files(path):   
    files = glob.glob(os.path.join(path, "*.pdf"))
    sorted_files = sorted(files, key=lambda x: int(x.split('/')[-1].split('.')[0]))
    return sorted(sorted_files) 


def create_document_id(metadata):
    # Create a unique document id
    document_id = hashlib.md5(
        (metadata['title'] +
        str(metadata['start_year']) +
        str(metadata['end_year']) +
        metadata['lpa']).encode('utf-8')
    ).hexdigest()
    return document_id


def split_string_to_dict(input_string):
    parts = input_string.split(">")
    dictionary = {}
    for index, part in enumerate(parts):
        dictionary["heading_level_" + str(index)] = part.strip()  # Assuming you want to remove leading/trailing whitespaces
    return dictionary