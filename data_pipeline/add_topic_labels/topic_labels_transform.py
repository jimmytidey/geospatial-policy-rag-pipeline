import openai
import os

def topic_labels_transform(title, text):
  
    prompt = f'''
    Please apply the following labels to the passage of short text and title supplied below. Return the labels as a comma separated list. Do not return any explanation or anything except the comma separated list. 

    Title: {title}

    Text: {text}

    Labels 
    "broken_fragment" - if the text appears incoherent or impossible to understand 

    "bad_start" - if the text appears to start mid-sentence 

    "truncated" - if the text is cut off half way through 

    "context" - if it describes the general topic of planning or neighborhood plans, or is introductory text

    "green_space" - if it explicitly discusses the phrase green space, green space assessment or green infrastructure etc. 

    "CIL" - if it is explicitly about the community infrastructure levy 

    "sustainable_development" if it is about sustainable development

    "house_building" if it is about building houses 

    "economy" - if it is about business, employment, industry or the economy

    "town_centers" - if it discusses the vibrancy of the town center, high street or shopping areas

    "communities" - if it is about social connectedness, meeting people, loneliness, communities, clubs

    "community_assets" - if it explicitly discusses community assets

    "village_hall" - if it is about village halls or community centers

    "transport" - if it is about the generalised topic of transport

    “cars” - if it is about parking, traffic, roads or cars 

    “bikes” - if it is about cycle lanes or bikes or cycling, bike lanes, bike storage, bike racks, biking or cycling infrastructure

    “walking” - if it is about bridleways, footpaths, pedestrians, or walking 

    "communications" if it is about broadband, phone signal, internet connections etc. 

    "design" - if it about architectural styles, shop fronts, building materials or building design guides 

    "green_belt" - if it is explicitly about the greenbelt

    "climate_change" - if it about flooding, coastal change, or climate change, climate emergency, or carbon reduction

    "natural_environment" if it is about biodiversity or the natural environment, or green spaces in general 

    "historic_environment" - if it is about heritage or historical preservation of the features of a village or town or archaeological sites or archticeture

    "materials" - if it is about mining or quarrying

    "policy" - if it explicitly states that the text is about action, policy, campaign, or strategy, or lobbying 

    "map" - if it is about a map or a key to a map or a description of a map

    "drainage" - if it is about drains, sewers, or drainage or water management or sustainable drainage systems     
    
    "consultation" - if the text describes a consultative process

    "annex" - if the text is an annex or appendix

    "table_of_contents" - if the text appears to be a table of contents

    “education” - if it is about schools, colleges or education

    “sports” - if it is about sports facilities, tennis courts, football pitches etc.

    'views' - if it is about views, vistas, or the visual impact of development

    “community_facilities” - if it is about village halls, medical centers, community centers etc.

    "no_label" - if it does not fit any category 

    '''

    # Set your OpenAI API key
    api_key = os.environ["OPENAI_API_KEY"]

    # Initialize the OpenAI API client
    openai.api_key = api_key

    # Define the message you want to send
    message = prompt

    # Send the message to ChatGPT-4 and get a response
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": message,
            },
        ],
    )
    result = completion.choices[0].message.content
    
    return [item.strip() for item in result.split(",")]