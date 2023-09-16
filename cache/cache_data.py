import json

"""stores cached long/lat to reduce API calls"""

def read_cache(file):
    with open(file, 'r') as file:
        data = json.load(file)
    return data

def save_cache(file, data):
    with open(file, 'w') as file:
        json.dump(data, file)