FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY services/auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared directory
COPY shared /app/shared

# Copy service application code
COPY services/auth /app

# Set PYTHONPATH so Python can find the shared module
ENV PYTHONPATH=/app
# Disable Python output buffering for immediate log visibility in containers
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

