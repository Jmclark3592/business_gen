# generates leads from scrubbing the internet
# NOTe from gogole mapls platform you can enable maps datasets API to import data as csv or json
# get around 120 limit *viewable* places on GMaps scraper https://www.youtube.com/watch?v=op9MabaZNZo
# 1 query per second (QPS) API limit with GPlaces

import googlemaps
import requests
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
phone = "16123417555"

url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=%2B{phone}&inputtype=phonenumber&key={GOOGLE_API_KEY}"

payload = {}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
