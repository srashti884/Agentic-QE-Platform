@echo off
echo ===================================================
echo Starting Agentic QE Platform (FastAPI Pure Web App)
echo Zero Node.js / Zero npm Dependency
echo ===================================================
echo.
echo Application URL: http://127.0.0.1:8000/
echo API Documentation: http://127.0.0.1:8000/docs
echo.

cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

