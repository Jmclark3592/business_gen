# generates leads from scrubbing the internet
# 1 query per second (QPS) API limit with GPlaces
# Change delta for more results? Change NUM_DIVISIONS for more results?
# LOCAL business generator without AWS SQS

import requests
from dotenv import load_dotenv
import json
from bs4 import BeautifulSoup
import os
import re
import urllib.parse
import boto3
from pydantic import BaseModel


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QUEUE_URL = os.getenv("QUEUE_URL")
SQS_REGION = os.getenv("SQS_REGION", "us-east-2")
ENDPOINT = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
DETAILS_ENDPOINT = "https://maps.googleapis.com/maps/api/place/details/json?"
GEOCODE_ENDPOINT = "https://maps.googleapis.com/maps/api/geocode/json?"

NUM_DIVISIONS = 5  # Number of subdivisions in each dimension (change as needed)

requests.packages.urllib3.disable_warnings()


class BusinessData(BaseModel):
    business_name: str
    url: str = ""  # Default empty string
    email: str = ""
    web_content: str = ""


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


# new get_places
def get_places(
    query, min_lat, max_lat, min_lng, max_lng, depth=1, max_depth=3, threshold=1000
):
    """Fetch businesses in the given bounding box."""
    location = (
        f"{(min_lat+max_lat)/2},{(min_lng+max_lng)/2}"  # Center of the bounding box
    )
    radius = 2000  # Adjust based on your needs; this is an example value

    params = {
        "query": query,
        "location": location,
        "radius": radius,
        "key": GOOGLE_API_KEY,
    }

    response = requests.get(ENDPOINT, params=params)

    # Check for a successful response
    try:
        response.raise_for_status()
        data = response.json()

        if "results" not in data:
            raise ValueError(
                f"Unexpected API response format. Response: {response.text}"
            )

    except requests.RequestException as e:
        print(f"Error querying the API: {e}")
        print(f"Response content: {response.text}")
        return []

    # Dynamic subdivision logic
    if len(data["results"]) >= threshold and depth < max_depth:
        mid_lat = (min_lat + max_lat) / 2
        mid_lng = (min_lng + max_lng) / 2

        # Quadrants
        nw = get_places(query, mid_lat, max_lat, min_lng, mid_lng, depth + 1, max_depth)
        ne = get_places(query, mid_lat, max_lat, mid_lng, max_lng, depth + 1, max_depth)
        sw = get_places(query, min_lat, mid_lat, min_lng, mid_lng, depth + 1, max_depth)
        se = get_places(query, min_lat, mid_lat, mid_lng, max_lng, depth + 1, max_depth)

        return nw + ne + sw + se

    return data["results"]  # Return the businesses found


def get_place_details(place_id):
    parameters = {"place_id": place_id, "key": GOOGLE_API_KEY}

    response = requests.get(DETAILS_ENDPOINT, params=parameters)
    return response.json().get("result", {})


def extract_email_from_soup(soup, depth=1, base_url=None):
    if not soup:
        return None

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
                if not href.startswith(("http://", "https://")) and base_url:
                    href = urllib.parse.urljoin(base_url, href)
                nested_soup = fetch_website_content(href)
                email = extract_email_from_soup(nested_soup, depth - 1, base_url=href)
                if email:
                    return email

    return None


def fetch_website_content(url, headers=None):
    if not headers:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    # Check if the URL is not empty or just a protocol
    if not url or not url.startswith(("http://", "https://")):
        print(f"Invalid or empty URL: {url}")
        return None

    if not url.startswith("http"):
        url = "http://" + url

    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching content from {url}: {e}")
        return None


def save_to_sqs(data, queue_url):
    sqs = boto3.client("sqs", region_name=SQS_REGION)
    for item in data:
        website = item.get("Website", "")
        soup = fetch_website_content(website)
        email = extract_email_from_soup(soup)
        web_content = (
            None
            if not soup
            else "\n".join(
                line.strip() for line in soup.get_text().splitlines() if line.strip()
            )
        )

        if email and web_content:  # Check if both email and web_content are present
            business_data = BusinessData(
                business_name=item["Name"],
                url=website,
                email=email,
                web_content=web_content,
            )

            try:
                response = sqs.send_message(
                    QueueUrl=queue_url, MessageBody=json.dumps(business_data.dict())
                )
                print(f"Message sent with ID: {response['MessageId']}")
            except Exception as e:
                print(f"Error sending message to SQS: {e}")
                import traceback

                traceback.print_exc()


def main():
    query = input("Enter the type of business: ")
    location_name = input("Enter the city and state (e.g. 'Tacoma, WA'): ")

    # Assuming you have a geocode_location function to fetch the central latitude and longitude
    lat, lng = geocode_location(location_name)

    delta = 0.05  # Adjust this value based on the initial size of the region
    data = get_places(query, lat - delta, lat + delta, lng - delta, lng + delta)
    save_to_sqs(data, QUEUE_URL)


if __name__ == "__main__":
    main()
