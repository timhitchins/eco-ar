# Base image
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Set ARGs and ENVs
ARG POETRY_VERSION=1.8.3
ENV POETRY_VERSION=${POETRY_VERSION} \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/home/vscode/.venv \
    POETRY_VIRTUALENVS_CREATE=false \
    DISPLAY=99

# Update PATH
ENV PATH=$VIRTUAL_ENV/bin:/root/.local/bin:/home/vscode/.ebcli-virtual-env/.ebcli-virtual-env/executables:$PATH

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y --no-install-recommends \
    gdal-bin \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    gcc \
    curl \
    wget \
    unzip \
    jq && \
    # Install Google Chrome
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Setup Chrome and ChromeDriver
RUN CHROME_VERSION=$(google-chrome-stable --version | awk '{print $3}' | cut -d'.' -f1) && \
    CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone.json" | jq -r ".milestones.\"${CHROME_VERSION}\".version") && \
    wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip -o /tmp/chromedriver.zip -d /tmp && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64

# Switch to non-root user
USER vscode

# Setup Python environment
RUN pip install pipx && \
    pipx install poetry==${POETRY_VERSION} && \
    python -m venv ${VIRTUAL_ENV}

# Set working directory and install dependencies
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root