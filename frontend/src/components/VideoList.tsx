'use client'

import React from 'react'
import { useStore } from '@/lib/store'
import { formatDistanceToNow } from 'date-fns'
import { vi } from 'date-fns/locale'

export const VideoList: React.FC = () => {
  const videos = useStore((state) => state.videos)

  if (videos.length === 0) {
    return (
      <div className="video-empty">
        <p>Chưa có video nào</p><span>Video đã tải lên sẽ xuất hiện tại đây.</span>
      </div>
    )
  }

  return (
    <div className="video-list">
      {videos.map((video) => (
        <div key={video.id} className="video-row">
          <div className="video-details">
            <h3>{video.original_filename}</h3>
            <p>
              {formatDistanceToNow(new Date(video.upload_date), { locale: vi, addSuffix: true })}
              {' · '}{(video.file_size / (1024 * 1024)).toFixed(1)} MB
            </p>
          </div>
          <div className="video-state">
            <div className={`video-badge ${getStatusColor(video.status)}`}>
              {getStatusText(video.status)}
            </div>
            {video.progress > 0 && video.progress < 100 && (
              <div className="video-row-progress">
                <progress max="100" value={video.progress} aria-label={`Tiến độ ${video.original_filename}`} />
                <span>{video.progress}%</span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800'
    case 'processing':
      return 'bg-blue-100 text-blue-800'
    case 'failed':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function getStatusText(status: string): string {
  switch (status) {
    case 'completed':
      return 'Hoàn thành'
    case 'processing':
      return 'Đang xử lý'
    case 'failed':
      return 'Thất bại'
    case 'uploaded':
      return 'Đã tải lên'
    default:
      return status
  }
}
