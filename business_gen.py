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


# Revised version of the save_to_csv() function

def save_to_csv(businesses, filename, user_input_data):
    """Save business data to CSV file."""
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        for bus_obj in businesses:
            # Convert Business object to dictionary for easy access
            place = {
                "name": bus_obj.name,
                "website": bus_obj.website,
                "formatted_phone_number": bus_obj.phone,
                "email": bus_obj.email
            }
            
            writer.writerow([
                user_input_data['state'],
                user_input_data['city'],
                user_input_data['business_type'],
                place["name"],
                place.get("website", "N/A"),
                place.get("formatted_phone_number", "N/A"),
                place.get("email", "N/A")
            ])





def main():
    load_dotenv()


    data, user_input_data = call_google()
    print(f"Number of businesses retrieved: {len(data)}")

    # create Business objects from Maps API
    businesses = create_businesses(data)
    print(f"Number of Business objects created: {len(businesses)}")

    for bus in businesses:
        bus = scrape(bus)
        print(f"Processed business object: name='{bus.name}' website='{bus.website}' email='{bus.email}'")
        send_to_sqs(bus, QUEUE_URL)
    
    #below is just testing 1 business
    #print(f"scraping only {businesses[0].name}")
    #bus = scrape(businesses[0])
    # print(f"first fully formed business object: {bus}")
    # send_to_sqs(bus, QUEUE_URL)

    # added csv to prove we are getting emails
    save_to_csv(businesses, "output.csv", user_input_data)


if __name__ == "__main__":
    main()