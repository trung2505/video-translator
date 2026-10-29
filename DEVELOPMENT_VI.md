# 🛠️ Developer Guide - Hướng Dẫn Cho Nhà Phát Triển

## Environment Setup (Thiết Lập Môi Trường)

### Local Development (Phát Triển Cục Bộ)

#### 1. Backend Setup (Thiết Lập Backend)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env

# Start PostgreSQL & Redis
# Make sure PostgreSQL and Redis are running on your system

# Run migrations (if using Alembic)
alembic upgrade head

# Start backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.workers.tasks worker --loglevel=info
```

#### 2. Frontend Setup (Thiết Lập Frontend)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# Start development server
npm run dev

# In browser, open http://localhost:3000
```

### Running Services with Docker (Chạy Dịch Vụ bằng Docker)

```bash
# From project root
cd docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Code Structure (Cấu Trúc Mã)

### Frontend Structure

```
frontend/src/
├── app/
│   ├── layout.tsx          # Root layout, styling setup
│   ├── page.tsx            # Home page - main component
│   ├── globals.css         # Global Tailwind CSS styles
│   └── fonts.ts            # Font configuration
├── components/             # Reusable React components
│   ├── VideoUploader.tsx   # Upload component with validation
│   ├── VideoList.tsx       # Video list with status display
│   ├── ProgressTracker.tsx # Step-by-step progress tracker
│   └── TranslationPanel.tsx # Translation control panel
├── lib/                    # Utility functions
│   ├── api.ts             # Axios HTTP client
│   └── store.ts           # Zustand global state
└── types/                 # TypeScript type definitions
    └── index.ts           # Video, Job, and other types
```

### Backend Structure

```
backend/app/
├── main.py                 # FastAPI app initialization
├── config.py              # Settings & configuration
├── api/                   # API route handlers
│   ├── videos.py          # Video upload/list routes
│   ├── translations.py    # Translation job routes
│   ├── health.py          # Health check endpoint
│   └── schemas.py         # Pydantic models
├── services/              # Business logic
│   ├── video_service.py              # Video CRUD ops
│   ├── audio_service.py              # Audio extraction
│   ├── speech_recognition_service.py # Whisper transcription
│   ├── translation_service.py        # Google Translate
│   ├── subtitle_service.py           # SRT generation
│   └── video_processing_service.py   # FFmpeg operations
├── models/                # SQLAlchemy ORM models
│   └── __init__.py        # Video & TranslationJob models
├── database/              # Database configuration
│   └── __init__.py        # SQLAlchemy engine & session
├── workers/               # Celery async tasks
│   └── tasks.py           # Video processing pipeline
└── utils/                 # Helper functions
    └── __init__.py
```

## Common Development Tasks (Các Tác Vụ Phát Triển Thường Gặp)

### Adding a New API Endpoint (Thêm Endpoint API Mới)

1. **Create schema in `app/api/schemas.py`**
```python
class NewFeatureRequest(BaseModel):
    param1: str
    param2: int
```

2. **Create route in `app/api/new_feature.py`**
```python
from fastapi import APIRouter

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.post("")
def create_feature(request: NewFeatureRequest):
    return {"message": "Feature created"}
```

3. **Include router in `app/main.py`**
```python
from app.api import new_feature
app.include_router(new_feature.router, prefix=settings.API_V1_STR)
```

### Adding a New React Component (Thêm Thành Phần React Mới)

1. **Create component file `frontend/src/components/NewComponent.tsx`**
```typescript
'use client'

export const NewComponent: React.FC = () => {
  return <div>New Component</div>
}
```

2. **Import in `frontend/src/app/page.tsx`**
```typescript
import { NewComponent } from '@/components/NewComponent'

export default function Home() {
  return <NewComponent />
}
```

### Running Tests (Chạy Kiểm Tra)

#### Backend Tests
```bash
cd backend
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_video_service.py
```

#### Frontend Tests
```bash
cd frontend
npm run test

# With coverage
npm run test:coverage
```

### Code Quality & Formatting (Chất Lượng & Định Dạng Mã)

#### Backend
```bash
# Format code with Black
black app/

# Check linting with Flake8
flake8 app/

# Type checking with mypy
mypy app/
```

#### Frontend
```bash
# Format code with Prettier
npm run format

# Check linting with ESLint
npm run lint

# Type checking
npm run type-check
```

## Database Management (Quản Lý Cơ Sở Dữ Liệu)

### Create Migration (Tạo Migration)
```bash
cd backend
alembic revision --autogenerate -m "Add new field"
alembic upgrade head
```

### Database Queries (Truy Vấn Cơ Sở Dữ Liệu)
```bash
# Connect to PostgreSQL
psql -U user -d video_translator

# List videos
SELECT * FROM videos;

# List jobs
SELECT * FROM translation_jobs;

# Check job status
SELECT id, status, progress FROM translation_jobs WHERE status='processing';
```

## Debugging (Gỡ Lỗi)

### Backend Debugging
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use Python debugger
import logging
logging.debug("Debug message")
```

### Frontend Debugging
```typescript
// Browser console
console.log("Debug message")

// React DevTools
// Install from Chrome Web Store

// NextJS debugging
// http://localhost:3000 → Open DevTools
```

### Docker Debugging
```bash
# View service logs
docker-compose logs service-name -f

# Execute command in container
docker-compose exec backend bash

# View container processes
docker top video-translator-backend
```

## Performance Optimization (Tối Ưu Hiệu Suất)

### Backend Optimization
1. Add database indexing
2. Cache frequently accessed data
3. Use async operations
4. Implement request rate limiting

### Frontend Optimization
1. Code splitting
2. Image optimization
3. Lazy loading components
4. Minify and compress assets

## Environment Variables (Biến Môi Trường)

Create `.env` and `.env.local` files:

```bash
# .env (shared)
NEXT_PUBLIC_API_URL=http://localhost:8000

# .env.local (local overrides, not committed)
GOOGLE_TRANSLATE_API_KEY=xxx
```

## Version Control (Kiểm Soát Phiên Bản)

### Commit Messages
```
feat: Add new feature
fix: Fix bug
docs: Update documentation
test: Add tests
refactor: Refactor code
```

### Branch Naming
```
feature/feature-name
bugfix/bug-name
hotfix/issue-name
```

## Deployment Preparation (Chuẩn Bị Triển Khai)

### Before Deploying to Production (Trước Khi Triển Khai Sản Xuất)

1. **Run all tests**
```bash
npm run test          # Frontend
pytest                # Backend
```

2. **Build for production**
```bash
npm run build          # Frontend
python -m pytest       # Backend
```

3. **Check environment variables**
```bash
# Ensure all required vars are set
cat .env | grep -v '^#'
```

4. **Database backups**
```bash
docker exec db pg_dump > backup.sql
```

5. **Update documentation**
```bash
# Update README, API docs, etc.
```

## Resources & Documentation (Tài Nguyên & Tài Liệu)

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [Celery Documentation](https://docs.celeryproject.io)
- [Docker Documentation](https://docs.docker.com)

## Useful Commands (Các Lệnh Hữu Ích)

```bash
# Frontend
npm start              # Start development
npm run build          # Build for production
npm run lint           # Check linting
npm run type-check     # TypeScript check

# Backend
uvicorn app.main:app --reload
celery -A app.workers.tasks worker
pytest                 # Run tests
black app/             # Format code

# Docker
docker-compose up -d
docker-compose down
docker-compose logs -f
docker-compose exec service bash
```

---

**Happy coding! 💻🚀**
