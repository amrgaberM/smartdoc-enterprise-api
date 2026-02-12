# Use a lightweight but stable Python image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and ensure logs are flush immediately
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# 1. Install system-level dependencies for Postgres and Python C-extensions
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy ONLY requirements first to leverage Docker cache
COPY requirements.txt /app/

# 3. Install heavy AI libraries
# --no-cache-dir keeps the image small and prevents memory hangs during install
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your application code
# Since the heavy install is done above, this step is instant
COPY . /app/

# 5. Start the server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]