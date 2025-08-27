# Use Python 3.13 image
FROM dockerproxy.repos.tech.orange/python:3.13.0-slim

# Set working directory
WORKDIR /app

# Copy requirements FIRST (for Docker layer caching)
COPY requirements.txt package*.json ./
Run pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt 

#Copy the whole project
COPY . .

# Expose port (Flask default)
EXPOSE 5000

# Run the application
CMD ["gunicorn", "-w", "2", "-b","0.0.0.0:5000","run:app"]