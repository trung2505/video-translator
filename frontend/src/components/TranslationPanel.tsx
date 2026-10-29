'use client'

import React, { useEffect, useState } from 'react'
import { useStore } from '@/lib/store'
import { startTranslation, downloadVideo, getTranslationStatus } from '@/lib/api'

interface TranslationPanelProps {
  videoId?: string
}

export const TranslationPanel: React.FC<TranslationPanelProps> = ({ videoId }) => {
  const videos = useStore((state) => state.videos)
  const [selectedVideoId, setSelectedVideoId] = useState(videoId || '')
  const [translating, setTranslating] = useState(false)
  const [job, setJob] = useState<{ id: string; status: string; progress: number; error_message?: string | null } | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!job || job.status === 'completed' || job.status === 'failed') return
    const timer = window.setInterval(async () => {
      try {
        const response = await getTranslationStatus(job.id)
        setJob(response.data)
        setError('')
      } catch {
        setError('Không thể cập nhật trạng thái video. Đang thử lại.')
      }
    }, 2000)
    return () => window.clearInterval(timer)
  }, [job])

  const handleStartTranslation = async () => {
    if (!selectedVideoId) {
      setError('Vui lòng chọn video.')
      return
    }

    setError('')
    setTranslating(true)
    try {
      const response = await startTranslation(selectedVideoId)
      setJob({ id: response.data.id, status: response.data.status, progress: 0 })
    } catch (error) {
      console.error('Translation failed:', error)
      setError('Không thể bắt đầu dịch video. Vui lòng thử lại.')
    } finally {
      setTranslating(false)
    }
  }

  const handleDownload = async () => {
    try {
      if (!job) return
      const response = await downloadVideo(job.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'translated_video.mp4')
      document.body.appendChild(link)
      link.click()
      link.parentElement?.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
      setError('Không thể tải video. Vui lòng thử lại.')
    }
  }

  return (
    <section className="video-job" aria-labelledby="video-job-title">
      <div className="section-heading"><div><span className="section-index">03</span><h2 id="video-job-title">Bắt đầu dịch</h2></div></div>
      <p className="video-job-intro">Chọn video đã tải lên để bắt đầu xử lý.</p>
      <div className="video-job-field">
        <label htmlFor="video-select" className="field-label">Chọn video</label>
        <select
          id="video-select"
          value={selectedVideoId}
          onChange={(e) => { setSelectedVideoId(e.target.value); setJob(null); setError('') }}
          disabled={translating || (!!job && job.status !== 'completed' && job.status !== 'failed')}
          className="video-select"
        >
          <option value="">Chọn video</option>
          {videos
            .filter((v) => v.status === 'uploaded')
            .map((video) => (
              <option key={video.id} value={video.id}>
                {video.original_filename}
              </option>
            ))}
        </select>
      </div>

      {job?.status !== 'completed' ? (
        <button
          onClick={handleStartTranslation}
          disabled={!selectedVideoId || translating || (!!job && job.status !== 'completed' && job.status !== 'failed')}
          className="button button-primary video-action"
        >
          {translating ? 'Đang xử lý...' : 'Bắt đầu dịch'}
        </button>
      ) : (
        <div>
          <p role="status" className="video-success">Video đã dịch xong.</p>
          <button
            onClick={handleDownload}
            className="button button-primary video-action"
          >
            Tải video đã dịch
          </button>
        </div>
      )}
      {job && job.status !== 'completed' && (
        <div role="status" className="job-status">
          <div><strong>{job.status === 'failed' ? (job.error_message || 'Dịch video thất bại.') : job.status === 'queued' ? 'Đang chờ xử lý' : 'Đang xử lý'}</strong><span>{job.progress}%</span></div>
          <progress max="100" value={job.progress} />
        </div>
      )}
      {error && <p role="alert" className="message message-error">{error}</p>}
    </section>
  )
}
