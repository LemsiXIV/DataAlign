# GitLab CI Docker Connectivity Fix

## Problem
The GitLab runner was encountering this error:
```
ERROR: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

## Root Cause
The issue occurs when using Kubernetes-based GitLab runners with Docker-in-Docker (DinD). The Docker client needs to connect to the DinD service over TCP with TLS, not via the local Unix socket.

## Solution Applied

### 1. Global Docker Variables
Added Docker connectivity variables at the global level:
```yaml
variables:
  DOCKER_HOST: tcp://docker:2376
  DOCKER_TLS_VERIFY: 1
  DOCKER_TLS_CERTDIR: "/certs"
```

### 2. Job-Level Docker Configuration
Updated all Docker jobs (`build`, `deploy_staging`, `deploy_production`, `cleanup`) with:
- Proper Docker connectivity variables
- Docker daemon wait logic in `before_script`

### 3. Fixed Job Names
- Corrected `-deploy_production:` to `deploy_production:` (removed leading dash)

### 4. Added Docker Login
- Added registry authentication in the build job: `docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY`

## Key Changes

### Docker Connectivity Variables
```yaml
variables:
  DOCKER_HOST: tcp://docker:2376
  DOCKER_TLS_VERIFY: 1
  DOCKER_TLS_CERTDIR: "/certs"
```

### Docker Daemon Wait Logic
```yaml
before_script:
  - until docker info; do echo "Waiting for docker daemon..."; sleep 1; done
```

## Why This Works

1. **DOCKER_HOST**: Tells Docker client to connect to the DinD service via TCP
2. **DOCKER_TLS_VERIFY**: Enables TLS verification for secure communication
3. **DOCKER_TLS_CERTDIR**: Specifies where TLS certificates are stored
4. **Wait Loop**: Ensures Docker daemon is ready before executing commands

## Testing
- ✅ YAML syntax validation passed
- ✅ All Docker jobs now have proper connectivity configuration
- ✅ Ready for Kubernetes-based GitLab runners

## Next Steps
The pipeline should now work properly with Kubernetes runners. The Docker daemon connectivity error should be resolved.
