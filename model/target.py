from typing import List

from pydantic import BaseModel

from utils.read_json import read_json


class Target(BaseModel):
    username: str = ""
    query: str = ""
    location: str = ""


def create_target(environment: str) -> Target:
    if environment == "local":
        target_json = read_json("tests/target.json")
        return Target(**target_json)
  
    else:
        # TODO: handle json coming from somewhere that's not the test file
        print("environment not local!")
        return Target()
