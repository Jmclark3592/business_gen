import requests
from dotenv import load_dotenv
import os
import csv


from maps.geocode import call_google
from model.business import create_businesses, Business
from scraper.bs import scrape
from sqs_notify.send_to_sqs import send_to_sqs

QUEUE_URL = os.environ["QUEUE_URL"]
requests.packages.urllib3.disable_warnings()


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

    send_to_sqs(bus, QUEUE_URL)
    # added csv to prove we are getting emails
    # save_to_csv(bus, "output.csv")


if __name__ == "__main__":
    main()

# does COPY . /app/ on docker ensure key/variables like QUEUE_URL are sent with the image?