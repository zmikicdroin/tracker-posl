FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for uploads and database
RUN mkdir -p /app/uploads /app/data

# Set environment variables
ENV FLASK_ENV=production
ENV DATABASE_PATH=/app/data/jobtracker.db
ENV UPLOAD_FOLDER=/app/uploads

# Expose port
EXPOSE 5000

# Run the application
# CMD ["python", "app.py"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
