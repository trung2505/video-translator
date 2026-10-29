#!/bin/bash
# Tree structure for documentation

cat << 'EOF'
video-translator/
│
├── 📁 frontend/                      # Next.js Frontend Application
│   ├── 📁 src/
│   │   ├── 📁 app/
│   │   │   ├── 📄 layout.tsx         # Root layout component
│   │   │   ├── 📄 page.tsx           # Home page
│   │   │   ├── 📄 globals.css        # Global styles
│   │   │   └── 📄 fonts.ts           # Font configuration
│   │   ├── 📁 components/
│   │   │   ├── 📄 VideoUploader.tsx  # File upload component
│   │   │   ├── 📄 VideoList.tsx      # Video list component
│   │   │   ├── 📄 ProgressTracker.tsx # Progress tracking
│   │   │   └── 📄 TranslationPanel.tsx # Translation controls
│   │   ├── 📁 lib/
│   │   │   ├── 📄 api.ts             # API client (Axios)
│   │   │   └── 📄 store.ts           # Zustand store
│   │   └── 📁 types/
│   │       └── 📄 index.ts           # TypeScript types
│   ├── 📁 public/                    # Static assets
│   ├── 📄 package.json               # Node dependencies
│   ├── 📄 next.config.js             # Next.js config
│   ├── 📄 tsconfig.json              # TypeScript config
│   ├── 📄 tailwind.config.ts         # Tailwind config
│   ├── 📄 postcss.config.js          # PostCSS config
│   └── 📄 .eslintrc.json             # ESLint config
│
├── 📁 backend/                       # FastAPI Backend Application
│   ├── 📁 app/
│   │   ├── 📄 main.py                # FastAPI entry point
│   │   ├── 📄 config.py              # Configuration & settings
│   │   ├── 📁 api/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 videos.py          # Video endpoints
│   │   │   ├── 📄 translations.py    # Translation endpoints
│   │   │   ├── 📄 health.py          # Health check
│   │   │   └── 📄 schemas.py         # Pydantic models
│   │   ├── 📁 services/
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 video_service.py              # Video management
│   │   │   ├── 📄 audio_service.py             # Audio extraction
│   │   │   ├── 📄 speech_recognition_service.py # Whisper transcription
│   │   │   ├── 📄 translation_service.py        # Google Translate
│   │   │   ├── 📄 subtitle_service.py           # SRT generation
│   │   │   └── 📄 video_processing_service.py   # FFmpeg operations
│   │   ├── 📁 models/
│   │   │   ├── 📄 __init__.py        # SQLAlchemy models
│   │   ├── 📁 database/
│   │   │   ├── 📄 __init__.py        # DB setup
│   │   ├── 📁 workers/
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 tasks.py           # Celery tasks
│   │   ├── 📁 utils/
│   │   │   └── 📄 __init__.py
│   │   └── 📄 __init__.py
│   └── 📄 requirements.txt            # Python packages
│
├── 📁 docker/                        # Docker Configuration
│   ├── 📄 Dockerfile.backend         # Backend container
│   ├── 📄 Dockerfile.frontend        # Frontend container
│   ├── 📄 Dockerfile.worker          # Worker container
│   └── 📄 docker-compose.yml         # Orchestration
│
├── 📁 tests/                         # Test files (optional)
│   ├── 📁 unit/
│   ├── 📁 integration/
│   └── 📁 e2e/
│
├── 📄 .env.example                   # Environment template
├── 📄 .gitignore                     # Git ignore rules
├── 📄 package.json                   # Root package config
├── 📄 start.sh                       # Start script (Linux/Mac)
├── 📄 start.bat                      # Start script (Windows)
│
├── 📄 README.md                      # Main documentation
├── 📄 QUICK_START_VI.md              # Quick start guide (Vietnamese)
├── 📄 ARCHITECTURE.md                # System architecture
├── 📄 DEVELOPMENT_VI.md              # Development guide (Vietnamese)
├── 📄 DEPLOYMENT_VI.md               # Production deployment (Vietnamese)
└── 📄 FILE_STRUCTURE.md              # This file

EOF
