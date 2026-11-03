@echo off
title Khoi dong he thong Com Trua (Docker)
echo =======================================================
echo   DANG KHOI DONG HE THONG COM TRUA QUA DOCKER...
echo =======================================================

:: Chay he thong qua Docker Compose
docker-compose up --build -d

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Khong the khoi dong Docker!
    echo Vui long kiem tra xem Docker Desktop da duoc bat hay chua.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =======================================================
echo   HE THONG DA SAN SANG!
echo   - Backend Swagger API: http://localhost:8000/docs
echo   - Quan ly CSDL (pgAdmin): http://localhost:5050
echo =======================================================
echo.
echo Dang tu dong mo trinh duyet...
timeout /t 3 >nul
start http://localhost:8000/docs
