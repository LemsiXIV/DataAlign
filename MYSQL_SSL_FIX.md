# MySQL SSL/TLS Error Fix for GitLab CI

## Problem
The MySQL connection was failing with:
```
ERROR 2026 (HY000): TLS/SSL error: self-signed certificate in certificate chain
```

## Root Cause
MySQL 8.0 by default requires SSL/TLS connections, but in CI environments, the MySQL service often uses self-signed certificates that aren't trusted by the client.

## Solutions Applied

### 1. Disabled SSL at MySQL Server Level
```yaml
services:
  - name: mysql:8.0
    alias: mysql
    variables:
      MYSQL_ROOT_PASSWORD: test_password
      MYSQL_DATABASE: dataalign_test
      MYSQL_USER: dataalign_test
      MYSQL_PASSWORD: test_password
    command: ["--default-authentication-plugin=mysql_native_password", "--skip-ssl", "--bind-address=0.0.0.0"]
```

### 2. Updated Database URL with SSL Disabled
```yaml
variables:
  DATABASE_URL: "mysql+pymysql://dataalign_test:test_password@mysql/dataalign_test?charset=utf8mb4&ssl_disabled=true"
```

### 3. Added SSL Disabled Flag to MySQL Client Commands
```bash
mysql -h mysql -u dataalign_test -ptest_password --ssl-mode=DISABLED -e "SELECT 1"
```

### 4. Improved Readiness Check
Added a two-stage readiness check:
1. **Port Check**: Uses `netcat` to verify MySQL port 3306 is accessible
2. **Authentication Check**: Tests actual MySQL login with SSL disabled

```bash
- until nc -z mysql 3306; do echo "MySQL port not ready, waiting..."; sleep 2; done
- until mysql -h mysql -u dataalign_test -ptest_password --ssl-mode=DISABLED -e "SELECT 1"; do echo "MySQL authentication not ready, waiting..."; sleep 2; done
```

### 5. Added netcat for Port Checking
```bash
apt-get install -y ... netcat-openbsd
```

## Key MySQL Parameters Added
- `--skip-ssl`: Disables SSL at server level
- `--default-authentication-plugin=mysql_native_password`: Uses traditional authentication
- `--bind-address=0.0.0.0`: Ensures MySQL binds to all interfaces
- `--ssl-mode=DISABLED`: Client-side SSL disable flag
- `ssl_disabled=true`: PyMySQL connection parameter

## Expected Results
- ✅ No more SSL certificate errors
- ✅ Faster MySQL connection establishment
- ✅ Reliable readiness checking
- ✅ Proper database connectivity for tests

## Security Note
These SSL disable settings are appropriate for CI/test environments only. 
Production deployments should use proper SSL certificates.
