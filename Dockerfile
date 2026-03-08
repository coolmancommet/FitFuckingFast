# Use a slim Python image as a base
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install uv, the fast Python package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Surge CLI
# Download the latest Linux binary directly
RUN curl -L -o /usr/local/bin/surge https://github.com/surge-downloader/surge/releases/latest/download/surge_linux_amd64 && \
    chmod +x /usr/local/bin/surge

# Copy project files
COPY pyproject.toml uv.lock ./
COPY main.py config.py ./
COPY run.sh ./

# Install Python dependencies using uv
# We don't use --frozen here to allow the lockfile to update if pyproject.toml changed
RUN uv sync

# Make the run script executable
RUN chmod +x run.sh

# Create a volume for downloads
VOLUME /app/downloads

# Set the entrypoint to the run script
ENTRYPOINT ["./run.sh"]
