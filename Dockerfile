# Use Python 3.13 image
FROM dockerproxy.repos.tech.orange/python:3.13.0-slim
 
# Installation de wkhtmltopdf et ses dépendances
RUN apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update \
 && apt-get install -y \
    wget fontconfig libfreetype6 libjpeg62-turbo libpng16-16 libx11-6 libxcb1 libxext6 libxrender1 \
    xfonts-75dpi xfonts-base \
 && wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
 && apt-get install -y ./wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
 && rm wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
 
 
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