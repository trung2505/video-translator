'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { createTTSJob, getTTSJob, getTTSAudioUrl } from '@/lib/api'

const MAX_TEXT_LENGTH = 100_000
const voices = [
  { value: 'female_young_adult', label: 'Nữ trẻ' },
  { value: 'male_young_adult', label: 'Nam trẻ' },
  { value: 'female_elderly', label: 'Nữ lớn tuổi' },
  { value: 'male_deep_voice', label: 'Nam trầm' },
  { value: 'female_child', label: 'Bé gái' },
]

type TTSJob = {
  id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  error_message?: string | null
}

const statusLabels: Record<TTSJob['status'], string> = {
  queued: 'Đang chờ xử lý',
  running: 'Đang tạo giọng đọc',
  completed: 'Đã tạo âm thanh',
  failed: 'Không thể tạo âm thanh',
}

export function TTSPanel() {
  const [source, setSource] = useState('')
  const [text, setText] = useState('')
  const [voice, setVoice] = useState(voices[0].value)
  const [job, setJob] = useState<TTSJob | null>(null)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!job || (job.status !== 'queued' && job.status !== 'running')) return
    const timer = window.setInterval(async () => {
      try {
        const response = await getTTSJob(job.id)
        setJob(response.data)
        setError(response.data.status === 'failed' ? (response.data.error_message || 'Không thể tạo file MP3.') : '')
      } catch {
        setError('Không thể cập nhật trạng thái xử lý. Đang thử lại.')
      }
    }, 2000)
    return () => window.clearInterval(timer)
  }, [job])

  const submit = async () => {
    setError('')
    if (!text.trim()) {
      setError('Vui lòng nhập văn bản tiếng Việt.')
      return
    }
    if (text.length > MAX_TEXT_LENGTH) {
      setError(`Văn bản không được vượt quá ${MAX_TEXT_LENGTH.toLocaleString('vi-VN')} ký tự.`)
      return
    }
    setIsSubmitting(true)
    setJob(null)
    try {
      const response = await createTTSJob(text, voice)
      setJob(response.data)
    } catch (requestError) {
      const detail = axios.isAxiosError(requestError) ? requestError.response?.data?.detail : null
      setError(typeof detail === 'string' ? detail : 'Không thể tạo yêu cầu TTS. Vui lòng thử lại.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const audioUrl = job?.status === 'completed' ? getTTSAudioUrl(job.id) : null
  const busy = isSubmitting || job?.status === 'queued' || job?.status === 'running'

  return (
    <div className="workspace">
      <div className="workspace-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> KHÔNG GIAN LÀM VIỆC</div>
          <h1>Văn bản & giọng đọc</h1>
          <p>Chuẩn bị nội dung và tạo giọng đọc tiếng Việt.</p>
        </div>
        <span className="language-pair">中文 <span aria-hidden="true">→</span> Tiếng Việt</span>
      </div>
      <div className="text-grid">
        <section className="editor-panel" aria-labelledby="source-title">
          <div className="editor-heading">
            <div><span className="section-index">01</span><h2 id="source-title">Văn bản gốc</h2></div>
            <span className="language-label">TIẾNG TRUNG</span>
          </div>
          <label className="sr-only" htmlFor="source-text">Văn bản tiếng Trung</label>
          <textarea id="source-text" value={source} onChange={(event) => setSource(event.target.value)} placeholder="Nhập hoặc dán văn bản tiếng Trung..." />
          <div className="editor-footer">
            <span>{source.length.toLocaleString('vi-VN')} ký tự</span>
            <button type="button" className="button button-secondary" disabled>Dịch văn bản</button>
          </div>
          <p className="inline-note">Dịch văn bản riêng lẻ chưa được hỗ trợ.</p>
        </section>
        <section className="editor-panel output-panel" aria-labelledby="output-title">
          <div className="editor-heading">
            <div><span className="section-index">02</span><h2 id="output-title">Nội dung tiếng Việt</h2></div>
            <span className="language-label language-label-green">TIẾNG VIỆT</span>
          </div>
          <label className="sr-only" htmlFor="tts-text">Văn bản tiếng Việt để tạo giọng đọc</label>
          <textarea id="tts-text" value={text} onChange={(event) => setText(event.target.value)} maxLength={MAX_TEXT_LENGTH} placeholder="Nhập hoặc dán nội dung tiếng Việt cần đọc..." />
          <div className="editor-footer"><span>Nội dung cho giọng đọc</span><span>{text.length.toLocaleString('vi-VN')} / {MAX_TEXT_LENGTH.toLocaleString('vi-VN')}</span></div>
        </section>
      </div>
      <section className="voice-section" aria-labelledby="voice-title">
        <div className="section-heading"><div><span className="section-index">03</span><h2 id="voice-title">Giọng đọc</h2></div><span className="provider-label"><span /> OmniVoice</span></div>
        <div className="voice-controls">
          <label className="field-label" htmlFor="voice-select">Chọn giọng
            <select id="voice-select" value={voice} onChange={(event) => setVoice(event.target.value)}>
              <optgroup label="OmniVoice">
                {voices.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </optgroup>
              <optgroup label="Chưa khả dụng">
                <option disabled>BV421 — Nhỏ Ngọt Ngào</option>
                <option disabled>BV074 — Cô Gái Hoạt Ngôn</option>
              </optgroup>
            </select>
          </label>
          <button type="button" onClick={submit} disabled={busy} className="button button-primary">{isSubmitting ? 'Đang gửi...' : busy ? 'Đang xử lý...' : 'Tạo giọng đọc'} <span aria-hidden="true">→</span></button>
        </div>
        <p className="inline-note">BV421 và BV074 chưa được tích hợp.</p>
        {job && <div className="job-status" role="status"><div><strong>{statusLabels[job.status] || job.status}</strong><span>{job.progress}%</span></div><progress max="100" value={job.progress} /></div>}
        {error && <p role="alert" className="message message-error">{error}</p>}
        {audioUrl && <div className="audio-result"><div><strong>Âm thanh của bạn</strong><span>MP3 · Sẵn sàng tải xuống</span></div><audio controls src={audioUrl} aria-label="Nghe giọng đọc" /><a href={audioUrl} download className="button button-secondary">Tải MP3 ↓</a></div>}
      </section>
    </div>
  )
}