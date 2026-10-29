'use client'

import { useEffect, useState } from 'react'
import { VideoUploader } from '@/components/VideoUploader'
import { VideoList } from '@/components/VideoList'
import { TranslationPanel } from '@/components/TranslationPanel'
import { TTSPanel } from '@/components/TTSPanel'
import { useStore } from '@/lib/store'
import { getVideoList } from '@/lib/api'

export default function Home() {
  const setVideos = useStore((state) => state.setVideos)
  const [view, setView] = useState<'text' | 'video'>('text')
  const [videoError, setVideoError] = useState(false)
  const [videosLoading, setVideosLoading] = useState(true)

  useEffect(() => {
    const fetchVideos = async () => {
      try {
        const response = await getVideoList()
        setVideos(response.data)
        setVideoError(false)
      } catch (error) {
        console.error('Failed to fetch videos:', error)
        setVideoError(true)
      } finally {
        setVideosLoading(false)
      }
    }

    fetchVideos()
    const interval = setInterval(fetchVideos, 5000)
    return () => clearInterval(interval)
  }, [setVideos])

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <div className="brand"><span className="brand-mark" aria-hidden="true">文</span><div><strong>Video Translator</strong><span>CHINESE TO VIETNAMESE</span></div></div>
          <nav className="main-nav" aria-label="Không gian làm việc">
            <button type="button" aria-pressed={view === 'text'} className={view === 'text' ? 'active' : ''} onClick={() => setView('text')}>Văn bản & giọng đọc</button>
            <button type="button" aria-pressed={view === 'video'} className={view === 'video' ? 'active' : ''} onClick={() => setView('video')}>Dịch video</button>
          </nav>
          <span className="header-caption">STUDIO <span> / </span> VI</span>
        </div>
      </header>
      <main className="main-content">
        <div hidden={view !== 'text'}><TTSPanel /></div>
        <div hidden={view !== 'video'} className="workspace">
          <div className="workspace-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> VIDEO TRANSLATOR</div><h1>Dịch video</h1><p>Quản lý video và theo dõi tiến độ dịch.</p></div><span className="language-pair">中文 <span aria-hidden="true">→</span> Tiếng Việt</span></div>
          {videoError && <p role="alert" className="message message-error">Không thể tải danh sách video. Đang thử kết nối lại.</p>}
          <div className="video-layout">
            <div className="video-main"><section className="video-section"><div className="section-heading"><div><span className="section-index">01</span><h2>Tải video lên</h2></div></div><VideoUploader /></section><section className="video-section"><div className="section-heading"><div><span className="section-index">02</span><h2>Video của bạn</h2></div></div>{videosLoading ? <p role="status" className="video-empty">Đang tải danh sách video...</p> : !videoError && <VideoList />}</section></div>
            <TranslationPanel />
          </div>
        </div>
      </main>
      <footer className="app-footer"><span>VIDEO TRANSLATOR</span><span>中文 → TIẾNG VIỆT</span></footer>
    </div>
  )
}