import requests
from dotenv import load_dotenv
import json
import os
import boto3
import csv


from maps.geocode import call_google
from model.business import create_businesses
from scraper.bs import scrape, extract_website_content, extract_email_from_website


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


# adding csv to prove we are obtaining them
def save_to_csv(data, filename):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Phone Number", "Address", "Website"])
        for place in data:
            writer.writerow(
                [
                    place["name"],
                    place.get("formatted_phone_number", ""),
                    place["formatted_address"],
                    place.get("website", ""),
                ]
            )


# added to prove getting emails
def append_emails_to_csv(filename, emails):
    with open(filename, mode="r") as file:
        reader = csv.reader(file)
        rows = list(reader)

    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        header = rows[0]
        header.append("Email")
        writer.writerow(header)
        for row, email in zip(rows[1:], emails):
            row.append(email)
            writer.writerow(row)


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
    save_to_sqs(data, QUEUE_URL)
    # added csv to prove we are getting emails
    save_to_csv(data, "output.csv")
    websites = [place.get("website", "") for place in data]
    emails = [extract_email_from_website(url) for url in websites]
    append_emails_to_csv("output.csv", emails)


if __name__ == "__main__":
    main()

# added functions: save to csv, append emails
# added to main: save to sqs, sqve to csv
