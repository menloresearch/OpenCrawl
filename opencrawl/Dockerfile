FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app:/app/opencrawl" \
    PATH="/root/.cargo/bin:${PATH}" \
    PATHIK_TMP_DIR="/tmp/pathik_data"

# Install system dependencies including ALL Chrome requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    pkg-config \
    libssl-dev \
    # Chrome/Chromium dependencies - comprehensive list
    chromium \
    fonts-liberation \
    fonts-noto-color-emoji \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxkbcommon0 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    lsb-release \
    wget \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && rustup default stable

# Copy requirements first for better layer caching
COPY opencrawl/examples/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install opencrawl as a pip package
RUN pip install --no-cache-dir opencrawl

# Pre-download the pathik binary and ensure it has execute permissions
RUN mkdir -p /usr/local/lib/python3.9/site-packages/pathik/bin/linux_arm64/ && \
    curl -L -o /usr/local/lib/python3.9/site-packages/pathik/bin/linux_arm64/pathik_bin https://github.com/mhazarika-price/pathik/releases/download/v0.3.11/pathik_v0.3.11_linux_arm64 && \
    chmod +x /usr/local/lib/python3.9/site-packages/pathik/bin/linux_arm64/pathik_bin

# Copy the application code
COPY . /app/

# Create a temporary directory for pathik with proper permissions
RUN mkdir -p /tmp/pathik_data && chmod 777 /tmp/pathik_data

# Create a directory for Chrome cache with proper permissions
RUN mkdir -p /root/.cache/rod/browser && chmod -R 777 /root/.cache

# Expose port for FastAPI
EXPOSE 8000

# Command to run the API
CMD ["python", "opencrawl/examples/app.py"] 