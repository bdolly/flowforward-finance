FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY services/accounts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared directory
COPY shared /app/shared

# Copy service application code
COPY services/accounts /app

# Set PYTHONPATH so Python can find the shared module
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

