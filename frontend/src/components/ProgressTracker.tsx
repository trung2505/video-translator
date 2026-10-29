'use client'

import React, { useEffect } from 'react'
import { useStore } from '@/lib/store'
import { getTranslationStatus } from '@/lib/api'

export const ProgressTracker: React.FC = () => {
  const currentJob = useStore((state) => state.currentJob)
  const updateJobProgress = useStore((state) => state.updateJobProgress)

  useEffect(() => {
    if (!currentJob) return

    const interval = setInterval(async () => {
      try {
        const response = await getTranslationStatus(currentJob.id)
        updateJobProgress(response.data.progress)
      } catch (error) {
        console.error('Failed to fetch status:', error)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [currentJob, updateJobProgress])

  if (!currentJob) return null

  const steps = [
    { name: 'Tải lên video', status: 'completed' },
    { name: 'Trích xuất âm thanh', status: currentJob.progress >= 20 ? 'completed' : 'pending' },
    { name: 'Nhận dạng giọng nói', status: currentJob.progress >= 40 ? 'completed' : 'pending' },
    { name: 'Dịch văn bản', status: currentJob.progress >= 60 ? 'completed' : 'pending' },
    { name: 'Tạo phụ đề', status: currentJob.progress >= 80 ? 'completed' : 'pending' },
    { name: 'Đốt phụ đề vào video', status: currentJob.progress >= 100 ? 'completed' : 'pending' },
  ]

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-6">Tiến độ xử lý</h2>
      <div className="space-y-4">
        {steps.map((step, index) => (
          <div key={index} className="flex items-center">
            <div
              className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
                step.status === 'completed' ? 'bg-green-500 text-white' : 'bg-gray-300'
              }`}
            >
              {step.status === 'completed' ? '✓' : index + 1}
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-gray-900">{step.name}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className="bg-primary-500 h-2 rounded-full transition-all" style={{ width: `${currentJob.progress}%` }}></div>
        </div>
        <p className="text-right text-sm text-gray-600 mt-2">{currentJob.progress}%</p>
      </div>
    </div>
  )
}
