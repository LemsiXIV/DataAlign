# DataAlign v2.0 - Docker Deployment Guide

This guide provides instructions for deploying DataAlign using Docker and Docker Compose.

## 🚀 Quick Start

### 🎯 Super Simple (Recommended)

```bash
# 1. Clone the repository
git clone <your-gitlab-repo-url>
cd dataalign

# 2. One command to rule them all!
python start.py

# That's it! ✨ Everything is set up automatically
```

### After Cloning from GitLab

```bash
# 1. Clone the repository
git clone <your-gitlab-repo-url>
cd dataalign

# 2. Start development environment (automatically sets up everything!)
python docker_deploy.py start --env dev

# That's it! The script automatically:
# ✅ Creates necessary directories (uploads, logs, temp, backups)
# ✅ Generates secure .env file with random passwords
# ✅ Sets up the complete Docker environment
# ✅ Starts all services

# Access the application
# - DataAlign: http://localhost:5006
# - Adminer (DB): http://localhost:8080  
# - MailHog: http://localhost:8025
# - Default users: testVikinn/admin123 (admin), testuser/test123 (user)
```

### Production Deployment

```bash
# 1. Clone and start production (fully automated!)
python docker_deploy.py start --env prod

# The script automatically:
# ✅ Generates secure passwords and SECRET_KEY
# ✅ Creates .env file with production settings
# ✅ Sets up directories and permissions
# ✅ Starts production stack with Nginx

# Access the application
# - DataAlign: http://localhost:5004
# - Nginx Proxy: http://localhost:80
# - Check IMPORTANT_PASSWORDS.txt for database credentials
```

## 📋 Available Commands

```bash
# Setup only (creates directories and .env file)
python docker_deploy.py setup

# Start environment (automatically runs setup first)
python docker_deploy.py start --env [dev|prod]

# Stop environment
python docker_deploy.py stop --env [dev|prod]

# View logs
python docker_deploy.py logs --env [dev|prod] [--service app]

# Check status
python docker_deploy.py status --env [dev|prod]

# Restart environment
python docker_deploy.py restart --env [dev|prod]
```

## 🛠️ Manual Docker Commands

### Development

```bash
# Start development stack
docker-compose -f docker-compose.dev.yml up --build -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop
docker-compose -f docker-compose.dev.yml down
```

### Production

```bash
# Start production stack
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🔧 Configuration

### Automatic Setup

The `docker_deploy.py` script automatically handles all configuration:

- **Creates directories**: `uploads/`, `logs/`, `temp/`, `backups/`
- **Generates .env file** with secure random passwords
- **Sets up database credentials** automatically
- **Creates SECRET_KEY** for Flask security

### Manual Configuration (Optional)

If you want custom passwords, you can:

1. Run `python docker_deploy.py setup` first
2. Edit the generated `.env` file
3. Start with `python docker_deploy.py start --env [dev|prod]`

Example `.env` file:
```env
SECRET_KEY=automatically-generated-secure-key
MYSQL_ROOT_PASSWORD=automatically-generated-password
MYSQL_PASSWORD=automatically-generated-password
FLASK_ENV=production
DEBUG=False
AUTO_MIGRATION=false
```

### Port Configuration

**Development:**
- App: 5006 → 5004
- MySQL: 3307 → 3306
- Adminer: 8080 → 8080
- MailHog: 8025 → 8025

**Production:**
- App: 5004 → 5004
- MySQL: 3306 → 3306
- Nginx: 80 → 80, 443 → 443

## 🗄️ Database

### Development
- Host: `localhost:3307`
- Database: `DataAlign_dev`
- User: `DataAlign`
- Password: `DataAlign`

### Production
- Host: `localhost:3306`
- Database: `DataAlign_prod`
- User: `DataAlign`
- Password: From `.env` file

## 📂 Volumes

The following directories are mounted as volumes:

- `./uploads` → `/app/uploads` (File uploads)
- `./logs` → `/app/logs` (Application logs)
- `./temp` → `/app/temp` (Temporary files)
- `./backups` → `/app/backups` (Database backups)

## 🏥 Health Checks

All services include health checks:

- **MySQL**: Connection test
- **App**: HTTP health endpoint (`/health`)
- **Nginx**: HTTP status check

## 🔍 Troubleshooting

### View Service Logs
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f app
docker-compose -f docker-compose.dev.yml logs -f mysql
```

### Database Connection Issues
```bash
# Check MySQL health
docker-compose -f docker-compose.dev.yml exec mysql mysqladmin ping -u root -p

# Connect to MySQL
docker-compose -f docker-compose.dev.yml exec mysql mysql -u DataAlign -p DataAlign_dev
```

### Application Issues
```bash
# Check app logs
docker-compose -f docker-compose.dev.yml logs -f app

# Access app container
docker-compose -f docker-compose.dev.yml exec app bash
```

### Reset Everything
```bash
# Stop and remove all containers and volumes
docker-compose -f docker-compose.dev.yml down -v

# Remove all DataAlign images
docker image prune -f

# Start fresh
python docker_deploy.py start --env dev
```

## 🔐 Security Notes

1. **Change default passwords** in `.env` for production
2. **Use HTTPS** in production (configure SSL certificates in nginx)
3. **Secure database access** (use strong passwords)
4. **Regular updates** of base images and dependencies

## 📊 Monitoring

### Health Endpoints
- App: `http://localhost:5006/health`
- App: `http://localhost:5006/ready`
- Nginx: `http://localhost:80/nginx-health`

### Database Management
- Adminer: `http://localhost:8080` (development only)

### Email Testing
- MailHog: `http://localhost:8025` (development only)

## 🚀 Production Deployment

For production deployment:

1. **Set up your server** (Ubuntu/CentOS recommended)
2. **Install Docker and Docker Compose**
3. **Clone the repository**
4. **Configure environment** (`.env` file)
5. **Set up SSL certificates** (optional)
6. **Start the production stack**
7. **Configure your domain** to point to the server
8. **Set up monitoring and backups**

## 📞 Support

If you encounter issues:

1. Check the logs using the commands above
2. Verify your `.env` configuration
3. Ensure all required ports are available
4. Check the health endpoints
