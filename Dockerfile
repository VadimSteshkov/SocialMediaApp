# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5001

# No system dependencies needed
# All packages in requirements.txt have pre-built wheels (no compilation needed)

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api.py .
COPY database.py .
COPY static/ ./static/

# Create directories for database and uploads
RUN mkdir -p /app/data && \
    mkdir -p /app/uploads/full && \
    mkdir -p /app/uploads/thumbnails

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/api/health')" || exit 1

# Run the application
CMD ["python", "api.py"]

