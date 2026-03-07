import argparse
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import aria2p
import requests
from lxml import etree
from tqdm import tqdm

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


# options = {"referer": "https://fuckingfast.co/",
#                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#                # "file-allocation": None,
#                "dir": download_dir,
#                "max-connection-per-server": str(connections),
#                "max-concurrent-downloads": str(connections),
#                "split": str(split)}


def download_with_aria2(links, download_dir, connections, split):
    """Adds multiple links as separate downloads to run in parallel."""
    try:
        aria2 = aria2p.API(
            aria2p.Client(host=config.ARIA2_HOST, port=config.ARIA2_PORT, secret=config.ARIA2_SECRET)
        )
    except Exception:
        print("Error: Could not connect to the aria2 RPC server.")
        return None

    # Global/Task options
    options = {
        "referer": "https://fuckingfast.co/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "dir": download_dir,

        # --- Performance & Connections ---
        "max-connection-per-server": str(connections),  # (Keep under 16 to avoid IP bans)
        "split": str(split),                            # (Should generally match max-connections)
        "max-concurrent-downloads": "3",                # Don't download too many *separate* files at once
        "min-split-size": "20M",                        # Prevents aria2 from splitting tiny files
        "file-allocation": "none",                      # 'none' or 'falloc' prevents freezing on startup

        # --- Reliability & Error Recovery (Anti-Failing) ---
        "continue": "true",                             # Always try to resume broken downloads
        "max-tries": "10",                              # Number of retries for dropped connections
        "retry-wait": "5",                              # Seconds to wait between retries
        "timeout": "60",                                # Close and retry connections that hang for 60s
        # "lowest-speed-limit": "50K",                    # Drop/re-establish threads that stall out completely
        "remote-time": "true"                           # Preserve the original file's timestamp
    }

    downloads = []
    try:
        for link in links:
            # Adding as a list containing one URI ensures it's treated as a unique file
            download = aria2.add_uris([link], options=options)
            downloads.append(download)

        print(f"\nSuccessfully added {len(downloads)} separate files to the queue.")

        # Optional: Force aria2 to allow more parallel slots if the server config is restrictive
        # aria2.set_global_options({"max-concurrent-downloads": "10"})

        return aria2
    except Exception as e:
        print(f"An error occurred while adding downloads to aria2: {e}")
        return None


def monitor_downloads(aria2):
    """Displays real-time, persistent progress bars for all downloads."""
    print("\n--- Initializing Download Monitors ---\n")

    # Dictionary to keep track of tqdm instances for each download GID
    bars = {}

    try:
        while True:
            downloads = aria2.get_downloads()

            # If there's absolutely nothing in the queue, we're done
            if not downloads:
                break

            active_or_waiting = [d for d in downloads if not d.is_complete and not d.is_removed]

            # Exit loop if everything is finished
            if not active_or_waiting:
                break

            for dl in active_or_waiting:
                # Initialize a new bar if we haven't seen this GID yet
                if dl.gid not in bars:
                    bars[dl.gid] = tqdm(
                        total=dl.total_length,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024,
                        desc=dl.name[:40],  # Truncate long names
                        leave=True,
                        dynamic_ncols=True
                    )

                # Update the bar to the current downloaded amount
                # We use 'n' to set the absolute position to avoid calculation errors
                bars[dl.gid].n = dl.completed_length

                # Update the speed and status in the postfix
                bars[dl.gid].set_postfix(
                    status=dl.status,
                    speed=dl.download_speed_string(),
                    refresh=False
                )
                bars[dl.gid].refresh()

            # Optional: Clean up bars for completed downloads to keep the UI tidy
            for gid in list(bars.keys()):
                dl = aria2.get_download(gid)
                if dl.is_complete:
                    bars[gid].n = dl.total_length  # Ensure it shows 100%
                    bars[gid].close()
                    del bars[gid]

            time.sleep(1)

        print("\n[✔] All downloads completed.")

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    finally:
        # Ensure all bars are closed on exit
        for bar in bars.values():
            bar.close()


def main():
    parser = argparse.ArgumentParser(description="Fetch download links and send to aria2.")
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

    aria2_api = download_with_aria2(final_links, args.dir, args.connections, args.split)
    if aria2_api and not args.no_progress:
        try:
            monitor_downloads(aria2_api)
        except KeyboardInterrupt:
            print("\nExiting progress monitor.")


if __name__ == "__main__":
    main()
