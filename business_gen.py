import requests
from dotenv import load_dotenv
import json
import os
import boto3
import csv

from maps.geocode import call_google
from model.business import create_businesses
from scraper.bs import scrape


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
QUEUE_URL = os.getenv("QUEUE_URL")
# ENDPOINT = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
# DETAILS_ENDPOINT = "https://maps.googleapis.com/maps/api/place/details/json?"
# NUM_DIVISIONS = 5  # Number of subdivisions in each dimension (change as needed)
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


# def extract_website_content(url):
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
#     }

#     if not url or not url.startswith("http"):
#         return ""

#     try:
#         response = requests.get(url, headers=headers, verify=False, timeout=10)
#         response.raise_for_status()

#         soup = BeautifulSoup(response.content, "html.parser")

#         # Remove script and style elements
#         for script in soup(["script", "style"]):
#             script.extract()

#         # Get text content
#         text = soup.get_text()

#         # Break into lines and remove leading and trailing whitespace
#         lines = (line.strip() for line in text.splitlines())

#         # Drop blank lines
#         clean_lines = list(line for line in lines if line)

#         return "\n".join(clean_lines)

#     except Exception as e:
#         print(f"Error extracting content from {url}: {e}")
#         return ""


# def extract_email_from_website(url, depth=1):
#     if not url:
#         return None
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
#     }
#     # If the URL doesn't start with 'http' (could be http or https), then prepend it with 'http://'
#     if not url.startswith("http"):
#         url = "http://" + url
#     try:
#         response = requests.get(url, headers=headers, verify=False)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, "html.parser")
#         # First, try to find mailto links
#         mailtos = soup.select("a[href^=mailto]")
#         for i in mailtos:
#             return i["href"].replace("mailto:", "")
#         # If that doesn't find an email, try searching the text using regex
#         email_pattern = r"[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}"
#         match = re.search(email_pattern, soup.get_text())
#         if match:
#             return match.group(0)
#         # If depth allows and we haven't found an email, follow potential "contact" links
#         if depth > 0:
#             contact_links = soup.select(
#                 'a[href*="contact"], a[href*="email"], a[href*="Contact"], a[href*="Email"]'
#             )
#             for link in contact_links:
#                 href = link.get("href")
#                 if href:
#                     # Build a full URL if it's a relative link
#                     if not href.startswith(("http://", "https://")):
#                         href = urllib.parse.urljoin(url, href)
#                     email = extract_email_from_website(href, depth - 1)
#                     if email:
#                         return email
#     except Exception as e:  # This will catch all exceptions
#         print(f"Error extracting email from {url}: {e}")
#         return None


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
    # query = input("Enter the type of business: ")
    # location_name = input("Enter the city and state (e.g. 'Tacoma, WA'): ")
    # lat, lng = geocode.geocode_location(location_name)
    # delta = 0.05  # Adjust this value as needed for city size
    # min_lat, max_lat = lat - delta, lat + delta
    # min_lng, max_lng = lng - delta, lng + delta
    # data = geocode.get_places(query, min_lat, max_lat, min_lng, max_lng)
    data = call_google()
    businesses = create_businesses(data)
    print(f"scraping only {businesses[0].name}")
    lines = scrape(businesses[0])
    # save_to_initial_queue(data, QUEUE_URL)
    # save_to_sqs(data, QUEUE_URL)
    # # added csv to prove we are getting emails
    # save_to_csv(data, "output.csv")
    # websites = [place.get("website", "") for place in data]
    # emails = [extract_email_from_website(url) for url in websites]
    # append_emails_to_csv("output.csv", emails)


if __name__ == "__main__":
    main()

# LINE 213 RETURNS EMPTY IF None...... If there is no email there is no point. It did get rid of traceback errors though.
# TO FIX: save_to_sqs is still not augmenting the SQS with email and URL. Confirmed Extract_email DOES work but its not appending..
# TO IMPROVE:
