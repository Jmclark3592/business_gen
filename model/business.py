from typing import List

from pydantic import BaseModel


class Business(BaseModel):
    name: str
    website: str = ""
    email: str = ""
    web_content: str = ""


def create_businesses(data) -> List[Business]:
    """Creates Business objects and populates name and website fields"""
    businesses = []

    for item in data:
        # adding name and website to Business
        business = Business(**item)
        businesses.append(business)
    
    return businesses
