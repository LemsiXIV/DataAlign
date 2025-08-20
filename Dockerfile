# Use Python 3.13 image
FROM dockerproxy.repos.tech.orange/python:3.13.0-slim

# Set working directory
WORKDIR /app

# Install system dependencies (MySQL client + Node.js for Tailwind/Flowbite build)
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev build-essential pkg-config curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash dataalign

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package.json and install Node deps for Tailwind + Flowbite
COPY package*.json ./
RUN npm install --production=false

# Copy project files and set ownership
COPY . .
RUN chown -R dataalign:dataalign /app

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads/source /app/uploads/archive /app/temp /app/backups \
    && chown -R dataalign:dataalign /app/logs /app/uploads /app/temp /app/backups

# Build Tailwind + Flowbite assets
RUN npx tailwindcss -i ./app/static/src/input.css -o ./app/static/dist/output.css --minify

# Switch to non-root user
USER dataalign

# Create DISABLE_AUTO_MIGRATIONS flag for Docker
RUN touch /app/DISABLE_AUTO_MIGRATIONS

# Expose Flask default port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Start Flask app with production settings
CMD ["python", "start_production.py"]
