@echo off
echo 🚀 Khởi động Video Translator...

:: Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker không được cài đặt. Vui lòng cài đặt Docker.
    pause
    exit /b 1
)

:: Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose không được cài đặt. Vui lòng cài đặt Docker Compose.
    pause
    exit /b 1
)

:: Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Tạo tập tin .env...
    copy .env.example .env
    echo ✅ Tạo .env thành công. Vui lòng cập nhật các giá trị trong .env
)

:: Create necessary directories
if not exist docker\uploads mkdir docker\uploads
if not exist docker\processed mkdir docker\processed

:: Start services
echo 🐳 Khởi động các dịch vụ Docker...
cd docker
docker-compose up -d
cd ..

:: Wait for services
echo ⏳ Chờ các dịch vụ khởi động (30 giây)...
timeout /t 30 /nobreak

echo.
echo ✅ Tất cả dịch vụ đã khởi động!
echo.
echo 📍 Các URL quan trọng:
echo   - Frontend: http://localhost:3000
echo   - API Backend: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Database: localhost:5432
echo   - Redis: localhost:6379
echo.
echo 🎬 Hãy mở http://localhost:3000 để bắt đầu dịch video!
pause
