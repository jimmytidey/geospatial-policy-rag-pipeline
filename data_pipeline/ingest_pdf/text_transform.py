import os 
from openai import OpenAI


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


def embed(chunks): 
    for chunk in chunks: 
        chunk['embedding'] = get_embedding(chunk['context_text'])
    return chunks


def get_embedding(text, model="text-embedding-ada-002"):
    client = OpenAI()
    text = text.replace("\n", " ")
    return client.embeddings.create(input = [text], model=model).data[0].embedding


def split_string_to_dict(input_string):
    parts = input_string.split(">")
    dictionary = {}
    for index, part in enumerate(parts):
        dictionary["heading_level_" + str(index)] = part.strip()  # Assuming you want to remove leading/trailing whitespaces
    return dictionary
