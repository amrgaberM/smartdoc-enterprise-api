# 1. Use Python 3.11 (Slim version is lighter/faster)
FROM python:3.11-slim

# 2. Set environment variables to optimize Python for Docker
# Prevents Python from writing .pyc files (useless in containers)
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures logs are printed immediately (Critical for debugging!)
ENV PYTHONUNBUFFERED 1

# 3. Set the working directory (The folder inside the container)
WORKDIR /app

# 4. Install system dependencies (Required for Postgres later)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 6. Copy the rest of the code
COPY . /app/

# 7. The command to start the server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]