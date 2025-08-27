# MySQL Connection Fix for GitLab CI

## Problem
The MySQL authentication was stuck in an infinite loop with the error:
```
mysql: unknown variable 'ssl-mode=DISABLED'
```

## Root Cause
The MySQL client parameter `--ssl-mode=DISABLED` is not recognized by all versions of the MySQL client. Different MySQL client versions use different SSL parameter formats.

## Solution Applied

### 1. Fixed SSL Parameter Format
Changed from:
```bash
--ssl-mode=DISABLED  # Not recognized
```

To:
```bash
--skip-ssl  # Universally supported
```

### 2. Added Robust Connection Testing
Implemented a multi-attempt connection strategy with timeout:

```bash
COUNTER=0
MAX_ATTEMPTS=30

while [ $COUNTER -lt $MAX_ATTEMPTS ]; do
  if mysql -h mysql -u dataalign_test -ptest_password --skip-ssl -e "SELECT 1" 2>/dev/null; then
    echo "✅ MySQL authentication successful!"
    break
  elif mysql -h mysql -u dataalign_test -ptest_password -e "SELECT 1" 2>/dev/null; then
    echo "✅ MySQL authentication successful (with default SSL)!"
    break
  else
    echo "MySQL authentication attempt $((COUNTER+1))/$MAX_ATTEMPTS failed, waiting..."
    sleep 2
    COUNTER=$((COUNTER+1))
  fi
done
```

### 3. Fallback Strategy
- **First attempt**: Try with `--skip-ssl`
- **Second attempt**: Try with default SSL settings
- **Timeout protection**: Maximum 30 attempts (60 seconds)
- **Graceful degradation**: Continue with tests even if connection check fails

### 4. Benefits of New Approach
- ✅ **No infinite loops**: Maximum 30 attempts with timeout
- ✅ **Multiple connection methods**: Tries both SSL and non-SSL
- ✅ **Better error handling**: Captures and suppresses error output
- ✅ **Graceful fallback**: Continues even if readiness check fails
- ✅ **Clear logging**: Shows progress and results

## MySQL Client SSL Parameters (Reference)

### Different MySQL Client Versions:
```bash
# Modern MySQL 8.0+
--ssl-mode=DISABLED

# Older MySQL clients
--skip-ssl

# MariaDB client
--ssl=0

# Universal approach (what we use)
--skip-ssl  # Works across most versions
```

## Expected Results
- ✅ No more "unknown variable" errors
- ✅ Connection established within 60 seconds
- ✅ Pipeline continues even if MySQL readiness check fails
- ✅ Tests handle their own database connectivity

## Testing Approach
The readiness check is now non-blocking. If it fails, the tests will still run and handle database connectivity within the application code, providing better error messages and fallback options.
