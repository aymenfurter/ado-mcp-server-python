FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=info

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Azure DevOps specific environment variables
# These will be provided when running the container
ENV ADO_PERSONAL_ACCESS_TOKEN=""
ENV ADO_ORGANIZATION_URL=""
ENV ADO_PROJECT_NAME=""

# Server configuration
ENV PORT=8000
ENV HOST=0.0.0.0

# Expose the application port
EXPOSE ${PORT}

# Set pytest-asyncio configuration to address the deprecation warning
ENV PYTHONPATH=/app
ENV PYTEST_ADDOPTS="--asyncio-default-fixture-loop-scope=function"

# Skip tests on container startup and go straight to server
CMD ["python", "server.py"]