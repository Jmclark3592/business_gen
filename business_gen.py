import requests
from dotenv import load_dotenv
import json
import os
import boto3

from maps.geocode import call_google
from model.business import create_businesses
from scraper.bs import scrape


QUEUE_URL = os.getenv("QUEUE_URL")
requests.packages.urllib3.disable_warnings()


def send_to_sqs(queue_url: str, business: Business):
    # Initialize the SQS client
    sqs = boto3.client("sqs")
    # Convert the Business object to JSON
    message_body = i.json()

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

    # get email
    # TODO: this func only takes one
    bus = scrape(businesses[0])

    print(f"first fully formed business object: {bus}")

    # TODO: write business object to queue


if __name__ == "__main__":
    main()

# LINE 213 RETURNS EMPTY IF None...... If there is no email there is no point. It did get rid of traceback errors though.
# TO FIX: save_to_sqs is still not augmenting the SQS with email and URL. Confirmed Extract_email DOES work but its not appending..
# TO IMPROVE:
