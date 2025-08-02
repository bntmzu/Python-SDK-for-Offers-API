# Dockerfile
# Purpose: Run Offers SDK CLI inside a minimal production container.

FROM python:3.11-slim

# Install Poetry (package manager)
RUN pip install --no-cache-dir poetry

# Set working directory
WORKDIR /app

# Copy dependency declarations and source code first
COPY pyproject.toml poetry.lock* README.md /app/
COPY src/ /app/src/

# Install only required dependencies (excluding dev)
RUN poetry config virtualenvs.create false \
 && poetry install --only main,cli,cache,aiohttp,requests

# Copy the rest of the source code
COPY . /app

# Define CLI entrypoint (set in pyproject.toml -> [project.scripts])
ENTRYPOINT ["offers-cli"]
