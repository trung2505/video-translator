import { create } from 'zustand'
import { Video, TranslationJob } from '@/types'

interface Store {
  videos: Video[]
  currentJob: TranslationJob | null
  setVideos: (videos: Video[]) => void
  setCurrentJob: (job: TranslationJob | null) => void
  addVideo: (video: Video) => void
  updateJobProgress: (progress: number) => void
}

export const useStore = create<Store>((set) => ({
  videos: [],
  currentJob: null,
  setVideos: (videos) => set({ videos }),
  setCurrentJob: (currentJob) => set({ currentJob }),
  addVideo: (video) => set((state) => ({ videos: [video, ...state.videos] })),
  updateJobProgress: (progress) =>
    set((state) => ({
      currentJob: state.currentJob ? { ...state.currentJob, progress } : null,
    })),
}))
