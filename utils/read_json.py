import json


def read_json(filename: str):
    with open(filename, 'r') as json_file:
        json_data = json.load(json_file)
    
    return json_data
