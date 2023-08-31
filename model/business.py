from typing import List

from pydantic import BaseModel


class Business(BaseModel):
    name: str
    website: str = ""
    email: str = ""

    def to_sqs(self):
        return {
            "name": self.name,
            "email": self.email
        }



def create_businesses(data) -> List[Business]:
    """Creates Business objects and populates name and website fields"""
    businesses = []

    for item in data:
        # adding name and website to Business
        business = Business(**item)
        businesses.append(business)
    
    return businesses
