import requests
from dotenv import load_dotenv
import json
import os
import boto3

from maps.geocode import call_google
from model.business import create_businesses
from scraper.bs import scrape
from model.business import Business

QUEUE_URL = os.getenv("QUEUE_URL")
requests.packages.urllib3.disable_warnings()


def send_to_sqs(queue_url: str, business: Business):
    # Initialize the SQS client
    sqs = boto3.client("sqs", region_name="us-east-2")
    # Convert the Business object to JSON
    message_body = business.model_dump_json()

    # Send the message to SQS
    try:
        response = sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)
        print("Message ID:", response["MessageId"])
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        print("Error sending message to SQS:", e)


def main():
    load_dotenv()
    # get data from Google Maps API
    data = call_google()

    # create Business objects from Maps API
    businesses = create_businesses(data)
    print(f"scraping only {businesses[0].name}")
    print(businesses)

    # get email
    # TODO: this func only takes one
    bus = scrape(businesses[0])

    print(f"first fully formed business object: {bus}")

    # TODO: write business object to queue
    send_to_sqs(QUEUE_URL, bus)


if __name__ == "__main__":
    main()

"""
CAN-SPAM Act
legal agreement stored for each user
all gpt emails must have client bus name and location
all gpt emails must have opt out option
each email result is put in user profile database
if opt out, database reflects DND
if email has DND, do not add to SQS
"""
