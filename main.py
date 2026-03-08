import argparse
import re
import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from lxml import etree

import config

# Initialize a global session to handle connection pooling for efficiency
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})


def fetch_intermediate_links(url):
    """Fetches the intermediate pages that contain the final download links."""
    print(f"Fetching intermediate links from: {url}")
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

    parser = etree.HTMLParser()
    tree = etree.fromstring(response.content, parser)
    return tree.xpath('//a[contains(@href, "fuckingfast.co")]/@href')


def fetch_single_final_link(link):
    """Worker function to fetch one intermediate page and extract the final link."""
    try:
        response = session.get(link, timeout=10)
        response.raise_for_status()
        link_regex = re.compile(r'window\.open\("(https://fuckingfast\.co/dl/[^"]+)"\)')
        match = link_regex.search(response.text)
        if match:
            return match.group(1)
    except requests.exceptions.RequestException:
        # Errors are ignored for single link fetches to not stop the whole process
        pass
    return None


def extract_final_download_links(intermediate_links):
    """Visits each intermediate link in parallel to extract the final download URL."""
    final_links = []
    print(f"Found {len(intermediate_links)} intermediate links. Now extracting final links in parallel...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_link = {executor.submit(fetch_single_final_link, link): link for link in intermediate_links}

        for i, future in enumerate(as_completed(future_to_link)):
            result = future.result()
            if result:
                final_links.append(result)
            # Print a progress bar
            print(f"\r  Processed {i + 1}/{len(intermediate_links)} pages... Found {len(final_links)} final links.",
                  end="")

    print("\nExtraction complete.")
    return final_links


def download_with_surge(links, download_dir, connections, split):
    """Downloads files using the Surge CLI tool in batch mode."""
    print(f"\nStarting download with Surge to {download_dir}...")

    # Ensure download directory exists
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir)
        except OSError as e:
            print(f"Error creating download directory: {e}")
            return

    # Create urls.txt file
    urls_file_path = "urls.txt"
    try:
        with open(urls_file_path, "w") as f:
            for link in links:
                f.write(f"{link}\n")
        print(f"Successfully wrote {len(links)} URLs to {urls_file_path}")
    except IOError as e:
        print(f"Error writing to {urls_file_path}: {e}")
        return

    # Construct the Surge command
    # surge --batch urls.txt --output <directory> --exit-when-done
    command = ["surge", "server","--batch", urls_file_path, "--output", download_dir, "--exit-when-done"]

    print(f"Executing: {' '.join(command)}")

    try:
        # Run the command and stream output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Stream stdout
        for line in process.stdout:
            print(line, end="")
        
        # Capture stderr
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"\nSTDERR:\n{stderr_output}")

        process.wait()
        
        if process.returncode == 0:
            print("\nSurge finished successfully.")
        else:
            print(f"\nSurge exited with error code {process.returncode}.")

    except FileNotFoundError:
        print("\nError: 'surge' command not found. Please ensure Surge CLI is installed and in your PATH.")
        print("Install via Homebrew (macOS/Linux): brew install surge-downloader/tap/surge")
        print("Install via Winget (Windows): winget install surge-downloader.surge")
    except Exception as e:
        print(f"\nAn unexpected error occurred while running Surge: {e}")
    finally:
        pass


def main():
    parser = argparse.ArgumentParser(description="Fetch download links and download using Surge CLI.")
    parser.add_argument("url", help="The URL to scrape for download links.")
    parser.add_argument("--dir", default=config.DEFAULT_DOWNLOAD_DIR,
                        help=f"Download directory (default: {config.DEFAULT_DOWNLOAD_DIR}).")
    parser.add_argument("-x", "--connections", type=int, default=config.DEFAULT_CONNECTIONS,
                        help=f"Max connections per server (default: {config.DEFAULT_CONNECTIONS}).")
    parser.add_argument("-s", "--split", type=int, default=config.DEFAULT_SPLIT,
                        help=f"Split a file into parts (default: {config.DEFAULT_SPLIT}).")
    parser.add_argument("--no-progress", action="store_true", help="Disable the live progress display.")
    args = parser.parse_args()

    intermediate_links = fetch_intermediate_links(args.url)
    if not intermediate_links:
        print("No intermediate links found. Exiting.")
        return

    final_links = extract_final_download_links(intermediate_links)
    if not final_links:
        print("No final download links could be extracted. Exiting.")
        return

    download_with_surge(final_links, args.dir, args.connections, args.split)


if __name__ == "__main__":
    main()
