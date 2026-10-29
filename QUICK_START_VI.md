# 🎬 Video Translator - Hướng Dẫn Bắt Đầu Nhanh

## 📋 Yêu Cầu Tiên Quyết

- Docker Desktop cài đặt và chạy
- Internet để tải hình ảnh Docker và mô hình AI

## 🚀 Khởi Động Nhanh

### Windows
```bash
# Chạy tập tin batch
start.bat
```

### macOS / Linux
```bash
# Chạy tập tin shell
chmod +x start.sh
./start.sh
```

## 📍 Truy Cập Ứng Dụng

Sau khi tất cả dịch vụ khởi động:

1. **Frontend**: Mở trình duyệt và truy cập http://localhost:3000
2. **API Docs**: http://localhost:8000/docs (Swagger UI)
3. **Database**: localhost:5432
4. **Redis**: localhost:6379

## 💡 Cách Sử Dụng

### 1. Tải lên Video
- Kéo thả video tiếng Trung vào vùng tải lên
- Hoặc nhấp để chọn tập tin từ máy tính
- Hỗ trợ: MP4, AVI, MOV, MKV, FLV, WMV

### 2. Chọn Video để Dịch
- Chọn video từ danh sách trong bảng điều khiển bên phải
- Video phải ở trạng thái "Đã tải lên"

### 3. Bắt Đầu Dịch
- Nhấp nút "Bắt đầu dịch"
- Theo dõi tiến độ xử lý trong cửa sổ "Tiến độ xử lý"

### 4. Tải Video Dịch
- Khi hoàn thành, nhấp "Tải video đã dịch"
- Một file MP4 với phụ đề tiếng Việt sẽ được tải xuống

## 🔧 Cấu Hình

### Tập tin .env
Cấu hình các thiết lập trong `.env`:

```env
# Cơ sở dữ liệu
DATABASE_URL=postgresql://user:password@postgres:5432/video_translator

# Google Translate API
GOOGLE_TRANSLATE_API_KEY=your-api-key-here

# Mô hình Whisper (tiny, base, small, medium, large)
WHISPER_MODEL=base

# Thiết bị Whisper (cuda hoặc cpu)
WHISPER_DEVICE=cpu
```

### Thay Đổi Cấu Hình

Chỉnh sửa `.env` và khởi động lại:
```bash
docker-compose -f docker/docker-compose.yml restart
```

## 📊 Quá Trình Xử Lý

```
1. Tải lên Video (0-5%)
2. Trích xuất âm thanh (5-20%)
3. Nhận dạng giọng nói (20-40%)
4. Dịch văn bản (40-60%)
5. Tạo phụ đề (60-80%)
6. Đốt phụ đề vào video (80-100%)
```

## ⏹️ Dừng Ứng Dụng

### Windows
```bash
cd docker
docker-compose down
```

### macOS / Linux
```bash
docker-compose -f docker/docker-compose.yml down
```

## 🐛 Khắc Phục Sự Cố

### Dịch vụ không khởi động
```bash
# Kiểm tra logs
docker-compose -f docker/docker-compose.yml logs

# Xóa tất cả container và khởi động lại
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d
```

### Lỗi kết nối cơ sở dữ liệu
```bash
# Kiểm tra xem PostgreSQL đã khởi động chưa
docker-compose -f docker/docker-compose.yml ps

# Khởi động lại PostgreSQL
docker-compose -f docker/docker-compose.yml restart postgres
```

### Frontend không tải
- Kiểm tra http://localhost:3000
- Xóa cache trình duyệt (Ctrl+Shift+Delete)
- Kiểm tra logs: `docker-compose -f docker/docker-compose.yml logs frontend`

## 📈 Tối Ưu Hiệu Suất

### Để tăng tốc độ xử lý:

1. **Sử dụng GPU cho Whisper**
   - Thay đổi `WHISPER_DEVICE=cuda` trong `.env`
   - Cần cài đặt CUDA on your system

2. **Sử dụng mô hình Whisper nhỏ hơn**
   - Thay đổi `WHISPER_MODEL=tiny` trong `.env`
   - Nhanh hơn nhưng độ chính xác thấp hơn

3. **Tăng số worker Celery**
   - Chỉnh sửa `docker-compose.yml`
   - Thêm nhiều dịch vụ worker

## 📞 Hỗ Trợ

Nếu gặp vấn đề:
1. Kiểm tra Docker logs
2. Đảm bảo tất cả dịch vụ đều running
3. Xóa cache và khởi động lại
4. Tạo issue trên GitHub

---

**Happy translating! 🎬🌍**
