# FitFuckingFast (ffdl)

**FitFuckingFast** is a high-performance, automated download link extractor and downloader designed specifically for **FitGirl Repacks**. It scrapes a given FitGirl game page, extracts all download links hosted on **fuckingfast.co**, and sends them directly to the **Surge** download manager for maximum speed.

This tool solves the tedious problem of manually clicking through dozens of intermediate pages to get the actual download links. It automates the entire process, from scraping the initial page to managing the downloads in parallel.

## 🚀 Features

*   **Automated Scraping**: simply provide a FitGirl Repack URL, and the tool does the rest.
*   **Smart Link Extraction**: Navigates through intermediate redirection pages to find the final, direct `fuckingfast.co` download URLs.
*   **Parallel Processing**: Uses multi-threading to fetch and parse multiple pages simultaneously, significantly reducing the time to start downloading.
*   **Surge Integration**: Seamlessly integrates with the **Surge CLI** (a high-performance, batch-capable downloader) to handle the actual file downloading.
*   **Live Progress Monitoring**: Displays real-time download progress directly from the Surge CLI.
*   **Cross-Platform**: Runs on Windows, macOS, and Linux (including Docker support).
*   **Modern Stack**: Built with Python and `uv` for blazing fast dependency management.

## 📋 Prerequisites

Before running the tool, ensure you have the following installed:

1.  **Surge CLI**: The core download engine.
    *   **Windows**: `winget install surge-downloader.surge`
    *   **macOS / Linux**: `brew install surge-downloader/tap/surge`
2.  **uv** (Optional but recommended): A fast Python package manager. The provided scripts will attempt to install it automatically if missing.

## 🛠️ Installation & Usage

### Option 1: Docker (Recommended)

The Docker image bundles everything you need (Python, dependencies, Surge).

1.  **Build the image**:
    ```bash
    docker build -t ffdl .
    ```

2.  **Run the container**:
    Mount a local directory to save your downloads.
    ```bash
    # Syntax: docker run --rm -v <HOST_DIR>:/app/downloads ffdl "<FITGIRL_URL>"

    docker run --rm -v ~/Downloads/Games:/app/downloads ffdl "https://fitgirl-repacks.site/cyberpunk-2077/"
    ```

### Option 2: Linux / macOS

1.  **Clone or download** this repository.
2.  **Make the script executable**:
    ```bash
    chmod +x run.sh
    ```
3.  **Run the script**:
    ```bash
    ./run.sh "https://fitgirl-repacks.site/cyberpunk-2077/"
    ```
    *The script will automatically set up a virtual environment, install dependencies, check for Surge (installing via Homebrew if missing), and begin the download.*

### Option 3: Windows

1.  **Clone or download** this repository.
2.  **Run the batch file**:
    ```cmd
    run.bat "https://fitgirl-repacks.site/cyberpunk-2077/"
    ```
    *The script will check for `winget`, `uv`, and `surge`, prompting to install them if missing.*

## ⚙️ Configuration & Arguments

You can customize the behavior using command-line arguments:

| Argument | Default | Description |
| :--- | :--- | :--- |
| `url` | *Required* | The URL of the FitGirl Repack page to scrape. |
| `--dir` | `/downloads/new_dex` | The directory where files will be saved. |
| `-x`, `--connections` | `16` | Maximum number of connections per server (speeds up downloads). |
| `-s`, `--split` | `1` | Number of pieces to split each file into. |
| `--no-progress` | `False` | Disable the live progress display. |

**Example:**
```bash
./run.sh "https://fitgirl-repacks.site/game-name/" --dir "./my_games" --connections 32
```

## 🔧 Troubleshooting

*   **"surge command not found"**: Ensure `surge` is in your system's PATH. On Windows, you might need to restart your terminal after installation.
*   **Download Stuck/Slow**: `fuckingfast.co` sometimes limits speeds or connections. Try reducing `--connections` if you encounter issues.
*   **Script crashes immediately**: Check your internet connection and ensure the FitGirl URL is valid and accessible.

## ⚠️ Disclaimer

This tool is for educational purposes only. The developers are not responsible for how this tool is used. Please respect copyright laws and the terms of service of the websites you visit.
