import time
import json
import csv
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import os

# Change the current working directory to the script's parent directory
os.chdir(Path(__file__).parent)

# Create the "output" folder if it doesn't exist
output_folder = Path("output")
output_folder.mkdir(exist_ok=True)

def get_url_filename(url):
    # Parse the URL
    parsed_url = urlparse(url)

    # Extract the path component of the URL
    path_components = parsed_url.path.split('/')

    # Find the filename by looking for the first non-empty path component
    for component in path_components[::-1]:
        if component:
            return f"{component}.csv"

    # If no filename is found, use a default name
    return "output.csv"

def scrape_reviews(url):
    # Use the extracted filename from the URL to name the output file
    output_file = output_folder / get_url_filename(url)

    try:
        # Try to load reviews from an existing file -- for items with many reviews, we don't want to rescrape every time
        with open(output_file, 'r', encoding='utf-8', newline='') as file:
            reader = csv.DictReader(file)
            reviews = [{'stars': row['stars'], 'review': row['review']} for row in reader]
        print(f"Reviews loaded from file {output_file}")

    except FileNotFoundError:
        # If the file doesn't exist, scrape reviews
        reviews = []

        # Start a Selenium WebDriver (in this example, I'm using Chrome)
        driver = webdriver.Chrome()

        try:
            while True:
                driver.get(url)

                # Wait for the reviews to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'reviewItem-module--message--3ed76'))
                )

                # Load in the HTML of the page
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')

                # Fine every section of reviews. There are usually 4 per page 
                review_sections = soup.find_all('div', class_='reviewItem-module--reviewItemWrap--947b9')
                
                # Within each review section, parse out individual components
                for section in review_sections:

                    # First, find every occurrence of the star icon and take the count to get the star rating for the review
                    stars_elements = section.find_all('svg', class_='cursor--pointer reviewStars-module--starIcon--3572e')
                    stars = len(stars_elements)

                    # Find the actual review text. This will be blank if there is only a star rating
                    review_text_element = section.find('p', class_='reviewItem-module--message--3ed76')
                    review_text = review_text_element.get_text() if review_text_element else ''

                    # Add onto the list of all reviews
                    reviews.append({'stars': stars, 'review': review_text})

                # Check if there is a "Next" button and it is not disabled. If either condition is met, break the loop and return reviews
                next_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Next"]')
                if 'pagination-module--inactive--11b03' in next_button.get_attribute('class') or next_button.get_attribute('disabled') == 'true':
                    break  # No more pages

                # Scroll the button into view
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)

                # Click the button using JavaScript
                driver.execute_script("arguments[0].click();", next_button)

                # Wait for the next page to load
                time.sleep(2)  # Adjust the sleep time based on your network speed and page load time

        finally:
            driver.quit()

        # Save reviews to the CSV file
        with open(output_file, 'w', encoding='utf-8', newline='') as file:
            fieldnames = ['stars', 'review']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(reviews)
        print(f"Reviews saved to file: {output_file}")

    return reviews

def main():
    # Replace 'your_url_here' with the URL of the web page you want to scrape
    url = 'https://www.quince.com/home/european-linen-double-flange-deluxe-bedding-bundle?color=aloe&productPosition=8&searchQuery=flange%20linen%20&tracker=landingPage__search_section__search_results'
    reviews = scrape_reviews(url)

    if reviews:
        for i, review in enumerate(reviews, start=1):
            print(f"Review {i} - Stars: {review['stars']}, Text: {review['review']}\n")

if (__name__) == '__main__':
    main() 
