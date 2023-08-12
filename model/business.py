from typing import List
from pydantic import BaseModel

from scraper.bs import extract_website_content
from scraper.bs import extract_email_from_website


class Business(BaseModel):
    name: str
    website: str = ""
    email: str = ""
    web_content: str = ""


def create_businesses(data) -> List[Business]:
    businesses = []

    for item in data:
        # adding name and website to Business
        business = Business(**item)
        print("adding business")
        # adding web_content to Business
        business.web_content = extract_website_content(business.website)
        # adding email to Business
        business.email = extract_email_from_website(business.website)
        businesses.append(business)
    
    return businesses
