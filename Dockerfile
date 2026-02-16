FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Ensure static directory structure exists with all files
RUN mkdir -p /app/data \
    /app/static/images/metals \
    /app/static/images/coins \
    /app/static/images/goldbacks && \
    echo "=== Checking static files ===" && \
    ls -la /app/static/ && \
    echo "=== Verifying favicon.png ===" && \
    ls -la /app/static/favicon.png && \
    echo "=== Verifying gb_logo.png ===" && \
    ls -la /app/static/gb_logo.png

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
