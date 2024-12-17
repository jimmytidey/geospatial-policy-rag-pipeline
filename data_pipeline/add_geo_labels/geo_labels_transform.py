import openai, googlemaps, os, string

def geo_labels_transform(record):
    location_names = get_location_names(record['sections'], record['text'])
    locations =  [string.capwords(item.strip()) for item in location_names.split(",")]
    return locations

def get_location_names(title, text):
  
    prompt = f'''
    Please extract all specifc geographic locations or pysical places or buildings, return them as a comma separated list.

    These locations will be sent to a geocoding API. Please only return the comma separated list, no apologies or other text.

    If there are no locations, please return an empty string.

    Do not include casual decriptions eg. "behind the church", or other locations that could not be automatically geocoded.

    Title: {title}

    Text: {text}

    '''

    api_key = os.environ["OPENAI_API_KEY"]
    openai.api_key = api_key
    message = prompt

    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": message,
            },
        ],
    )
    return completion.choices[0].message.content

