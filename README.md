# 🎬 Video Translator - Chinese to Vietnamese

A full-stack web application for translating Chinese videos to Vietnamese with AI. This project uses state-of-the-art technologies including Faster-Whisper for speech recognition, Google Translate API for translation, and FFmpeg for video processing.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Module Explanation](#module-explanation)
- [Vietnamese Documentation](#vietnamese-documentation)

---

## ✨ Features

1. **Video Upload** - Upload Chinese video files (MP4, AVI, MOV, MKV, FLV, WMV)
2. **Audio Extraction** - Extract audio from video using FFmpeg
3. **Speech Recognition** - Detect and transcribe Chinese speech using Faster-Whisper
4. **Text Translation** - Translate Chinese text to Vietnamese using Google Translate
5. **Subtitle Generation** - Create SRT subtitle files
6. **Subtitle Burning** - Embed subtitles into video using FFmpeg
7. **Video Download** - Download the translated video with burned-in subtitles
8. **Progress Tracking** - Real-time progress updates during processing

---

## 🛠️ Tech Stack

### Frontend
- **Next.js 15** - Modern React framework with server-side rendering
- **TypeScript** - Type-safe JavaScript development
- **TailwindCSS** - Utility-first CSS framework
- **Zustand** - Lightweight state management
- **Axios** - HTTP client for API calls
- **React Dropzone** - File upload component

### Backend
- **FastAPI** - High-performance async Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database
- **Redis** - Message broker and caching
- **Celery** - Distributed task queue
- **Faster-Whisper** - Fast speech-to-text model
- **Google Cloud Translate** - Translation API
- **FFmpeg** - Video and audio processing
- **LibRosa** - Audio analysis library

### DevOps
- **Docker** - Container orchestration
- **Docker Compose** - Multi-container deployment

---

## 📁 Project Structure

```
video-translator/
├── frontend/                    # Next.js frontend application
│   ├── src/
│   │   ├── app/               # Next.js app directory
│   │   │   ├── layout.tsx      # Root layout component
│   │   │   ├── page.tsx        # Home page
│   │   │   └── globals.css     # Global styles
│   │   ├── components/         # React components
│   │   │   ├── VideoUploader.tsx       # File upload component
│   │   │   ├── VideoList.tsx           # Video list component
│   │   │   ├── ProgressTracker.tsx     # Progress tracking component
│   │   │   └── TranslationPanel.tsx    # Translation control panel
│   │   ├── lib/               # Utility functions and hooks
│   │   │   ├── api.ts         # API client
│   │   │   └── store.ts       # Zustand store
│   │   └── types/             # TypeScript type definitions
│   │       └── index.ts       # Type definitions
│   ├── public/                # Static assets
│   ├── package.json           # Node.js dependencies
│   ├── next.config.js         # Next.js configuration
│   ├── tsconfig.json          # TypeScript configuration
│   └── tailwind.config.ts     # TailwindCSS configuration
│
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── config.py          # Configuration settings
│   │   ├── api/               # API route handlers
│   │   │   ├── videos.py      # Video upload/list endpoints
│   │   │   ├── translations.py # Translation job endpoints
│   │   │   ├── health.py      # Health check endpoint
│   │   │   └── schemas.py     # Pydantic request/response models
│   │   ├── services/          # Business logic layer
│   │   │   ├── video_service.py              # Video file management
│   │   │   ├── audio_service.py             # Audio extraction
│   │   │   ├── speech_recognition_service.py # Whisper transcription
│   │   │   ├── translation_service.py        # Google Translate integration
│   │   │   ├── subtitle_service.py           # SRT subtitle generation
│   │   │   └── video_processing_service.py   # FFmpeg subtitle burning
│   │   ├── models/            # SQLAlchemy database models
│   │   │   └── __init__.py    # Video and TranslationJob models
│   │   ├── database/          # Database configuration
│   │   │   └── __init__.py    # SQLAlchemy setup
│   │   ├── workers/           # Celery async tasks
│   │   │   └── tasks.py       # Video processing pipeline
│   │   └── utils/             # Utility functions
│   └── requirements.txt        # Python dependencies
│
├── docker/                     # Docker configuration
│   ├── Dockerfile.backend      # Backend container image
│   ├── Dockerfile.frontend     # Frontend container image
│   ├── Dockerfile.worker       # Celery worker container image
│   └── docker-compose.yml      # Docker Compose configuration
│
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── package.json               # Root package.json (optional)
└── README.md                  # This file

```

---

## 🚀 Installation

### Prerequisites
- Docker and Docker Compose
- Git
- Node.js 18+ (for local development without Docker)
- Python 3.11+ (for local development without Docker)
- FFmpeg installed on system

### Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd video-translator
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Update .env with your settings**
```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/video_translator
DATABASE_USER=user
DATABASE_PASSWORD=password
DATABASE_NAME=video_translator

# Google Translate API
GOOGLE_TRANSLATE_API_KEY=your-api-key-here

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Start all services**
```bash
docker-compose -f docker/docker-compose.yml up -d
```

5. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

# Start Redis
redis-server

# Start PostgreSQL
# Make sure PostgreSQL is running and database is created

# Run migrations (if using Alembic)
alembic upgrade head

# Start Celery worker in one terminal
celery -A app.workers.tasks worker --loglevel=info

# Start FastAPI server in another terminal
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📖 Usage

1. **Open the application**: Navigate to http://localhost:3000
2. **Upload a video**: Drag and drop or click to select a Chinese video file
3. **Wait for upload**: Monitor the upload progress
4. **Start translation**: Click "Bắt đầu dịch" to begin processing
5. **Monitor progress**: Watch the real-time progress tracker
6. **Download result**: Click "Tải video đã dịch" when complete

---

## 🔌 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### Videos
- `POST /videos/upload` - Upload a video file
- `GET /videos` - List all videos
- `GET /videos/{video_id}` - Get specific video
- `DELETE /videos/{video_id}` - Delete a video

#### Translations
- `POST /translations` - Start translation job
- `GET /translations/{job_id}` - Get job status
- `GET /translations/{job_id}/download` - Download translated video
- `GET /translations/{job_id}/subtitles` - Download subtitles

#### Health
- `GET /health` - Health check

### Example Requests

**Upload Video**
```bash
curl -X POST http://localhost:8000/api/v1/videos/upload \
  -F "file=@video.mp4"
```

**Start Translation**
```bash
curl -X POST http://localhost:8000/api/v1/translations \
  -H "Content-Type: application/json" \
  -d '{"video_id": "abc123"}'
```

**Get Job Status**
```bash
curl http://localhost:8000/api/v1/translations/job123
```

---

## 📚 Module Explanation

### Frontend Modules

#### `VideoUploader.tsx`
Handles video file uploads with drag-and-drop support. Shows upload progress bar and validates file types.

#### `VideoList.tsx`
Displays all uploaded videos with their status, upload date, and file size. Updates in real-time.

#### `ProgressTracker.tsx`
Shows step-by-step progress of the translation pipeline with a visual progress bar.

#### `TranslationPanel.tsx`
Control panel to select a video and start the translation process. Shows completion status and download button.

#### `api.ts`
Axios HTTP client for communicating with the backend API. Handles file uploads and API calls.

#### `store.ts`
Zustand store for managing global application state (videos list, current job).

### Backend Modules

#### `video_service.py`
Manages video file storage and database records. Handles file uploads and CRUD operations.

#### `audio_service.py`
Extracts audio from videos using FFmpeg and splits audio into processable chunks.

#### `speech_recognition_service.py`
Uses Faster-Whisper to detect language and transcribe audio to Chinese text.

#### `translation_service.py`
Translates Chinese text to Vietnamese using Google Cloud Translate API.

#### `subtitle_service.py`
Generates SRT subtitle files from translation segments with proper timing.

#### `video_processing_service.py`
Burns subtitles into video and handles video metadata retrieval using FFmpeg.

#### `tasks.py` (Celery Workers)
Orchestrates the entire translation pipeline with progress updates:
1. Audio extraction (5-20%)
2. Speech recognition (25-40%)
3. Text translation (45-60%)
4. Subtitle generation (65-80%)
5. Subtitle burning (85-100%)

#### `schemas.py`
Pydantic models for request/response validation and API documentation.

#### `main.py`
FastAPI application setup with CORS, middleware, and route configuration.

---

## 🐳 Docker Deployment

### Services

**postgres**: PostgreSQL database for storing video and job metadata
**redis**: Redis for message broker and caching
**backend**: FastAPI application server
**worker**: Celery worker for async video processing
**frontend**: Next.js frontend application

### Environment Variables

See `.env.example` for all available configuration options.

---

## 🌐 VIETNAMESE DOCUMENTATION

# 🎬 Video Translator - Dịch Video Tiếng Trung sang Tiếng Việt

Một ứng dụng web full-stack cho phép dịch video tiếng Trung sang tiếng Việt sử dụng AI. Dự án sử dụng các công nghệ hiện đại nhất bao gồm Faster-Whisper để nhận dạng giọng nói, Google Translate API để dịch, và FFmpeg để xử lý video.

## ✨ Các Tính Năng

1. **Tải lên video** - Tải lên các tập tin video tiếng Trung (MP4, AVI, MOV, MKV, FLV, WMV)
2. **Trích xuất âm thanh** - Trích xuất âm thanh từ video bằng FFmpeg
3. **Nhận dạng giọng nói** - Phát hiện và chuyển giọng nói tiếng Trung thành văn bản bằng Faster-Whisper
4. **Dịch văn bản** - Dịch văn bản tiếng Trung sang tiếng Việt bằng Google Translate
5. **Tạo phụ đề** - Tạo tập tin phụ đề SRT
6. **Đốt phụ đề vào video** - Nhúng phụ đề vào video bằng FFmpeg
7. **Tải video dịch** - Tải video đã dịch với phụ đề được đốt vào
8. **Theo dõi tiến độ** - Cập nhật tiến độ thực tế trong quá trình xử lý

## 📚 Giải Thích Các Module

### Frontend

#### `VideoUploader.tsx`
Xử lý tải lên tập tin video với hỗ trợ kéo và thả. Hiển thị thanh tiến độ tải lên và kiểm tra loại tập tin.

#### `VideoList.tsx`
Hiển thị tất cả video đã tải lên với trạng thái, ngày tải lên và kích thước tập tin. Cập nhật theo thời gian thực.

#### `ProgressTracker.tsx`
Hiển thị tiến độ từng bước của quy trình dịch với thanh tiến độ trực quan.

#### `TranslationPanel.tsx`
Bảng điều khiển để chọn video và bắt đầu quá trình dịch. Hiển thị trạng thái hoàn thành và nút tải.

#### `api.ts`
Máy khách HTTP Axios để giao tiếp với API backend. Xử lý tải lên tập tin và các lệnh gọi API.

#### `store.ts`
Kho Zustand để quản lý trạng thái ứng dụng toàn cục (danh sách video, công việc hiện tại).

### Backend

#### `video_service.py`
Quản lý lưu trữ tập tin video và các bản ghi cơ sở dữ liệu. Xử lý tải lên và hoạt động CRUD.

#### `audio_service.py`
Trích xuất âm thanh từ video bằng FFmpeg và chia âm thanh thành các phần có thể xử lý được.

#### `speech_recognition_service.py`
Sử dụng Faster-Whisper để phát hiện ngôn ngữ và chuyên ngôn nói thành văn bản tiếng Trung.

#### `translation_service.py`
Dịch văn bản tiếng Trung sang tiếng Việt bằng Google Cloud Translate API.

#### `subtitle_service.py`
Tạo tập tin phụ đề SRT từ các phần dịch với thời gian thích hợp.

#### `video_processing_service.py`
Đốt phụ đề vào video và xử lý siêu dữ liệu video bằng FFmpeg.

#### `tasks.py` (Celery Workers)
Điều phối toàn bộ quy trình dịch với các bản cập nhật tiến độ:
1. Trích xuất âm thanh (5-20%)
2. Nhận dạng giọng nói (25-40%)
3. Dịch văn bản (45-60%)
4. Tạo phụ đề (65-80%)
5. Đốt phụ đề (85-100%)

#### `schemas.py`
Các mô hình Pydantic để xác thực yêu cầu/phản hồi và tài liệu API.

#### `main.py`
Thiết lập ứng dụng FastAPI với CORS, middleware và cấu hình tuyến đường.

## 🗂️ Cấu Trúc Thư Mục Chi Tiết

```
video-translator/
├── frontend/                              # Ứng dụng frontend Next.js
│   ├── src/
│   │   ├── app/                          # Thư mục app của Next.js
│   │   │   ├── layout.tsx                # Thành phần bố cục gốc
│   │   │   ├── page.tsx                  # Trang chủ
│   │   │   └── globals.css               # Kiểu toàn cục
│   │   ├── components/                   # Các thành phần React
│   │   │   ├── VideoUploader.tsx         # Thành phần tải lên tập tin
│   │   │   ├── VideoList.tsx             # Thành phần danh sách video
│   │   │   ├── ProgressTracker.tsx       # Thành phần theo dõi tiến độ
│   │   │   └── TranslationPanel.tsx      # Bảng điều khiển dịch
│   │   ├── lib/                          # Các hàm tiện ích
│   │   │   ├── api.ts                    # Máy khách API
│   │   │   └── store.ts                  # Kho trạng thái Zustand
│   │   └── types/                        # Định nghĩa kiểu TypeScript
│   │       └── index.ts
│   └── ...
│
├── backend/                               # Ứng dụng backend FastAPI
│   ├── app/
│   │   ├── main.py                       # Điểm vào ứng dụng FastAPI
│   │   ├── config.py                     # Cấu hình
│   │   ├── api/                          # Trình xử lý tuyến đường API
│   │   │   ├── videos.py                 # Điểm cuối tải/liệt kê video
│   │   │   ├── translations.py           # Điểm cuối công việc dịch
│   │   │   ├── health.py                 # Điểm cuối kiểm tra sức khỏe
│   │   │   └── schemas.py                # Mô hình Pydantic
│   │   ├── services/                     # Lớp logic kinh doanh
│   │   │   ├── video_service.py          # Quản lý tập tin video
│   │   │   ├── audio_service.py          # Trích xuất âm thanh
│   │   │   ├── speech_recognition_service.py  # Chuyên đổi giọng nói
│   │   │   ├── translation_service.py    # Tích hợp dịch
│   │   │   ├── subtitle_service.py       # Tạo phụ đề SRT
│   │   │   └── video_processing_service.py   # Đốt phụ đề FFmpeg
│   │   ├── models/                       # Mô hình cơ sở dữ liệu SQLAlchemy
│   │   │   └── __init__.py
│   │   ├── database/                     # Cấu hình cơ sở dữ liệu
│   │   ├── workers/                      # Tác vụ Celery không đồng bộ
│   │   │   └── tasks.py                  # Quy trình xử lý video
│   │   └── utils/                        # Các hàm tiện ích
│   └── requirements.txt                  # Phụ thuộc Python
│
├── docker/                                # Cấu hình Docker
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.worker
│   └── docker-compose.yml
│
└── ...
```

## 🚀 Cách Sử Dụng

1. **Mở ứng dụng**: Chuyển đến http://localhost:3000
2. **Tải lên video**: Kéo thả hoặc nhấp để chọn tập tin video tiếng Trung
3. **Chờ tải xong**: Giám sát tiến độ tải lên
4. **Bắt đầu dịch**: Nhấp "Bắt đầu dịch" để bắt đầu xử lý
5. **Giám sát tiến độ**: Xem theo dõi tiến độ theo thời gian thực
6. **Tải video**: Nhấp "Tải video đã dịch" khi hoàn thành

## 🔧 Biến Môi Trường

Xem `.env.example` để biết tất cả các tùy chọn cấu hình có sẵn.

**Các biến quan trọng:**
- `DATABASE_URL` - Chuỗi kết nối PostgreSQL
- `REDIS_URL` - URL Redis broker
- `WHISPER_MODEL` - Kích thước mô hình Whisper (tiny, base, small, medium, large)
- `GOOGLE_TRANSLATE_API_KEY` - API key cho Google Translate
- `NEXT_PUBLIC_API_URL` - URL API backend cho frontend

## 📊 Quy Trình Xử Lý Video

```
Tải lên Video
    ↓
Trích xuất âm thanh (FFmpeg)
    ↓
Phát hiện ngôn ngữ (Faster-Whisper)
    ↓
Chuyên đổi giọng nói thành văn bản (Faster-Whisper)
    ↓
Dịch văn bản (Google Translate)
    ↓
Tạo phụ đề SRT
    ↓
Đốt phụ đề vào video (FFmpeg)
    ↓
Tải video dịch
```

## 🐳 Triển Khai Docker

**Dịch vụ:**
- **postgres** - Cơ sở dữ liệu PostgreSQL
- **redis** - Redis broker
- **backend** - Máy chủ ứng dụng FastAPI
- **worker** - Celery worker
- **frontend** - Ứng dụng frontend Next.js

**Khởi động:**
```bash
docker-compose -f docker/docker-compose.yml up -d
```

**Dừng:**
```bash
docker-compose -f docker/docker-compose.yml down
```

## 📞 Hỗ Trợ

Để báo cáo lỗi hoặc yêu cầu tính năng, vui lòng tạo một issue trong kho.

---

**Made with ❤️ for video translation**
