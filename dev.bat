@echo off
echo ========================================
echo   DataAlign Development Environment
echo ========================================
echo.
echo Starting services...
echo.

echo 1. Building CSS...
echo    Input: ./app/static/src/input.css
echo    Output: ./app/static/dist/output.css
echo    Config: tailwind.config.js
npx tailwindcss -i ./app/static/src/input.css -o ./app/static/dist/output.css --minify --config ./tailwind.config.js
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CSS build failed!
    pause
    exit /b 1
)
echo    ✅ CSS built successfully!

echo.
echo 2. Starting Flask application...
echo    Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop all services
echo.

REM Start CSS watcher in background
echo Starting CSS watcher...
start "CSS Watcher" /min cmd /c "npx tailwindcss -i ./app/static/src/input.css -o ./app/static/dist/output.css --watch"

echo Starting Flask application...
REM Start Flask app
.\.venv\Scripts\python.exe run.py
