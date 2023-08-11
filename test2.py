from bs4 import BeautifulSoup
import requests


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


# Test the function
url = "https://www.brandography.com/"
print(extract_website_content(url))
