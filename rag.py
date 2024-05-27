from helpers import search
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage


def rag_query(topic): 

    results = search(topic, 14, {"chunker": "sherpa"})

    prompt = f"""
    I'm writing a neighbourhood plan. 

    I want some ideas on what policies and approaches other communites have in relation to the topic of {topic}. 

    Below are some eaxampes of policies, along with the names of the neighbourhoods that have them in their neighbourhood plan.

    Please summarise and sythesise these policies to make a bullet point list of ideas that we could consider for our plan.
    
    If a specific policy is particularly interesting, please provide more detail on that policy and the neighbourhood that has it.

    Not every point has to be related to a specific location, please consider sythesising ideas from multiple locations.

    Please first response with a brief summary describing what the selected topic means in terms of neighbourhood planning.
    
    Pay special attention to any issues of consultation. 

    Provide 5 ideas, pay attention to technical detials and nuances of planning language. 


    CONTEXT:
    """


    for result in results:
        prompt += f""" 
        {result.metadata['neighbourhood']} in {result.metadata['lpa']} \n
        Policy: {result.metadata['context_text']}\n
        Link: {result.metadata['url']}
        \n\n"""

    links = '<ul>'
    for result in results:
        links += f"<li><a href='{result.metadata['url']}'> {result.metadata['neighbourhood']} neighbourhood plan </a>, page {result.metadata['page']}</li>"

    links += '</ul>'
    print(prompt)

    chat = ChatOpenAI(model_name="gpt-4", temperature=0.0)

    # Send the query to GPT-4 chat model
    response = chat([HumanMessage(content=prompt)])


    return [prompt, response, links]