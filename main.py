import asyncio
import os
from utilities import URLValidator, Fetcher, Processor, Downloader, Makercbz

async def main():
    url_input = input("Enter the Mangaforfree URL: ")

    # Validate URL
    url_replacement = url_input.split('/')[-1]
    base_url = "https://mangareader.cc/manga/REPLACEMENT"
    url_validator = URLValidator(base_url)
    is_valid = url_validator.is_valid_url(url_replacement)

    # Run fetchers
    if is_valid:
        # Set vars to build main folder's name
        folder_first = url_replacement.split('-')[-2]
        folder_last = url_replacement.split('-')[-1]
        main_folder = f"{folder_first.title()}{folder_last.title()}"
        # Create main folder with uppercase
        os.makedirs(f"{main_folder}/chapters", exist_ok=True)
        os.makedirs(f"{main_folder}/CBZ_files", exist_ok=True)
        # Fetch chapters
        # chapters_list = await Fetcher.fetcher_chapters(url_input)
        # for chapter_link in reversed(chapters_list):
            # Destination folder's name
            # chapter_name = chapter_link.split('/')[-1]
            # Add safe wait
            # await asyncio.sleep(delay=5)
            # images_list = Processor.process_chapters(chapter_link)
            # Downloader.download_image(images_list, chapter_name, main_folder=f"{main_folder}/chapters")
            #await asyncio.sleep(3)  # Wait for 5 seconds between downloads
        Makercbz.create_cbz(main_folder=f"{main_folder}/chapters", cbz_folder=f"{main_folder}/CBZ_files")
asyncio.run(main())