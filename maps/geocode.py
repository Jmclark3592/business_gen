import requests
import os
from dotenv import load_dotenv
from cache.cache_data import read_cache, save_cache

#from model.target import create_target *used for testing

load_dotenv()

GEOCODE_ENDPOINT = "https://maps.googleapis.com/maps/api/geocode/json?"
DETAILS_ENDPOINT = "https://maps.googleapis.com/maps/api/place/details/json?"
TEXTSEARCH_ENDPOINT = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
NUM_DIVISIONS = 2  # Number of subdivisions in each dimension (change as needed)
ENVIRONMENT = os.getenv("ENVIRONMENT")


def geocode_location(location):
    """geocode_location takes location [str] and calls Google Maps API to get
    lat and long [int, int]. Currently stores lat/lng in local file.
    """
    # Attempt to read from cache
    cached_data = read_cache("latlong_cache.json")
    
    # Check if the location is already in the cache
    if location in cached_data:
        return cached_data[location]["lat"], cached_data[location]["lng"]
    
    # If not in cache, proceed with API call
    params = {"address": location, "key": GOOGLE_API_KEY}
    response = requests.get(GEOCODE_ENDPOINT, params=params)
    data = response.json()
    if data["status"] == "OK":
        lat = data["results"][0]["geometry"]["location"]["lat"]
        lng = data["results"][0]["geometry"]["location"]["lng"]
        
        # Save the obtained lat/lng to cache for future use
        cached_data[location] = {"lat": lat, "lng": lng}
        save_cache("latlong_cache.json", cached_data)
        
        return lat, lng
    else:
        raise ValueError(
            f"Error geocoding location {location}. Error message: {data['status']}"
        )




def subdivide_region(min_lat, max_lat, min_lng, max_lng, num_divisions):
    """Takes lat, long and returns a grids [List of lat, long]"""
    lat_step = (max_lat - min_lat) / num_divisions
    lng_step = (max_lng - min_lng) / num_divisions
    grids = []
    for i in range(num_divisions):
        for j in range(num_divisions):
            grid_min_lat = min_lat + i * lat_step
            grid_max_lat = grid_min_lat + lat_step
            grid_min_lng = min_lng + j * lng_step
            grid_max_lng = grid_min_lng + lng_step
            grids.append((grid_min_lat, grid_max_lat, grid_min_lng, grid_max_lng))
    return grids


def get_places_for_grid(query, min_lat, max_lat, min_lng, max_lng):
    """Handles pagination"""
    location = f"{(min_lat+max_lat)/2},{(min_lng+max_lng)/2}"  # Use the center of the grid as location
    parameters = {
        "query": query,
        "location": location,
        "key": GOOGLE_API_KEY,
        "radius": 2000,
    }  # Adjust the radius as needed
    all_results = []
    response = requests.get(TEXTSEARCH_ENDPOINT, params=parameters)
    results = response.json().get("results", [])
    all_results.extend(results)
    # Handle pagination
    while "next_page_token" in response.json():
        parameters["pagetoken"] = response.json()["next_page_token"]
        response = requests.get(TEXTSEARCH_ENDPOINT, params=parameters)
        results = response.json().get("results", [])
        all_results.extend(results)
    return all_results


def get_place_details(place_id):
    parameters = {"place_id": place_id, "key": GOOGLE_API_KEY}
    response = requests.get(DETAILS_ENDPOINT, params=parameters)
    return response.json().get("result", {})


def get_places(query, min_lat, max_lat, min_lng, max_lng):
    """Takes query and lat, long and returns unique set of places
    Do not cache this as the API calls are for business info only"""
    grids = subdivide_region(min_lat, max_lat, min_lng, max_lng, NUM_DIVISIONS)
    all_results = []
    for grid in grids:
        grid_results = get_places_for_grid(query, *grid)
        all_results.extend(grid_results)
    # Removing potential duplicates
    seen_place_ids = set()
    unique_results = []
    for place in all_results:
        if place["place_id"] not in seen_place_ids:
            seen_place_ids.add(place["place_id"])
            unique_results.append(place)
    # Fetch additional details for unique results
    for idx, place in enumerate(unique_results):
        details = get_place_details(place["place_id"])
        unique_results[idx].update(details)
    return unique_results



def call_google():
    print("Starting call_google() function...")
    
    # Collecting multiple business types from the user
    business_types = []
    while True:
        query = input("Enter a type of business (or type 'exit' to proceed): ")
        if query.lower() == 'exit':
            break
        business_types.append(query)
    
    location_name = input("Enter the city and state (e.g. 'Tacoma, WA'): ")
    location_name = location_name.upper()
    
    # Extract city and state from location_name
    city = location_name.split(",")[0].strip()
    state = location_name.split(",")[1].strip()

    #target = create_target(ENVIRONMENT) *used for testing
    lat, lng = geocode_location(location_name) #(target.location_name) *when in ENVIRONMENT
    delta = 0.05  # Adjust this value as needed for city size
    min_lat, max_lat = lat - delta, lat + delta
    min_lng, max_lng = lng - delta, lng + delta
    
    all_data = []
    for business_type in business_types:
        data = get_places(business_type, min_lat, max_lat, min_lng, max_lng)
        all_data.extend(data)

    user_input_data = {
        'business_types': business_types,
        'city': city,
        'state': state
    }
    print("Finishing call_google() function...")
    return all_data, user_input_data


if __name__ == '__main__':
    call_google()