// store/abortStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AbortStore {
  controller: AbortController | null
  setController: (controller: AbortController | null) => void
  abort: () => void
}

const useAbortStore = create<AbortStore>()(
  persist(
    (set, get) => ({
      controller: null,
      setController: (controller) => set({ controller }),
      abort: () => {
        get().controller?.abort()
        set({ controller: null }) // 한 번 abort 후 초기화
      },
    }),
    {
      name: "abort-storage", // localStorage에 저장될 키 이름
    }
  )
)

export default useAbortStore