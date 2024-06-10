from helpers import search
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import google.generativeai as genai
import os
from datetime import datetime
import markdown

def rag_query(topic): 

    print(f'Start RAG retrival at {datetime.now()}')
    results = search(topic, 20, {'chunker': 'sherpa' })
    print(f'Finish RAG retrival at {datetime.now()}')

    long_sentence_results = [
        d for d in results if len(d[0].metadata.get("text", "").split()) >= 30
    ]

    relevant_long_sentence_results = [
        d for d in long_sentence_results if d[1] < 0.21
    ]

    if len(relevant_long_sentence_results) <5:
        ret = "Not enough relevant results to generate a response. Please try a different topic."
        return [ret, ret, ret]

    prompt = f"""
    
    Please provide advice as though you are a planning and localism expert, advising on writing a neighbourhood plan for a community in the UK.
    
    Please provide some ideas on what policies and approaches other communites have in relation to the topic of {topic}, using only information from the example policies.

    Provide 5 ideas, pay attention to technical planning detials. Connect each idea to a specific policy or approach from the example policies.
    
    Please use only the information from the example policies to generate your response.
    

    ------------------------------------------
    Example policies: 
    """


    for result in relevant_long_sentence_results:
        prompt += f""" 
        {result[0].metadata['neighbourhood']} in {result[0].metadata['lpa']} \n
        Policy Title: {result[0].metadata['sections']}\n
        Policy Details: {result[0].metadata['text']}\n
        Link: {result[0].metadata['url']}
        \n\n"""

    links = '<ul>'
    for result in results[0:6]:
        links += f"<li><a href='{result[0].metadata['url']}'> {result[0].metadata['neighbourhood']} neighbourhood plan </a>, page {result[0].metadata['page']}</li>"

    links += '</ul>'
    

    print(f'Gemini query starts at {datetime.now()}')
    chat = ChatOpenAI(model_name="gpt-4", temperature=0.0)
    
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
  
    print(f'Gemini query complete at {datetime.now()}')
   
    return [prompt, markdown.markdown(response.text), links]