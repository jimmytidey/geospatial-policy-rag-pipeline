from helpers import search
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import google.generativeai as genai
import os
from datetime import datetime
import markdown

def rag_query(topic): 

    print(f'Start RAG retrival at {datetime.now()}')
    results = search(topic, 10, {'chunker': 'sherpa' })
    print(f'Finish RAG retrival at {datetime.now()}')


    prompt = f"""
    
    You are a planning and localism expert, advising on writing a neighbourhood plan for a community in the UK.
    
    Please provide some ideas on what policies and approaches other communites have in relation to the topic of {topic}. 

    Below are some eaxampes of policies, along with the names of the neighbourhoods that have them in their neighbourhood plan.

    Please summarise and sythesise these policies to make a bullet point list of ideas to recommend to the community.
    
    If a specific policy is particularly detailed, please provide more detail on that policy and the neighbourhood that has it.

    Not every point has to be related to a specific location, please consider sythesising ideas from multiple policies.

    Pay special attention to any issues of consultation. 

    Provide 5 ideas, pay attention to technical detials and call out and explain any specialist planning language.


    CONTEXT:
    """

    sorted_results = sorted(results, key=lambda x: len(x.metadata['context_text']), reverse=True)

    for result in sorted_results:
        prompt += f""" 
        {result.metadata['neighbourhood']} in {result.metadata['lpa']} \n
        Policy Title: {result.metadata['sections']}\n
        Policy Details: {result.metadata['text']}\n
        Link: {result.metadata['url']}
        \n\n"""

    links = '<ul>'
    for result in results[0:6]:
        links += f"<li><a href='{result.metadata['url']}'> {result.metadata['neighbourhood']} neighbourhood plan </a>, page {result.metadata['page']}</li>"

    links += '</ul>'
    

    print(f'Gemini query starts at {datetime.now()}')
    chat = ChatOpenAI(model_name="gpt-4", temperature=0.0)
    
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
  
    print(f'Gemini query complete at {datetime.now()}')
   
    return [prompt, markdown.markdown(response.text), links]