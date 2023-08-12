from typing import List
from pydantic import BaseModel


class Business(BaseModel):
    name: str
    website: str = ""  # Default empty string
    email: str = ""
    web_content: str = ""


def create_businesses(data) -> List[Business]:
    businesses = []

    for item in data:
        business = Business(**item)
        print("adding business")
        print(business.name)
        print(business.website)
        businesses.append(business)
    
    return businesses
