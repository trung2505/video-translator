#!/bin/bash

echo "🚀 Khởi động Video Translator..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker không được cài đặt. Vui lòng cài đặt Docker."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose không được cài đặt. Vui lòng cài đặt Docker Compose."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Tạo tập tin .env..."
    cp .env.example .env
    echo "✅ Tạo .env thành công. Vui lòng cập nhật các giá trị trong .env"
fi

# Create necessary directories
mkdir -p docker/uploads
mkdir -p docker/processed

# Start services
echo "🐳 Khởi động các dịch vụ Docker..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be ready
echo "⏳ Chờ các dịch vụ khởi động..."
sleep 10

# Check if services are running
if docker-compose -f docker/docker-compose.yml ps | grep -q "Up"; then
    echo "✅ Tất cả dịch vụ đã khởi động thành công!"
    echo ""
    echo "📍 Các URL quan trọng:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - API Backend: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Database: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo ""
    echo "🎬 Hãy mở http://localhost:3000 để bắt đầu dịch video!"
else
    echo "❌ Lỗi khi khởi động dịch vụ. Kiểm tra logs bằng: docker-compose -f docker/docker-compose.yml logs"
fi
