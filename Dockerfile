# Production Dockerfile for DataAlign v2.0
FROM python:3.13.0-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash dataalign

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package.json and install Node dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads/source /app/uploads/archive /app/temp /app/backups

# Build CSS assets
RUN npx tailwindcss -i ./app/static/src/input.css -o ./app/static/dist/output.css --minify

# Set ownership to dataalign user
RUN chown -R dataalign:dataalign /app

# Switch to non-root user
USER dataalign

# Expose port
EXPOSE 5004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:5004/health || exit 1

# Start command
CMD ["python", "run.py"]
