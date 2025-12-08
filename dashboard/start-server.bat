@echo off
echo ========================================
echo   ZeroCarb Dashboard Server
echo ========================================
echo.
echo Starting web server on http://localhost:8000
echo.
echo Pages available:
echo   - http://localhost:8000/index.html
echo   - http://localhost:8000/climatiq-validation.html
echo   - http://localhost:8000/energy-profiling.html
echo   - http://localhost:8000/regression-tracking.html
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd public
python -m http.server 8000
