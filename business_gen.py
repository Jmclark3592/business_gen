# generates leads from scrubbing the internet
# NOTE from gogole mapls platform you can enable maps datasets API to import data as csv or json


import googlemaps
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

Maps = googlemaps.Client(key=GOOGLE_API_KEY)
