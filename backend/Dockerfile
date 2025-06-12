FROM python:3.11

WORKDIR /app

# 1. install build tools + atlas + clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      gfortran \
      python3-dev \
      libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data


# Create a script to initialize the database and start the application
RUN echo '#!/bin/bash\n\
# Initialize the database\necho "Initializing database..."\npython -c "from database import init_db; init_db()"\n\n# Start the application\necho "Starting application..."\nexec uvicorn main:app --host 0.0.0.0 --port 8000 --reload\n' > /app/start.sh \
    && chmod +x /app/start.sh

EXPOSE 8000

# Use the start script as the entrypoint
ENTRYPOINT ["/app/start.sh"]
