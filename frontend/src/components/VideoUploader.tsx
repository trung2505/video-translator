'use client'

import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { uploadVideo } from '@/lib/api'
import { useStore } from '@/lib/store'

export const VideoUploader: React.FC = () => {
  const [uploading, setUploading] = React.useState(false)
  const [progress, setProgress] = React.useState(0)
  const [error, setError] = React.useState('')
  const addVideo = useStore((state) => state.addVideo)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return

      const file = acceptedFiles[0]
      setError('')
      setUploading(true)
      setProgress(0)

      try {
        const response = await uploadVideo(file, setProgress)
        addVideo(response.data)
        setProgress(100)
        setTimeout(() => setUploading(false), 1000)
      } catch (error) {
        console.error('Upload failed:', error)
        setError('Không thể tải video lên. Vui lòng thử lại.')
        setUploading(false)
      }
    },
    [addVideo]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDropRejected: () => setError('Định dạng video không được hỗ trợ.'),
    multiple: false,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'],
    },
    disabled: uploading,
  })

  return (
    <div>
    <div {...getRootProps({ className: `upload-zone ${isDragActive ? 'drag-active' : ''}`, 'aria-label': 'Chọn video để tải lên' })}>
      <input {...getInputProps()} />
      {uploading ? (
        <div role="status" className="upload-progress">
          <p>Đang tải lên · {progress}%</p>
          <progress max="100" value={progress} />
        </div>
      ) : (
        <div>
          <span className="upload-symbol" aria-hidden="true">↑</span>
          <p className="upload-title">Kéo video vào đây hoặc <strong>chọn tệp</strong></p>
          <p className="upload-formats">MP4, AVI, MOV, MKV, FLV, WMV</p>
        </div>
      )}
    </div>
    {error && <p role="alert" className="message message-error">{error}</p>}
    </div>
  )
}
