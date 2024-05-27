
# def pdf_to_chunks(file_path): 
#     elements = partition_pdf(filename=file_path, strategy='auto')
#     chunks = elements_to_chunks(elements)
#     return chunks 

# def url_to_chunks(url): 
#     elements = partition_html(url=url, strategy='auto')
#     chunks = elements_to_chunks(elements)
#     return chunks 

# def elements_to_chunks(elements):
#     chunks = chunk_elements(elements, max_characters=1000, overlap=100)
#     total_word_count = 0 
#     for chunk in chunks:
#         words = chunk.text.split()
#         word_count = len(words) 
#         total_word_count += word_count
#     print("total wordcount after chunking " + str(total_word_count))    
#     return chunks


# def pdf_to_text(source_pdf_folder_path, file_name):

#     try:
#         source_file_path = source_pdf_folder_path + "/" + file_name
  
#         with open(source_file_path, 'rb') as pdf_file:
#             # Create a PDF reader object
#             pdf_reader = PyPDF2.PdfReader(pdf_file)
            
#             # Initialize an empty string to store the text
#             text = ''
            
#             # Iterate through each page of the PDF
#             for page_num in range(len(pdf_reader.pages)):
#                 # Get the page object
#                 page = pdf_reader.pages[page_num]
                
#                 # Extract text from the page
#                 text += page.extract_text()
            
#             print('finished reading')
#             print(text[0:20])   
#             return text

#     except Exception as e: 
#         print(file_name)
#         print(e)



# def plain_text_chunker():

#     # Split text
#     split_texts_list = sent_tokenize(text)

#     # Only keep sentences with more than 6 words
#     proper_sentences = [i for i in split_texts_list if i.count(" ") >= 6]
#     print("Number of sentences", len (proper_sentences))
#     print('sentences')
#     pprint.pprint(proper_sentences)

#     # Group sentences into triplets
#     n = 3  # group size
#     m = 2  # overlap size
#     triplets = [
#         " ".join(proper_sentences[i: i + n])
#         for i in range(0, len(proper_sentences), n - m)
#     ]
#     pprint.pprint(triplets)

#     print('number of triplets ', len(triplets)) 
#     # Truncate triplets to 1000 characters
#     triplets_trucated = [i[:1000] for i in triplets][0:100]

    