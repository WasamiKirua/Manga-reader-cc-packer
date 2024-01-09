from urllib.parse import urlparse
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import requests
import zipfile

class URLValidator:
    """
    A class to validate URLs with a replaceable part.
    """
    def __init__(self, base_url):
        """
        Initializes the URLValidator with a base URL.
        """
        self.base_url = base_url

    def is_valid_url(self, replacement):
        """
        Checks if the URL with the replacement is valid.
        """

        # Replace 'REPLACEMENT' in the base URL with the actual replacement value
        url_with_replacement = self.base_url.replace('REPLACEMENT', replacement)

        # Parse the URL and validate the scheme and netloc (domain)
        parsed_url = urlparse(url_with_replacement)
        return all([parsed_url.scheme, parsed_url.netloc])
    
class Fetcher:
    @staticmethod
    async def fetcher_chapters(url):
        async with async_playwright() as p:
            # Launch the browser (Chromium, Firefox, or WebKit)
            browser = await p.chromium.launch()
            page = await browser.new_page()
            # Go to the webpage
            await page.goto(url)
            # Get the page content
            content = await page.content()
            # Parse the HTML
            tree = HTMLParser(content)
            # Find all the "li" elements with class "wp-manga-chapter"
            global chapters_list
            chapters_list = []

            for span in tree.css('span.leftoff'):
                for a_tag in span.css('a'):
                    href = a_tag.attributes.get('href')
                    if href:
                        chapters_list.append(href)

            # Close the browser
            await browser.close()

            return chapters_list
        
def setup_driver():
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run headless Chrome
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

class Processor:
    @staticmethod    
    def process_chapters(chapter_link, max_retries=3):
        driver = None
        retries = 0
        while retries < max_retries:
            try:
                # Open the webpage
                driver = setup_driver()
                driver.get(chapter_link)
                # Wait for the dropdown element to load
                time.sleep(3)
                # Find the dropdown for image loading and set it to 'all images'
                select_element = driver.find_element(By.CSS_SELECTOR, 'div.load_ch select[name="number"]')
                select_object = Select(select_element)
                select_object.select_by_value('1')
                # Wait for the images to load after changing the dropdown
                time.sleep(5)
                # Find all image elements
                img_elements = driver.find_elements(By.TAG_NAME, 'img')
                # Extract image sources
                img_srcs = [img.get_attribute('src') for img in img_elements if 'jpg' in img.get_attribute('src')]
                # img_srcs = [f"{img.get_attribute('src')}_{i+1}" for i, img in enumerate(img_elements) if 'jpg' in img.get_attribute('src')]
                # Close the browser
                driver.quit()
                # Print or process the image sources
                print(f"Processed: {chapter_link} with {len(img_srcs)} Images")
                return img_srcs
            except (NoSuchElementException, TimeoutException):
                print(f"Attempt {retries + 1} failed, retrying...")
                retries += 1
                time.sleep(5)  # Wait before retrying

            finally:
                if driver:
                    driver.quit()
        return None
    
class Downloader:
    @staticmethod
    def download_image(images_list, chapter_name, main_folder, retry_count=3):
        index_count = 0
        # Ensure directory exists
        os.makedirs(f"{main_folder}/{chapter_name}", exist_ok=True)
        for img_url in images_list:
            index_count = index_count + 1
            for attempt in range(retry_count):
                try:
                    response = requests.get(img_url, stream=True)
                    if response.status_code == 200:
                        # Construct a filename from the URL
                        filename = f"{index_count}_{img_url.split('/')[-1]}"
                        filepath = os.path.join(main_folder, chapter_name, filename)
                        with open(filepath, 'wb') as out_file:
                            for chunk in response.iter_content(chunk_size=8192):
                                out_file.write(chunk)
                        # Image downloaded successfully
                        print(f"Image downloaded successfully: {img_url}")
                        time.sleep(3)
                        break
                    else:
                        print(f"Error downloading image {img_url}: Status code {response.status_code}")
                except requests.RequestException as e:
                    print(f"An error occurred: {e}")
            else:
                print(f"Failed to download image after {retry_count} attempts: {img_url}")

class Makercbz:
    @staticmethod
    def create_cbz(main_folder, cbz_folder):
        # Initialize a dictionary to hold the file names for each subfolder
        subfolder_files = {}

        # Check if the base folder exists
        if os.path.exists(main_folder) and os.path.isdir(main_folder):
            # List all entries in the base folder
            entries = os.listdir(main_folder)
            # Filter out subfolders and sort them
            subfolders = [entry for entry in entries]
            # Sorting the chapters numerically
            sorted_chapters = sorted(subfolders, key=lambda x: float(x.split('-')[-1]))
            print(sorted_chapters)
        else:
            print(f"Error: destination folder '{main_folder}' does not exists")
        for chapter in sorted_chapters:
            chapter_path = os.path.join(main_folder, chapter)
            if os.path.isdir(chapter_path):
                # List files in the chapter folder
                chapter_files = os.listdir(chapter_path)
                # Sorting the files numerically (assuming filenames are numeric or have numeric prefixes)
                sorted_files = sorted(chapter_files, key=lambda x: int(x.split('_')[0]))
                subfolder_files[chapter] = sorted_files
        for chapter, files in subfolder_files.items():
            # Create the path for the CBZ file
            cbz_file_path = os.path.join(cbz_folder, f"{chapter}.cbz")

            # Create a ZIP file
            with zipfile.ZipFile(cbz_file_path, 'w') as zipf:
                for file in files:
                    # Add each JPG file to the ZIP archive
                    zipf.write(os.path.join(main_folder, chapter, file), file)