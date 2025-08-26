# Docker Performance & Troubleshooting Guide

## ⏰ Why Docker Takes So Long?

### First Run (5-15 minutes)
Docker is slow on the first run because it needs to:

1. **Download base images** (Python 3.13, MySQL 8.0, etc.) - ~500MB-1GB
2. **Install system packages** (build tools, MySQL client, Node.js)
3. **Install Python packages** from requirements.txt
4. **Install Node.js packages** for Tailwind CSS
5. **Build the application** and CSS assets

### Subsequent Runs (30 seconds - 2 minutes)
After the first build, Docker reuses cached layers, making it much faster!

## 🚀 Speed Optimization Tips

### 1. Use Quick Start for Subsequent Runs
```bash
# First time (slow)
python docker_deploy.py start --env dev

# Subsequent times (fast)
python docker_deploy.py quick-start --env dev
```

### 2. Enable Docker BuildKit (Windows)
```powershell
# Add to your PowerShell profile or run before Docker commands
$env:DOCKER_BUILDKIT=1
$env:COMPOSE_DOCKER_CLI_BUILD=1
```

### 3. Increase Docker Resources
In Docker Desktop:
- **Memory**: Set to at least 4GB (8GB recommended)
- **CPU**: Use all available cores
- **Disk**: Ensure sufficient space (10GB+)

### 4. Use Docker Layer Caching
The Dockerfile is optimized to cache:
- System packages (rarely change)
- Python requirements (change less often)
- Node packages (change less often)
- Application code (changes most often)

## 🔍 Monitoring Build Progress

### Live Build Output
```bash
# See what's happening during build
python docker_deploy.py start --env dev
# This now shows live output so you can see progress!
```

### Manual Build Monitoring
```bash
# Build with live output
docker-compose -f docker-compose.dev.yml build --progress=plain

# Monitor Docker processes
docker ps

# Check Docker image sizes
docker images
```

## 🐛 Common Issues & Solutions

### 1. Docker Desktop Not Running
```
Error: Cannot connect to the Docker daemon
```
**Solution**: Start Docker Desktop and wait for it to fully load

### 2. Port Already in Use
```
Error: Port 5006 is already allocated
```
**Solution**: 
```bash
python docker_deploy.py stop --env dev
# Or find and kill the process using the port
```

### 3. Out of Disk Space
```
Error: no space left on device
```
**Solution**: Clean up Docker
```bash
# Remove unused containers, networks, images
docker system prune -a

# Remove volumes (careful! this deletes data)
docker volume prune
```

### 4. Build Fails on Node.js/npm
```
Error: npm install failed
```
**Solution**: Clear npm cache
```bash
# Remove node_modules and try again
docker-compose -f docker-compose.dev.yml build --no-cache app
```

### 5. MySQL Connection Issues
```
Error: Can't connect to MySQL server
```
**Solution**: Wait longer for MySQL to start
```bash
# Check MySQL logs
python docker_deploy.py logs --env dev --service mysql

# MySQL takes 30-60 seconds to fully start
```

## 📊 Performance Expectations

### Initial Setup Times
- **Fast Computer (SSD, 16GB RAM)**: 3-5 minutes
- **Average Computer**: 5-10 minutes
- **Slower Computer**: 10-15 minutes

### Quick Start Times
- **All systems**: 30 seconds - 2 minutes

### What's Normal
- ✅ Long first build (downloading & building)
- ✅ Quick subsequent starts
- ✅ MySQL taking 30-60 seconds to be ready
- ✅ Health checks taking 1-2 minutes

### What's Not Normal
- ❌ Build failing repeatedly
- ❌ Taking more than 20 minutes on first build
- ❌ Quick start taking more than 5 minutes
- ❌ Services never becoming healthy

## 🎯 Optimization Commands

### Clean Start (if things are broken)
```bash
# Nuclear option - clean everything and start fresh
python docker_deploy.py stop --env dev
docker-compose -f docker-compose.dev.yml down -v
docker system prune -a
python docker_deploy.py start --env dev
```

### Rebuild Only Application (after code changes)
```bash
# Rebuild just the app container
docker-compose -f docker-compose.dev.yml build app
python docker_deploy.py quick-start --env dev
```

### Pre-download Images
```bash
# Download images without building
docker-compose -f docker-compose.dev.yml pull
```

## 💡 Pro Tips

1. **Leave Docker running** - Stopping/starting Docker Desktop is slow
2. **Use WSL2** on Windows for better performance
3. **Exclude Docker from antivirus** real-time scanning
4. **Use quick-start** for daily development
5. **Only rebuild** when dependencies change
6. **Monitor Docker stats** with `docker stats`

## 🆘 Emergency Commands

```bash
# Kill everything Docker-related
docker kill $(docker ps -q)
docker rm $(docker ps -a -q)
docker rmi $(docker images -q)

# Reset Docker to factory settings
# (Docker Desktop -> Settings -> Reset to factory defaults)
```

Remember: **The first build is always slow, but it gets much faster after that!** ☕
