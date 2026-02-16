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
    ls -la /app/static/images/ && \
    echo "Checking for favicon..." && \
    ls -la /app/static/favicon.png || echo "WARNING: favicon.png not found"
    echo "Checking for goldback logo..." && \
    ls -la /app/static/gb_logo.png || echo "WARNING: favicon.png not found"

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
