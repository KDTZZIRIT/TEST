import { create } from "zustand";
import { persist } from "zustand/middleware";

interface PcbStore {
  pcbData: any[];
  setPcbData: (pcbData: any[]) => void;

  scheduledInspections: any[];
  setScheduledInspections: (scheduledInspections: any[]) => void;

  originalPcbData: any[];
  setOriginalPcbData: (originalPcbData: any[]) => void;

  visionData: {id: string, pcb_id: string, name: string, urls: string[]} | null;
  setVisionData: (visionData: {id: string, pcb_id: string, name: string, urls: string[]} | null) => void;

  inspectionResults: any[];
  setInspectionResults: (inspectionResults: any[] | ((prev: any[]) => any[])) => void;
  
  isInspectionRunning: boolean;
  setIsInspectionRunning: (isInspectionRunning: boolean) => void;
  
  currentInspectionIndex: number;
  setCurrentInspectionIndex: (currentInspectionIndex: number) => void;
  
  selectedInspection: any;
  setSelectedInspection: (selectedInspection: any) => void;

  inspectionHistory: any[];
  setInspectionHistory: (inspectionHistory: any[]) => void;
  addToInspectionHistory: (inspectionData: any) => void;

}


const pcbStore = create<PcbStore>()(
  // 로컬스토리지에 자동 저장
  persist(
    (set, get) => ({
      pcbData: [],
      setPcbData: (pcbData) => set({ pcbData }),

      scheduledInspections: [],
      setScheduledInspections: (scheduledInspections) => set({ scheduledInspections }),

      originalPcbData: [],
      setOriginalPcbData: (originalPcbData) => set({ originalPcbData }),

      visionData: null,
      setVisionData: (visionData) => set({ visionData }),

      inspectionResults: [],
      setInspectionResults: (inspectionResults) => set((state) => ({ 
        inspectionResults: typeof inspectionResults === 'function' 
          ? inspectionResults(state.inspectionResults) 
          : inspectionResults 
      })),
      
      isInspectionRunning: false,
      setIsInspectionRunning: (isInspectionRunning) => set({ isInspectionRunning }),
      
      currentInspectionIndex: 0,
      setCurrentInspectionIndex: (currentInspectionIndex) => set({ currentInspectionIndex }),
      
      selectedInspection: null,
      setSelectedInspection: (selectedInspection) => set({ selectedInspection }),

      inspectionHistory: [],
      setInspectionHistory: (inspectionHistory) => set({ inspectionHistory }),
      addToInspectionHistory: (inspectionData) => set((state) => {
        const newHistory = [inspectionData, ...state.inspectionHistory]
        // 최근 100개 결과만 유지
        return { inspectionHistory: newHistory.slice(0, 100) }
      }),

    }),
    {
      name: "pcb-storage", // localStorage에 저장될 키 이름
    }
  )
);

export default pcbStore;
