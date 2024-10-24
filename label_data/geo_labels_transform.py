import openai, googlemaps, os

def geo_labels_transform(record):
    location_names = get_location_names(record[1], record[2])

    locations = [] 
    for location_name in location_names.split(","):
        locations.append(geocode(location_name, 'leeds'))


def get_location_names(title, text):
  
    prompt = f'''
    Please extract all specifc geographic locations or pysical places or buildings, return them as a comma separated list.

    Do not include casual decriptions eg. "behind the church". 

    Title: {title}

    Text: {text}

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
    return completion.choices[0].message.content

def geocode(search_string, place_name):
    print(f"Geocoding: {search_string}")
    
    gmaps = googlemaps.Client(key=os.environ["GOOGLEMAPS_API_KEY"])
    geocode_result = gmaps.geocode(search_string + ", Leeds, UK")

    print(geocode_result)

    if geocode_result:
        # Extract the latitude, longitude, and formatted address
        location = geocode_result[0]['geometry']['location']
        lat = location['lat']
        lng = location['lng']
        formatted_address = geocode_result[0]['formatted_address']
        
        return {'location_name': search_string, 'lat': lat, 'lng': lng, 'formatted_address': formatted_address}
    else:
        print(f"Error geocoding {place_name}: No results found")
        return False