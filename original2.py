"""OK i have a better idea. Let's get rid of the second queue and instead write 
a pydantic model that has 4 fields (business name, url, email and web content).
 The business name and url will come from my call to Google API and then bueatiful 
 soup will output the email and webpage contents. The purpose is to collect the business name 
 and url from Google Maps API, use that url to extract email and web page contents and then the 
 next phase (dont worry about this yet) we will use the web page contents to write an email that 
 is personalized based on what the web page does. So I need all four of those components to be passed 
 thru the SQS. Can you modify this code to accomplish that? You can get rid of all things related to the 
 SECOND_QUEUE and enriched data stuff because I think with the class 
you create we just need the first queue."""

import requests
from dotenv import load_dotenv
import json
from bs4 import BeautifulSoup
import os
import re
import urllib.parse
import boto3
import csv


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QUEUE_URL = os.getenv("QUEUE_URL")
SECOND_QUEUE_URL = os.getenv("SECOND_QUEUE_URL")
ENDPOINT = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
DETAILS_ENDPOINT = "https://maps.googleapis.com/maps/api/place/details/json?"
GEOCODE_ENDPOINT = "https://maps.googleapis.com/maps/api/geocode/json?"

NUM_DIVISIONS = 5  # Number of subdivisions in each dimension (change as needed)

requests.packages.urllib3.disable_warnings()


def geocode_location(location):
    params = {"address": location, "key": GOOGLE_API_KEY}
    response = requests.get(GEOCODE_ENDPOINT, params=params)
    data = response.json()

    if data["status"] == "OK":
        lat = data["results"][0]["geometry"]["location"]["lat"]
        lng = data["results"][0]["geometry"]["location"]["lng"]
        return lat, lng
    else:
        raise ValueError(
            f"Error geocoding location {location}. Error message: {data['status']}"
        )


def subdivide_region(min_lat, max_lat, min_lng, max_lng, num_divisions):
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
    location = f"{(min_lat+max_lat)/2},{(min_lng+max_lng)/2}"  # Use the center of the grid as location
    parameters = {
        "query": query,
        "location": location,
        "key": GOOGLE_API_KEY,
        "radius": 2000,
    }  # Adjust the radius as needed

    all_results = []
    response = requests.get(ENDPOINT, params=parameters)
    results = response.json().get("results", [])
    all_results.extend(results)
    # Handle pagination
    while "next_page_token" in response.json():
        parameters["pagetoken"] = response.json()["next_page_token"]
        response = requests.get(ENDPOINT, params=parameters)
        results = response.json().get("results", [])
        all_results.extend(results)

    return all_results


def get_places(query, min_lat, max_lat, min_lng, max_lng):
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


def get_place_details(place_id):
    parameters = {"place_id": place_id, "key": GOOGLE_API_KEY}

    response = requests.get(DETAILS_ENDPOINT, params=parameters)
    return response.json().get("result", {})


import json  # Add this import to the top of your code


def save_to_initial_queue(data, queue_url):
    initial_data = []

    for place in data:
        item = {
            "Name": place["name"],
            "Address": place["formatted_address"],
            "Website": place.get("website", ""),
        }
        initial_data.append(item)

    send_to_sqs(initial_data, queue_url)


def save_to_enriched_queue(data, queue_url):
    enriched_data = []

    for place in data:
        website = place.get("Website", "")
        email = extract_email_from_website(website)

        if email:  # This line ensures only businesses with emails get added
            item = {
                "Name": place["Name"],
                "Address": place["Address"],
                "Website": website,
                "Email": email,
                "PageContent": extract_website_content(website) if website else "",
            }
            enriched_data.append(item)

    send_to_sqs(enriched_data, queue_url)


def extract_website_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    if not url or not url.startswith("http"):
        return ""

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return ""


def extract_email_from_website(url, depth=1):
    if not url:
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    # If the URL doesn't start with 'http' (could be http or https), then prepend it with 'http://'
    if not url.startswith("http"):
        url = "http://" + url

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # First, try the earlier method to find mailto links
        mailtos = soup.select("a[href^=mailto]")
        for i in mailtos:
            return i["href"].replace("mailto:", "")

        # If that doesn't find an email, try searching the text using regex
        email_pattern = r"[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}"
        match = re.search(email_pattern, soup.get_text())
        if match:
            return match.group(0)

        # If depth allows and we haven't found an email, follow potential "contact" links
        if depth > 0:
            contact_links = soup.select(
                'a[href*="contact"], a[href*="email"], a[href*="Contact"], a[href*="Email"]'
            )
            for link in contact_links:
                href = link.get("href")
                if href:
                    # Build a full URL if it's a relative link
                    if not href.startswith(("http://", "https://")):
                        href = urllib.parse.urljoin(url, href)
                    email = extract_email_from_website(href, depth - 1)
                    if email:
                        return email

    except Exception as e:  # This will catch all exceptions
        print(f"Error extracting email from {url}: {e}")
        return None


def send_to_sqs(data, queue_url):
    sqs = boto3.client("sqs", region_name="us-east-2")  # might be east-1
    for item in data:
        try:
            response = sqs.send_message(
                QueueUrl=queue_url, MessageBody=json.dumps(item)
            )
            print(f"Message sent with ID: {response['MessageId']}")
        except Exception as e:
            print(f"Error sending message to SQS: {e}")


def main():
    query = input("Enter the type of business: ")
    location_name = input("Enter the city and state (e.g. 'Tacoma, WA'): ")

    lat, lng = geocode_location(location_name)
    delta = 0.05  # Adjust this value as needed for city size

    min_lat, max_lat = lat - delta, lat + delta
    min_lng, max_lng = lng - delta, lng + delta

    data = get_places(query, min_lat, max_lat, min_lng, max_lng)
    save_to_initial_queue(data, QUEUE_URL)

    # Now fetch the enriched data and save to the second queue
    save_to_enriched_queue(data, SECOND_QUEUE_URL)


if __name__ == "__main__":
    main()