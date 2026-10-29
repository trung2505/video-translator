# 🏗️ Architecture & Design - Kiến Trúc & Thiết Kế

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Browser                              │
│                    (http://localhost:3000)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Next.js Frontend│
                    │  (React + TS)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────────────────┐
                    │   FastAPI Backend           │
                    │  (http://localhost:8000)    │
                    ├────────────────────────────┤
                    │ • Video Upload Endpoint    │
                    │ • Translation Job Endpoint │
                    │ • Progress Tracking        │
                    └────────┬────────────────────┘
                             │
                    ┌────────▼───────────┬──────────────┐
                    │                    │              │
          ┌─────────▼─────────┐ ┌──────▼────────┐ ┌────▼──────────┐
          │   PostgreSQL DB   │ │    Redis      │ │  File Storage │
          │  (Metadata)       │ │  (Queue)      │ │  (Uploads)    │
          └───────────────────┘ └──────┬────────┘ └───────────────┘
                                       │
                            ┌──────────▼──────────┐
                            │  Celery Workers    │
                            │ (Async Tasks)      │
                            └────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
        ┌───────────▼───────┐ ┌──────▼──────┐ ┌─────▼────────────┐
        │  FFmpeg           │ │Faster-Whisper│ │ Google Translate│
        │ (Audio/Video)     │ │ (STT)        │ │ API             │
        └───────────────────┘ └──────────────┘ └─────────────────┘
```

## Data Flow

### Video Upload & Processing Flow

```
User Upload Video
        │
        ▼
┌─────────────────┐
│ Frontend        │  1. Validate file
│ VideoUploader   │  2. Upload to Backend
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ Backend /videos/upload      │  1. Save to disk
│ video_service.save_file()   │  2. Create DB record
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ PostgreSQL Database     │
│ Video Table             │
│ status: 'uploaded'      │
└─────────────────────────┘
```

### Translation Pipeline Flow

```
User Start Translation
        │
        ▼
┌────────────────────────┐
│ POST /translations     │
│ Create Job Record      │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────────┐
│ Celery Task Queue          │
│ (Redis)                    │
└────────┬───────────────────┘
         │
         ▼ (Celery Worker picks up task)
┌─────────────────────────────────────┐
│ Step 1: Extract Audio (0-20%)       │
│ AudioService.extract_audio()        │
│ FFmpeg: video → wav                 │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Step 2: Transcribe (20-40%)         │
│ SpeechRecognitionService.transcribe()│
│ Faster-Whisper: audio → Chinese text│
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Step 3: Translate (40-60%)          │
│ TranslationService.translate()      │
│ Google API: Chinese → Vietnamese    │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Step 4: Generate Subtitles (60-80%) │
│ SubtitleService.generate_srt()      │
│ Text + Timing → SRT file            │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Step 5: Burn Subtitles (80-100%)    │
│ VideoProcessingService.burn()       │
│ FFmpeg: video + srt → output video  │
└────────┬────────────────────────────┘
         │
         ▼
┌────────────────────┐
│ Job Complete       │
│ Ready for Download │
└────────────────────┘
```

## Database Schema

### Videos Table
```sql
CREATE TABLE videos (
  id VARCHAR PRIMARY KEY,
  original_filename VARCHAR,
  file_path VARCHAR UNIQUE,
  upload_date DATETIME DEFAULT NOW(),
  status ENUM('uploaded', 'processing', 'completed', 'failed'),
  duration FLOAT,
  file_size INTEGER,
  error_message TEXT
);
```

### TranslationJobs Table
```sql
CREATE TABLE translation_jobs (
  id VARCHAR PRIMARY KEY,
  video_id VARCHAR,
  status ENUM('pending', 'processing', 'completed', 'failed'),
  progress INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT NOW(),
  completed_at DATETIME,
  transcription TEXT,
  translation TEXT,
  subtitles_path VARCHAR,
  output_video_path VARCHAR,
  error_message TEXT
);
```

## API Response Examples

### Upload Video Response
```json
{
  "id": "abc123xyz",
  "original_filename": "video.mp4",
  "upload_date": "2024-01-15T10:30:00",
  "status": "uploaded",
  "progress": 0,
  "duration": null,
  "file_size": 536870912,
  "error_message": null
}
```

### Start Translation Response
```json
{
  "id": "job123abc",
  "video_id": "abc123xyz",
  "status": "pending",
  "message": "Translation started"
}
```

### Translation Job Status Response
```json
{
  "id": "job123abc",
  "video_id": "abc123xyz",
  "status": "processing",
  "progress": 45,
  "created_at": "2024-01-15T10:35:00",
  "completed_at": null,
  "error_message": null
}
```

## Technology Details

### Frontend Technologies
- **Next.js 15**: App router, SSR capabilities
- **TypeScript**: Type safety
- **TailwindCSS**: Responsive design
- **Zustand**: Lightweight state management
- **Axios**: HTTP client with interceptors
- **React Dropzone**: File upload with preview

### Backend Technologies
- **FastAPI**: Async web framework
- **SQLAlchemy**: ORM for database
- **Pydantic**: Data validation
- **Celery**: Task queue
- **Redis**: Message broker
- **Faster-Whisper**: Optimized Whisper model
- **Google Cloud Translate**: Translation API
- **FFmpeg**: Multimedia framework

### Database & Storage
- **PostgreSQL**: Relational database
- **Redis**: In-memory cache & message broker
- **File System**: Video & processed files storage

### Deployment
- **Docker**: Container images
- **Docker Compose**: Orchestration
- **Volume Mounts**: Persistent storage

## Performance Considerations

### Optimization Strategies

1. **Audio Processing**
   - Chunk audio into 30-second segments
   - Process chunks in parallel with multiple workers
   - Use 16kHz mono for Whisper (optimal)

2. **Subtitle Generation**
   - Generate SRT format (compatible with all players)
   - Minimal text processing
   - Cache translations

3. **Video Processing**
   - FFmpeg hardware acceleration (if available)
   - Adaptive bitrate encoding
   - Parallel subtitle burning

4. **Frontend**
   - React component optimization
   - Zustand state management (minimal re-renders)
   - Real-time progress updates via polling

## Scalability

### Current Limitations
- Single database instance
- Single Redis instance
- Limited worker processes

### Scaling Strategy
1. Add more Celery workers for parallel processing
2. Use database connection pooling
3. Implement Redis clustering
4. Use S3/object storage for file management
5. Add load balancer for frontend/backend

## Error Handling

### Frontend Error Handling
```typescript
try {
  const response = await uploadVideo(file)
} catch (error) {
  console.error('Upload failed:', error)
  // Show user-friendly error message
}
```

### Backend Error Handling
```python
try:
    # Process video
except Exception as e:
    job.status = TranslationStatus.failed
    job.error_message = str(e)
    db.commit()
    raise
```

## Security Considerations

1. **File Upload**
   - Validate file type and size
   - Scan for malware (optional)
   - Store outside web root

2. **API Security**
   - CORS configuration
   - Input validation with Pydantic
   - Rate limiting (can be added)

3. **Database**
   - Connection pooling
   - Parameterized queries (SQLAlchemy)
   - Encrypted passwords

4. **Deployment**
   - Environment variables for secrets
   - HTTPS in production
   - Regular updates

---

**Last Updated**: 2024
**Version**: 1.0.0
