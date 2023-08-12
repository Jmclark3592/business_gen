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


def save_to_initial_queue(data, queue_url):
    initial_data = []

    for place in data:
        item = {
            "Name": place["name"],
            "Address": place["formatted_address"],
            "Website": place.get("website", ""),
        }
        initial_data.append(item)
    send_to_sqs(initial_data, queue_url)


def send_to_sqs(data, queue_url):
    sqs = boto3.client("sqs", region_name="us-east-2")
    for item in data:
        try:
            response = sqs.send_message(
                QueueUrl=queue_url, MessageBody=json.dumps(item)
            )
            print(f"Message sent with ID: {response['MessageId']}")
        except Exception as e:
            print(f"Error sending message to SQS: {e}")


def save_to_sqs(data, queue_url):
    sqs = boto3.client("sqs", region_name="us-east-2")
    for item in data:
        business_data = BusinessData(
            business_name=item.get("Name", "Default Name"),
            url=item.get("Website", ""),
            email=extract_email_from_website(item.get("Website", ""))
            or "",  # Use empty string if None is returned
            web_content=extract_website_content(item.get("Website", "")),
        )

        try:
            response = sqs.send_message(
                QueueUrl=queue_url, MessageBody=json.dumps(business_data.dict())
            )
            print(f"Message sent with ID: {response['MessageId']}")
        except Exception as e:
            print(f"Error sending message to SQS: {e}")


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
