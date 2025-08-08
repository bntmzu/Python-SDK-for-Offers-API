# Dockerfile
# Purpose: Run Offers SDK CLI inside a minimal production container.

FROM python:3.11-slim

# Install Poetry (package manager)
RUN pip install --no-cache-dir poetry

# Set working directory
WORKDIR /app

# Copy dependency declarations first
COPY pyproject.toml poetry.lock* README.md /app/

# Copy source code first for poetry install
COPY src/ /app/src/

# Install only production dependencies (no dev tools)
RUN poetry config virtualenvs.create false \
 && poetry install --only main \
 && poetry config virtualenvs.in-project false

# Copy the rest of the source code
COPY . /app

# Set Python path
ENV PYTHONPATH=/app/src
