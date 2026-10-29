export interface Video {
  id: string
  original_filename: string
  upload_date: string
  status: 'uploaded' | 'processing' | 'completed' | 'failed'
  progress: number
  duration: number
  file_size: number
  error_message?: string
}

export interface TranslationJob {
  id: string
  video_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  created_at: string
  completed_at?: string
  result?: TranslationResult
  error_message?: string
}

export interface TranslationResult {
  subtitles_url: string
  translated_video_url: string
  language: string
  duration: number
}

export interface ProcessingStep {
  name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
}
