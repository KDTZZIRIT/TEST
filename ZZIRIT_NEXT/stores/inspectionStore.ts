import { create } from 'zustand'

interface InspectionProgress {
  progress: number
  currentStep: number
  totalSteps: number
  isRunning: boolean
  currentImage: string
  status: 'idle' | 'running' | 'completed' | 'error'
  message: string
  pcbName: string
  defectRate: number
}

interface InspectionStore {
  inspectionProgress: InspectionProgress
  updateProgress: (progress: Partial<InspectionProgress>) => void
  resetProgress: () => void
  startInspection: (totalSteps: number, pcbName?: string) => void
  completeInspection: () => void
  setError: (message: string) => void
}

export const useInspectionStore = create<InspectionStore>((set, get) => ({
  inspectionProgress: {
    progress: 0,
    currentStep: 0,
    totalSteps: 0,
    isRunning: false,
    currentImage: '',
    status: 'idle',
    message: '',
    pcbName: '',
    defectRate: 0
  },

  updateProgress: (progress) => set((state) => ({
    inspectionProgress: { ...state.inspectionProgress, ...progress }
  })),

  resetProgress: () => set((state) => ({
    inspectionProgress: {
      progress: 0,
      currentStep: 0,
      totalSteps: 0,
      isRunning: false,
      currentImage: '',
      status: 'idle',
      message: '',
      pcbName: '',
      defectRate: 0
    }
  })),

  startInspection: (totalSteps: number, pcbName: string = '') => set((state) => ({
    inspectionProgress: {
      ...state.inspectionProgress,
      progress: 0,
      currentStep: 0,
      totalSteps,
      isRunning: true,
      status: 'running',
      message: '검사가 시작되었습니다.',
      pcbName,
      defectRate: 0
    }
  })),

  completeInspection: () => set((state) => ({
    inspectionProgress: {
      ...state.inspectionProgress,
      progress: 100,
      isRunning: false,
      status: 'completed',
      message: '검사가 완료되었습니다.'
    }
  })),

  setError: (message: string) => set((state) => ({
    inspectionProgress: {
      ...state.inspectionProgress,
      isRunning: false,
      status: 'error',
      message
    }
  }))
})) 