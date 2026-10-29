import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const uploadVideo = async (file: File, onProgress?: (progress: number) => void) => {
  const formData = new FormData()
  formData.append('file', file)

  return api.post('/api/v1/videos/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(progress)
      }
    },
  })
}

export const startTranslation = (videoId: string) => {
  return api.post(`/api/v1/translations`, { video_id: videoId })
}

export const getTranslationStatus = (jobId: string) => {
  return api.get(`/api/v1/translations/${jobId}`)
}

export const getVideoList = () => {
  return api.get('/api/v1/videos')
}

export const downloadVideo = (jobId: string) => {
  return api.get(`/api/v1/translations/${jobId}/download`, {
    responseType: 'blob',
  })
}

export const createTTSJob = (text: string, voice: string) => {
  return api.post('/api/v1/tts', { text, voice })
}

export const getTTSJob = (jobId: string) => {
  return api.get(`/api/v1/tts/${jobId}`)
}

export const getTTSAudioUrl = (jobId: string) => {
  return `${API_URL}/api/v1/tts/${jobId}/audio`
}

export default api
