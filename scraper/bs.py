import requests
import re
import urllib.parse

from bs4 import BeautifulSoup


def scrape(business):
    print("calling scrape")
    lines = extract_website_content(business.website)
    print(lines)

    return business


def extract_website_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    if not url or not url.startswith("http"):
        return ""

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get text content
        text = soup.get_text()

        # Break into lines and remove leading and trailing whitespace
        lines = (line.strip() for line in text.splitlines())

        # Drop blank lines
        clean_lines = list(line for line in lines if line)

        return "\n".join(clean_lines)

    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return ""


def extract_email_from_website(url, depth=1):
    if not url:
        return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    # If the URL doesn't start with 'http' (could be http or https), then prepend it with 'http://'
    if not url.startswith("http"):
        url = "http://" + url
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # First, try to find mailto links
        mailtos = soup.select("a[href^=mailto]")
        for i in mailtos:
            return i["href"].replace("mailto:", "")
        # If that doesn't find an email, try searching the text using regex
        email_pattern = r"[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}"
        match = re.search(email_pattern, soup.get_text())
        if match:
            return match.group(0)
        # If depth allows and we haven't found an email, follow potential "contact" links
        if depth > 0:
            contact_links = soup.select(
                'a[href*="contact"], a[href*="email"], a[href*="Contact"], a[href*="Email"]'
            )
            for link in contact_links:
                href = link.get("href")
                if href:
                    # Build a full URL if it's a relative link
                    if not href.startswith(("http://", "https://")):
                        href = urllib.parse.urljoin(url, href)
                    email = extract_email_from_website(href, depth - 1)
                    if email:
                        return email
    except Exception as e:  # This will catch all exceptions
        print(f"Error extracting email from {url}: {e}")
        return None
