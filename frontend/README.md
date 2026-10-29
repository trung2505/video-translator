# Video Translator Frontend

Minimal Next.js + TypeScript frontend for the video translator backend.

Features:
- Drag & drop upload
- Upload progress bar
- Video preview
- Processing status polling
- Subtitle preview (SRT)
- Download translated video

Setup

1. Install dependencies

```bash
cd frontend
npm install
```

2. Create `.env.local` with your backend URL (optional)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run dev server

```bash
npm run dev
```
