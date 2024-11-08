import openai, googlemaps, os

def geo_labels_transform(record):
    location_names = get_location_names(record[1], record[2])

    locations = [] 
    for location_name in location_names.split(","):
        location_name_clean = location_name.strip().title()
        locations.append(geocode(location_name_clean, 'leeds'))

    print(f"Extracted locations: {locations}")
    return locations

def get_location_names(title, text):
  
    prompt = f'''
    Please extract all specifc geographic locations or pysical places or buildings, return them as a comma separated list.

    Do not include casual decriptions eg. "behind the church". 

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

def geocode(search_string, place_name):
  
    gmaps = googlemaps.Client(key=os.environ["GOOGLEMAPS_API_KEY"])
    geocode_result = gmaps.geocode(search_string + ", Leeds, UK")

    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        lat = location['lat']
        lng = location['lng']
        formatted_address = geocode_result[0]['formatted_address']
        
        return {'location_name': search_string, 'lat': lat, 'lng': lng, 'formatted_address': formatted_address}
    else:
        print(f"Error geocoding {place_name}: No results found")
        return False