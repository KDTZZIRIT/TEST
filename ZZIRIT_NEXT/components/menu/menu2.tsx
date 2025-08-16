import React, { useState, useRef, useEffect } from "react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import useAbortStore from "@/stores/abortStore"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import {
  Calendar,
  Eye,
  Activity,
  Search,
  ChevronDown,
  Plus,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Trash2,
  Bot,
  Check,
  X,
  CircuitBoard,
  Brain,
  Zap,
} from "lucide-react"
import pcbStore from "@/stores/pcbStore"
import { useInspectionStore } from "@/stores/inspectionStore"




const Menu2 = () => {
  const [showReservationModal, setShowReservationModal] = useState(false)
  const [selectedPcb, setSelectedPcb] = useState<any>(null)
  const [inspectionDate, setInspectionDate] = useState("")
  const [inspectionType, setInspectionType] = useState("incoming")
  const [inspectionMethod, setInspectionMethod] = useState("full")
  const { isInspectionRunning, setIsInspectionRunning, currentInspectionIndex, setCurrentInspectionIndex, inspectionResults, setInspectionResults } = pcbStore();
  const inspectionStartTimeRef = useRef<number | null>(null)
  const individualInspectionStartTimeRef = useRef<number | null>(null)
  const { controller, setController, abort } = useAbortStore()
  const { pcbData, setPcbData } = pcbStore();
  const [ matchedUrls, setMatchedUrls ] = useState<{urls: string[], name: string, id: string, count: number} | null>(null)
  const { visionData, setVisionData } = pcbStore();
  const [showCalendarModal, setShowCalendarModal] = useState(false)
  const [currentDate, setCurrentDate] = useState(new Date())
  const { scheduledInspections, setScheduledInspections } = pcbStore();
  const { originalPcbData, setOriginalPcbData } = pcbStore();
  const [searchTerm, setSearchTerm] = useState("")
  const [materialFilter, setMaterialFilter] = useState("all")
  const { selectedInspection, setSelectedInspection } = pcbStore();
  const { addToInspectionHistory } = pcbStore();
  const { startInspection, updateProgress, completeInspection, setError } = useInspectionStore();

  // 컴포넌트 마운트 시 상태 동기화
  useEffect(() => {
    // 컴포넌트가 마운트될 때 Zustand store의 상태 확인
    const currentStore = pcbStore.getState()
    
    // 만약 검사가 실행 중이지만 AbortController가 없다면 검사를 중단
    if (currentStore.isInspectionRunning && !controller) {
      console.log('컴포넌트 마운트 시 검사 상태 동기화: 검사 중단')
      setIsInspectionRunning(false)
      setCurrentInspectionIndex(0)
      setVisionData(null)
      setSelectedInspection(null)
    }
  }, [controller, setIsInspectionRunning, setCurrentInspectionIndex, setVisionData, setSelectedInspection])

  // 재질별 필터링 함수
  const getUniqueMaterials = () => {
    if (!Array.isArray(pcbData)) return [];
    const materials = pcbData.map(pcb => pcb.substrate).filter(Boolean);
    return [...new Set(materials)].sort();
  };

  // 검색 및 재질 필터링 함수
  const filteredPcbData = Array.isArray(pcbData) ? pcbData.filter((pcb) => {
    // 검색어 필터링
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      const pcbId = `PCB${pcb.id}`.toLowerCase();
      const pcbName = pcb.name.toLowerCase();
      
      if (!pcbId.includes(searchLower) && !pcbName.includes(searchLower)) {
        return false;
      }
    }
    
    // 재질 필터링
    if (materialFilter !== "all" && pcb.substrate !== materialFilter) {
      return false;
    }
    
    return true;
  }) : [];

  //PCB 이미지 불러오기 (새로고침) - 예약된 PCB 제외
  const refreshClick = () => {
            fetch("http://43.201.249.204:5000/api/user/pcb-summary")
      .then(res => res.json())
      .then(data => {

        // 예약된 PCB ID 목록 생성
        const reservedPcbIds = Array.isArray(scheduledInspections) 
          ? scheduledInspections.map(inspection => inspection.pcb_id)
          : [];


        // 1단계: 전체 데이터를 먼저 변환 (복구용 원본 데이터)
        const allPcbData = data.map((item: any, index: number) => ({
          id: item.pcb_id, // PCB ID를 고유 ID로 사용
          pcb_id: item.pcb_id,
          name: item.pcbName,
          size: item.size,
          count: item.count,
          substrate: item.substrate,
          smt: item.smt,
          manufactureDate: item.manufactureDate ? (() => {
            try {
              // 년,월,일로 표현
              const year = item.manufactureDate.substring(0, 4);
              const month = item.manufactureDate.substring(4, 6);
              const day = item.manufactureDate.substring(6, 8);
              return `${year}년 ${parseInt(month)}월 ${parseInt(day)}일`;
            } catch (error) {
              return item.manufactureDate;
            }
          })() : '',
          urls: item.urls,
          imageUrl: Array.isArray(item.urls) ? item.urls[0] : item.urls
        }));

        // 예약되지 않은 PCB만 필터링 (미리보기용)
        const availablePcbData = allPcbData.filter((item: any) => 
          !reservedPcbIds.includes(item.pcb_id)
        );

        // 중복 제거 (pcb_id 기준)
        const uniqueAvailablePcbData = availablePcbData.filter((item: any, index: number, self: any[]) => 
          index === self.findIndex((t: any) => t.pcb_id === item.pcb_id)
        );


        // 핵심: 전체 데이터를 원본으로, 필터링된 데이터를 미리보기용으로 분리
        setOriginalPcbData(allPcbData);  // 예약된 PCB 포함한 전체 데이터 (복구용)
        setPcbData(uniqueAvailablePcbData);  // 예약되지 않은 PCB만 (미리보기용)


      })
      .catch(error => {
        console.error("데이터 로드 실패:", error);
      });
  };

  // 검사 예약 버튼 클릭시
  const handleInspectionReservation = (pcb: any) => {
    setSelectedPcb(pcb)
    setShowReservationModal(true)
  }


  // 모달안 검사 예약 완료 버튼 클릭시
  const handleReservationComplete = () => {
    setShowReservationModal(false)
    
    // 선택한 pcb의 urls 리스트를 가져오기
    const target = pcbData.find((item) => item.id === selectedPcb.id);

    const matchedUrls = {
      pcb_id: target ? target.pcb_id : "",
      urls: target ? target.urls : [],
      name: target ? target.name : "",
      id: target ? target.id : "",
      count: target ? target.count : 0,
    };
    setMatchedUrls(matchedUrls);
    console.log("matchedUrls:", matchedUrls);

    // 새로운 검사 일정을 scheduledInspections에 추가
    if (inspectionDate && selectedPcb) {
      const newInspection = {
        id: matchedUrls.id,
        pcb_id: matchedUrls.pcb_id,
        pcbName: matchedUrls.name,
        date: inspectionDate,
        type: inspectionType === 'incoming' ? '입고검사' : '투입전 검사',
        method: inspectionMethod === 'full' ? '전수검사' : '샘플검사',
        count: matchedUrls.count,
        urls: matchedUrls.urls,
      };
      
      
      setScheduledInspections(Array.isArray(scheduledInspections) ? [...scheduledInspections, newInspection] : [newInspection]);
      
      // PCB 미리보기에서 해당 카드 제거
      const updatedPcbData = pcbData.filter((item: any) => item.id !== selectedPcb.id);
      setPcbData(updatedPcbData);
    }


    // 검사 일정 모달 표시
    setShowCalendarModal(true)
    
    setSelectedPcb(null)
    setInspectionDate("")
    setInspectionType("incoming")
    setInspectionMethod("full")
  }

  const getScheduledInspectionsForDate = (date: Date) => {
    // 예약된 검사 일정을 날짜별로 필터링
    return Array.isArray(scheduledInspections) ? scheduledInspections.filter(inspection => {
      const inspectionDate = new Date(inspection.date)
      return inspectionDate.toDateString() === date.toDateString()
    }) : []
  }

  const isToday = (date: Date) => {
    const today = new Date()
    return date.toDateString() === today.toDateString()
  }

  // 날짜 클릭 시 해당 날짜의 예약된 검사 일정 표시
  const handleDateClick = (date: Date) => {
    const inspections = getScheduledInspectionsForDate(date)
    if (inspections.length > 0) {
      console.log(`${date.toLocaleDateString()} 예약된 검사 일정:`, inspections)
    }
  }

  // 검사일정 선택하기
  const handleSelectInspection = (inspection: any) => {
    setSelectedInspection(inspection)

    const visionData = {
      id: inspection.id,
      pcb_id: inspection.pcb_id,
      name: inspection.pcbName,
      urls: inspection.urls,
    }
    setVisionData(visionData)
  }

  // 검사 일정 삭제
  const handleDeleteInspection = (inspectionId: string) => {
    const inspectionToDelete = Array.isArray(scheduledInspections) ? scheduledInspections.find(inspection => inspection.id === inspectionId) : undefined


    if (inspectionToDelete) {
      // 검사일정에서 삭제
      setScheduledInspections(Array.isArray(scheduledInspections) ? scheduledInspections.filter(inspection => inspection.id !== inspectionId) : [])
      
      // ⭐ PCB ID로 원본 데이터에서 복구할 PCB 찾기
      const originalPcb = originalPcbData.find(pcb => pcb.pcb_id === inspectionToDelete.pcb_id)

      
      // 이미 미리보기에 있는지 확인 (중복 방지)
      const alreadyExists = pcbData.find(pcb => pcb.pcb_id === inspectionToDelete.pcb_id);

      if (originalPcb && !alreadyExists) {
        // 원본 데이터를 그대로 복원
        setPcbData([...pcbData, originalPcb])
      } else if (alreadyExists) {
        console.log("⚠️ 이미 존재하므로 복구 생략");
      } else {
        console.log("❌ 원본 데이터에서 PCB를 찾을 수 없음");
      }
      
      // 만약 삭제된 검사일정이 현재 선택된 검사일정이라면 슬라이드에서도 제거
      if (selectedInspection?.id === inspectionId) {
        setVisionData(null)
        setSelectedInspection(null)
        setCurrentInspectionIndex(0)
      }
    } else {
      console.log("❌ 삭제할 검사를 찾을 수 없음");
    }
  }

  // 검사 중지 함수
  const handleStopInspection = () => {
    // 진행 중인 fetch 요청 중단
    if (controller) {
      abort()
      setController(null)
    }
    
    setIsInspectionRunning(false)
    setCurrentInspectionIndex(0)
    setInspectionResults([]) // 실시간 검사 결과도 모두 지우기
    setVisionData(null)
    setSelectedInspection(null)
    inspectionStartTimeRef.current = null
    individualInspectionStartTimeRef.current = null
    
    // inspectionStore 초기화
    completeInspection()
  }

  // AI 비전 검사 시작 (검사 하기 버튼 클릭시)
  const handleAIVisionInspection = (inspection: any) => {
    // 새로운 AbortController 생성
    setController(new AbortController())
    
    setIsInspectionRunning(true)
    setCurrentInspectionIndex(0)
    setInspectionResults([]) // 새로운 검사 시작 시 결과 초기화
    inspectionStartTimeRef.current = Date.now() // 검사 시작 시간 기록

    // 선택된 inspection의 데이터로 visionData 설정
    const visionData = {
      id: inspection.id,
      pcb_id: inspection.pcb_id,
      name: inspection.pcbName,
      urls: inspection.urls,
    }
    setVisionData(visionData)
    console.log("visionData:", visionData);

    // inspectionStore 시작 - PCB 이름 전달
    startInspection(visionData.urls.length, visionData.name)

    const simulateInspection = async (index: number) => {
       // Zustand store에서 실시간 상태 확인
       const currentStore = pcbStore.getState()
       
       // 검사가 중단되었는지 확인
       if (!currentStore.isInspectionRunning) {
         console.log('검사가 중단되어 시뮬레이션 중단')
         return
       }
       
       if (index >= (Array.isArray(visionData.urls) ? visionData.urls.length : 0)) {
         // 검사 완료 시 히스토리에 저장
         const currentResults = pcbStore.getState().inspectionResults
         if (Array.isArray(currentResults) && currentResults.length > 0) {
           const totalInspected = currentResults.length
           const defectiveCount = currentResults.filter(r => r.status === 'defective' || r.status === '불합격').length
           const passedCount = totalInspected - defectiveCount
           const defectRate = totalInspected > 0 ? Math.round((defectiveCount / totalInspected) * 100 * 10) / 10 : 0
           
           const inspectionSummary = {
             id: Date.now().toString(),
             pcbName: visionData.name,
             pcb_id: visionData.pcb_id,
             completedAt: new Date().toISOString(),
             totalInspected,
             passedCount,
             defectiveCount,
             defectRate,
             results: currentResults,
             inspectionTime: inspectionStartTimeRef.current ? Math.round((Date.now() - inspectionStartTimeRef.current) / 1000) : 0,
           }
           
           addToInspectionHistory(inspectionSummary)
         }
         
         setIsInspectionRunning(false)
         inspectionStartTimeRef.current = null // 검사 완료 시 시작 시간 초기화
         individualInspectionStartTimeRef.current = null
         setCurrentInspectionIndex(0) // 검사 인덱스 초기화
         setVisionData(null) // visionData 삭제
         setSelectedInspection(null) // 선택된 검사일정 초기화
         
         // inspectionStore 완료
         completeInspection()
         return
       }

      // 먼저 슬라이드를 현재 인덱스로 이동 (시각적 동기화)
      setCurrentInspectionIndex(index)
      
      // 개별 PCB 검사 시작 시간 기록
      individualInspectionStartTimeRef.current = Date.now()

      // inspectionStore 진행률 업데이트
      const progress = ((index + 1) / visionData.urls.length) * 100
      updateProgress({
        progress,
        currentStep: index + 1,
        currentImage: visionData.urls[index]
      })



      // PCB외관 비전 검사 진행
      try {
        const res = await fetch("http://43.201.249.204:5000/api/user/visionAI", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ pcb_id: visionData.pcb_id, imageUrl: visionData.urls[index] }),
          signal: controller?.signal,
        });

        // 비전 검사 결과 받아오기
        const visionResult = await res.json();
        console.log("비전 검사 결과:", visionResult);

        // 개별 PCB 검사 시간 계산 (현재 시간 - 개별 검사 시작 시간)
        const currentTime = Date.now()
        const inspectionTime = individualInspectionStartTimeRef.current ? Math.round((currentTime - individualInspectionStartTimeRef.current) / 1000) : 0

         // 검사 결과 생성
          const result = {
            id: visionData.id,
            pcb_id: visionResult.pcb_id, // PCB ID 추가
            name: visionData.name,
            status: visionResult.status,   // 불량 여부
            defects: visionResult.defects,   // 불량 (배열형태 -> 위치 (x1, y1, x2, y2), 불량종류(label), score(신뢰도))
            defect_count: visionResult.defect_count,   // 불량 개수
            confidence: visionResult.max_confidence,   // 신뢰도
            inspectionTime: inspectionTime,   // 검사 시간 (초 단위)
            timestamp: Date.now(), // 타임스탬프 추가
          }
         
         
         setInspectionResults(prev => {
           const currentResults = Array.isArray(prev) ? prev : []
           const newResults = [result, ...currentResults]
           console.log('새로운 검사 결과 추가:', result)
           console.log('전체 결과 개수:', newResults.length)
           
           // 실시간 불량률 계산
           const totalInspected = newResults.length
           const defectiveCount = newResults.filter(r => r.status === 'defective').length
           const defectRate = totalInspected > 0 ? (defectiveCount / totalInspected) * 100 : 0
           
           // inspectionStore에 불량률 업데이트
           updateProgress({
             defectRate: Math.round(defectRate * 10) / 10 // 소수점 1자리까지
           })
           
           return newResults
         })
         
          // 검사 결과 표시 후 바로 다음 검사로 이동 (Zustand store 상태 확인 후)
          const currentStore = pcbStore.getState()
          if (currentStore.isInspectionRunning) {
            simulateInspection(index + 1)
          }

        } catch (err: any) {
         if (err.name === 'AbortError') {
           return // 중단된 경우 조용히 종료
         }
         console.error('검사 중 오류 발생 :', err)
         
         // inspectionStore 오류 상태 설정
         setError('검사 중 오류가 발생했습니다.')
       }



    }

    simulateInspection(0)
  }



  // 캘린더 관련 함수들
  const handleCalendarClick = () => {
    setShowCalendarModal(true)
  }

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startingDayOfWeek = firstDay.getDay()
    
    return { daysInMonth, startingDayOfWeek }
  }

  const goToPreviousMonth = () => {
    setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))
  }

  const goToNextMonth = () => {``
    setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('ko-KR', { 
      year: 'numeric', 
      month: 'long' 
    })
  }





  

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 flex items-center justify-center">
            <Zap className="w-8 h-8 text-yellow-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">PCB VISION 검사 관리</h1>
          </div>
        </div>

      </div>

      {/* Enhanced PCB Inspection Target Preview */}
      <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-2">
              검사 대상 PCB 미리보기
            </CardTitle>
            <div className="flex items-center gap-3">

              {/* Material Filter */}
              <select 
                value={materialFilter}
                onChange={(e) => setMaterialFilter(e.target.value)}
                className="bg-[#0D1117] border border-[#30363D] text-white rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500/50 min-w-[120px]"
              >
                <option value="all">모든 재질</option>
                {getUniqueMaterials().map((material) => (
                  <option key={material} value={material}>
                    {material}
                  </option>
                ))}
              </select>

              {/* Search Input */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-4 h-4" />
                <Input
                  placeholder="PCB ID 또는 이름 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 w-48 bg-[#0D1117] border-[#30363D] text-white text-sm focus:ring-2 focus:ring-blue-500/50"
                />
              </div>

              {/* Filter Reset Button */}
              {(searchTerm || materialFilter !== "all") && (
                <Button
                  variant="outline"
                  size="sm"
                  className="bg-blue-500/20 border-blue-500/30 text-blue-300 hover:text-blue-200 hover:bg-blue-500/30 transition-all duration-200"
                  onClick={() => {
                    setSearchTerm("")
                    setMaterialFilter("all")
                  }}
                >
                  <X className="w-4 h-4" />
                </Button>
              )}

              {/* Refresh Button */}
              <Button
                variant="outline"
                size="sm"
                className="bg-blue-500/20 border-blue-500/30 text-blue-300 hover:text-blue-200 hover:bg-blue-500/30 transition-all duration-200"
                onClick={refreshClick}
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Horizontal Scrollable Container */}
          <div className="relative">
            {/* Scrollable PCB Cards */}
            <div className="overflow-x-auto [&::-webkit-scrollbar]:h-2 [&::-webkit-scrollbar-track]:bg-[#161B22] [&::-webkit-scrollbar-thumb]:bg-blue-500/60 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-blue-400/80 [&::-webkit-scrollbar-thumb]:transition-all [&::-webkit-scrollbar-thumb]:duration-300 scroll-smooth">
              {filteredPcbData.length > 0 ? (
                <div className="flex gap-4 pb-2" style={{ width: "max-content" }}>
                  {filteredPcbData.map((pcb, index) => (
                  <div
                    key={index}
                    className={`group relative bg-[#0D1117]/50 rounded-lg border transition-all duration-300 hover:scale-105 hover:shadow-lg flex-shrink-0 w-56 ${
                      materialFilter !== "all" && pcb.substrate === materialFilter
                        ? 'border-blue-500/50 shadow-blue-500/20'
                        : 'border-[#30363D] hover:border-blue-500/30'
                    }`}
                  >
                    <div className="p-4">
                      {/* PCB Image */}
                      <div className="relative mb-3">
                        <Image
                          src={pcb.imageUrl}
                          alt={pcb.name}
                          width={200}
                          height={120}
                          className="w-full h-28 object-cover rounded-lg bg-gray-700/20"
                        />
                      </div>

                      {/* PCB Title */}
                      <h3 className="text-white font-medium text-sm mb-3">{pcb.name}</h3>

                      {/* Metadata - 4 lines */}
                      <div className="space-y-1 text-xs mb-3">
                        <div className="flex justify-between">
                          <span className="text-gray-400">PCB ID:</span>
                          <span className="text-gray-300 font-mono">PCB{pcb.pcb_id}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">크기:</span>
                          <span className="text-gray-300">{pcb.size}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">재질:</span>
                          <span className={`font-medium ${
                            pcb.substrate === 'FR4' ? 'text-green-400' :
                            pcb.substrate === 'FR1' ? 'text-yellow-400' :
                            pcb.substrate === 'CEM1' ? 'text-blue-400' :
                            pcb.substrate === 'CEM3' ? 'text-purple-400' :
                            'text-gray-300'
                          }`}>
                            {pcb.substrate}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">SMT:</span>
                          <span className="text-gray-300">{pcb.smt}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">수량:</span>
                          <span className="text-gray-300">{pcb.count}개</span>
                        </div>
                      </div>

                      {/* Manufacturing Date */}
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-400">제조일:</span>
                        <span className="text-blue-400">{pcb.manufactureDate}</span>
                      </div>
                    </div>

                    {/* Hover Action Overlay */}
                    <div className="absolute inset-0 bg-blue-600/10 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                      <Button
                        size="sm"
                        className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg"
                        onClick={() => handleInspectionReservation(pcb)}
                      >
                        검사 예약
                      </Button>
                    </div>
                  </div>
                ))}
                </div>
              ) : (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <Search className="w-12 h-12 mx-auto mb-4 text-gray-500 opacity-50" />
                    <p className="text-gray-400 text-sm">
                      {searchTerm ? `"${searchTerm}"에 대한 검색 결과가 없습니다.` : "검색어를 입력해주세요."}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Summary Footer */}
          <div className="mt-4 pt-4 border-t border-[#30363D] flex items-center justify-between text-sm">
            {/* Filter Summary */}
            <div className="text-gray-400">
              {searchTerm || materialFilter !== "all" ? (
                <span>
                  필터링 결과: <span className="text-blue-400 font-medium">{filteredPcbData.length}</span>개 
                  {searchTerm && <span> (검색어: "{searchTerm}")</span>}
                  {materialFilter !== "all" && <span> (재질: {materialFilter})</span>}
                </span>
              ) : (
                <span>
                  전체: <span className="text-blue-400 font-medium">{filteredPcbData.length}</span>개
                </span>
              )}
            </div>
            
            {/* Available Materials */}
            <div className="text-gray-400">
              PCB 재질 종류: {getUniqueMaterials().join(", ")}
            </div>
              <div className="flex items-center gap-4">
                <span className="text-gray-400">검사 대기 PCB 수량:</span>
                <span className="text-white font-medium">
                  {Array.isArray(pcbData) 
                    ? pcbData.reduce((total, pcb) => total + (Array.isArray(pcb.urls) ? pcb.urls.length : 0), 0) 
                    : 0}개
                </span>
              </div>
            </div>
        </CardContent>
      </Card>

      {/* PCB Visual Inspection and Real-time Monitor */}
      <div className="grid grid-cols-3 gap-6">
        {/* PCB Visual Inspection */}
        <Card className="col-span-2 bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              PCB 외관 검사 및 불량 위치 분석
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Inspection Controls */}
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${isInspectionRunning ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></div>
                  <span className="text-sm text-gray-300">
                    {isInspectionRunning ? '검사 진행중...' : '대기중'}
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-blue-500/30 text-blue-400 hover:bg-blue-600/10 bg-transparent"
                  onClick={handleCalendarClick}
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  검사 일정
                </Button>
                <Button
                  size="sm"
                  className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg"
                  disabled={isInspectionRunning || !visionData}
                  onClick={async () => {
                    if (visionData && selectedInspection) {
                      // 부품 감소 로직
                      try {
                        const response = await fetch("http://43.201.249.204:5000/api/user/inspection", {
                          method: "POST",
                          headers: {
                            "Content-Type": "application/json",
                          },
                          body: JSON.stringify({
                            pcb_id: visionData.pcb_id,
                            count: (selectedInspection as any).count || 100 // 타입 캐스팅으로 count 접근
                          }),
                        });

                        const result = await response.json();
                        console.log("검사 요청 결과:", result);

                        if (response.ok) {
                          console.log("검사 요청 성공:", result);
                          handleAIVisionInspection({
                            id: visionData.id,
                            pcb_id: visionData.pcb_id,
                            pcbName: visionData.name,
                            urls: visionData.urls
                          });
                        } else {
                          console.error("검사 요청 실패:", result.message);
                        }
                      } catch (error) {
                        console.error("검사 요청 중 오류 발생:", error);
                      }
                    }
                  }}
                >
                  <Bot className="w-4 h-4 mr-2" />
                  검사하기
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-red-500/30 text-red-400 hover:bg-red-600/10 bg-transparent"
                  disabled={!isInspectionRunning}
                  onClick={handleStopInspection}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  검사중지
                </Button>
              </div>

              {/* PCB Production Line */}
              <div className="relative bg-[#0D1117]/50 rounded-lg p-8 border border-[#30363D] overflow-hidden">
                {/* Conveyor Belt Effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-gray-800/20 via-gray-600/20 to-gray-800/20 animate-pulse"></div>
                
                {/* Conveyor Belt Container */}
                <div className="relative bg-gradient-to-r from-gray-900/50 via-gray-700/30 to-gray-900/50 rounded-lg p-6 border border-gray-600/30 min-h-[280px]">
                  {/* Conveyor Belt Lines */}
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-gray-500/50 to-transparent"></div>
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-gray-500/50 to-transparent"></div>
                  
                  {/* PCB Images Line */}
                  <div className="absolute inset-0 flex flex-col justify-center items-center h-full w-full pointer-events-none overflow-hidden">
                    <div
                      className="flex gap-8 items-center h-full pointer-events-auto transition-transform duration-1000 ease-in-out"
                      style={{
                        transform: `translateX(calc(50% - ${currentInspectionIndex * (240 + 32)}px - 120px))`
                        // transform: isInspectionRunning
                        //   ? `translateX(calc(50% - 120px - ${currentInspectionIndex * 280}px))`
                        //   : 'translateX(0px)'
                      }}
                    >

                      {/* 검사 중 이미지 파일 관리 */}
                      {Array.isArray(visionData?.urls) && visionData.urls.map((pcb, index) => (
                        <div
                          key={index}
                          className={`relative transition-all duration-5000 flex-shrink-0 w-[240px] ${
                            isInspectionRunning && index === currentInspectionIndex
                              ? 'scale-125 shadow-2xl shadow-blue-500/50 z-20'
                              : index === currentInspectionIndex - 1
                              ? 'scale-90 opacity-70 z-10'
                              : index === currentInspectionIndex + 1
                              ? 'scale-90 opacity-70 z-10'
                              : 'scale-75 opacity-40 z-0'
                          }`}
                        >
                          <div className="relative w-full">
                            <Image
                              src={pcb || "/default-image.jpg"}
                              alt={`PCB ${visionData.name}`}
                              width={240}
                              height={180}
                              className={`w-full h-[180px] rounded-lg border-2 object-cover transition-all duration-1000 ${
                                isInspectionRunning && index === currentInspectionIndex
                                  ? 'border-blue-500 shadow-lg'
                                  : index < currentInspectionIndex
                                  ? 'border-gray-500 opacity-60'
                                  : 'border-[#30363D]'
                              }`}
                              style={{
                                filter: index < currentInspectionIndex ? 'grayscale(50%) brightness(0.7)' : 'none'
                              }}
                            />
                            
                            {/* Status Indicator */}
                            <div className="absolute -top-2 -right-2">
                              <div className={`w-5 h-5 rounded-full border-2 border-white transition-all duration-300 ${
                                index < currentInspectionIndex
                                  ? Array.isArray(inspectionResults) && inspectionResults.find(r => r.id === visionData?.id && r.name === visionData?.name)?.status === '합격'
                                    ? 'bg-green-500'
                                    : Array.isArray(inspectionResults) && inspectionResults.find(r => r.id === visionData?.id && r.name === visionData?.name)?.status === '불합격'
                                    ? 'bg-red-500'
                                    : 'bg-gray-500'
                                  : index === currentInspectionIndex
                                  ? 'bg-blue-500 animate-pulse'
                                  : 'bg-gray-400'
                              }`}></div>
                            </div>

                            {/* Inspection Progress */}
                            {isInspectionRunning && index === currentInspectionIndex && (
                              <div className="absolute inset-0 bg-blue-500/30 rounded-lg flex items-center justify-center">
                                <div className="w-8 h-8 border-3 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                              </div>
                            )}

                            {/* PCB Name */}
                            <div className={`absolute bottom-0 left-0 right-0 text-white text-xs p-2 rounded-b-lg text-center transition-all duration-300 ${
                              isInspectionRunning && index === currentInspectionIndex
                                ? 'bg-blue-600/80 font-medium'
                                : 'bg-black/70'
                            }`}>
                              {visionData?.name}
                              {isInspectionRunning && index === currentInspectionIndex && (
                                <div className="text-blue-300 text-xs mt-1">검사중...</div>
                              )}
                            </div>

                            {/* Inspection Number */}
                            <div className={`absolute -top-3 -left-3 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                              index === currentInspectionIndex
                                ? 'bg-blue-500 text-white scale-110'
                                : index < currentInspectionIndex
                                ? 'bg-green-500 text-white'
                                : 'bg-gray-500 text-gray-300'
                            }`}>
                              {index + 1}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {/* Exit Zone - PCB들이 사라지는 영역 */}
                    <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-gray-900/80 to-transparent pointer-events-none"></div>
                    
                    {/* Entry Zone - PCB들이 들어오는 영역 */}
                    <div className="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-gray-900/80 to-transparent pointer-events-none"></div>
                  </div>
                </div>

                {/* Inspection Progress Bar */}
                {isInspectionRunning && (
                  <div className="mt-4">
                    <div className="flex justify-between text-sm text-gray-400 mb-2">
                      <span>검사 진행률</span>
                      <span>{Math.round(((currentInspectionIndex + 1) / (Array.isArray(visionData?.urls) ? visionData.urls.length : 1)) * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full transition-all duration-1000"
                        style={{ width: `${((currentInspectionIndex + 1) / (Array.isArray(visionData?.urls) ? visionData.urls.length : 1)) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Real-time Inspection Monitor */}
        <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-green-400" />
                실시간 검사 결과
              </CardTitle>
              
              {/* Reset Button */}
              {Array.isArray(inspectionResults) && inspectionResults.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  className="bg-blue-500/20 border-blue-500/30 text-blue-300 hover:text-blue-200 hover:bg-blue-500/30 transition-all duration-200"
                  onClick={() => setInspectionResults([])}
                >
                  <X className="w-4 h-4 mr-1" />
                  RESET
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {Array.isArray(inspectionResults) && inspectionResults.length > 0 ? (
              <div className="flex flex-col h-96">
                {/* 검사 결과 목록 - 더 많은 공간 할당 */}
                <div className="flex-1 overflow-y-auto space-y-3 pr-2 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-[#161B22] [&::-webkit-scrollbar-thumb]:bg-blue-500/60 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-blue-400/80 [&::-webkit-scrollbar-thumb]:transition-all [&::-webkit-scrollbar-thumb]:duration-300">
                  {inspectionResults.map((result, index) => (
                    <div
                      key={result.timestamp || index}
                      className={`bg-[#0D1117]/50 rounded-lg p-3 border ${
                        result.status === '합격' 
                          ? 'border-green-500/30' 
                          : 'border-red-500/30'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium text-sm">PCB{result.pcb_id}</span>
                          <span className="text-gray-400 text-xs">({result.name})</span>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs font-medium ${
                          result.status === '합격'
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}>
                          {result.status === '합격' ? '합격' : '불합격'}
                        </div>
                      </div>
                      
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-400">불량 개수:</span>
                          <span className="text-white">{result.defect_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">AI 신뢰도:</span>
                          <span className="text-white">{(result.confidence * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">검사 시간:</span>
                          <span className="text-white">{result.inspectionTime}초</span>
                        </div>
                        {result.defects && result.defects.length > 0 && (
                          <div className="mt-2">
                            <span className="text-gray-400">불량 유형:</span>
                            <div className="mt-1 space-y-1">
                              {result.defects.map((defect: any, idx: number) => (
                                <div key={idx} className="text-red-400 text-xs">
                                  • {defect.label} (신뢰도: {(defect.score * 100).toFixed(1)}%)
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-[#0D1117]/50 rounded-lg p-4 border border-gray-500/30">
                <div className="text-center text-gray-400">
                  <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">검사 결과가 여기에 표시됩니다</p>
                </div>
              </div>
            )}
            
            {/* Summary Stats - 아래쪽에 위치 */}
            {Array.isArray(inspectionResults) && inspectionResults.length > 0 && (
              <div className="pt-3 border-t border-[#30363D] mt-4">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-400">총 검사:</span>
                    <span className="text-white">{Array.isArray(inspectionResults) ? inspectionResults.length : 0}개</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">합격:</span>
                    <span className="text-green-400">
                      {Array.isArray(inspectionResults) ? inspectionResults.filter(r => r.status === '합격').length : 0}개
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">불합격:</span>
                    <span className="text-red-400">
                      {Array.isArray(inspectionResults) ? inspectionResults.filter(r => r.status === '불합격').length : 0}개
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">불량률:</span>
                    <span className="text-red-400">
                      {Array.isArray(inspectionResults) && inspectionResults.length > 0 ? Math.round((inspectionResults.filter(r => r.status === '불합격').length / inspectionResults.length) * 100) : 0}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 불량 검사 예약 모달 */}
      <Dialog open={showReservationModal} onOpenChange={setShowReservationModal}>
        <DialogContent className="bg-[#161B22]/80 backdrop-blur-xl border-[#30363D] shadow-2xl">
          <DialogHeader>
            <DialogTitle className="text-white">불량 검사 예약</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-[#0D1117]/50 rounded-lg p-4 border border-[#30363D]">
              <p className="text-white mb-2">선택된 PCB: {selectedPcb?.name}</p>
              <p className="text-gray-400 text-sm">ID: PCB{selectedPcb?.pcb_id}</p>
            </div>
              <div>
               <label className="text-white block mb-2">검사 날짜 및 시간</label>
                <Input
                  type="datetime-local"
                  value={inspectionDate}
                  onChange={(e) => setInspectionDate(e.target.value)}
                  className="bg-[#0D1117]/50 backdrop-blur-sm border-[#30363D] text-white [&::-webkit-calendar-picker-indicator]:invert [&::-webkit-calendar-picker-indicator]:cursor-pointer"
                  required
                />
             </div>
            <div>
              <label className="text-white block mb-2">검사 유형</label>
              <select 
                value={inspectionType}
                onChange={(e) => setInspectionType(e.target.value)}
                className="w-full bg-[#0D1117]/50 backdrop-blur-sm border border-[#30363D] text-white rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="incoming">입고검사</option>
                <option value="pre-input">투입전 검사</option>
              </select>
            </div>
            <div>
              <label className="text-white block mb-2">검사 방법</label>
              <select 
                value={inspectionMethod}
                onChange={(e) => setInspectionMethod(e.target.value)}
                className="w-full bg-[#0D1117]/50 backdrop-blur-sm border border-[#30363D] text-white rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="full">전수검사</option>
                <option value="sample">샘플검사</option>
              </select>
            </div>
                         <div className="flex gap-3 pt-4">
               <Button
                 onClick={handleReservationComplete}
                 className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-lg"
                 disabled={!inspectionDate}
               >
                 예약 완료
               </Button>
               <Button
                 onClick={() => setShowReservationModal(false)}
                 variant="outline"
                 className="flex-1 border-blue-500/30 text-blue-400 hover:bg-blue-600/10 bg-transparent"
               >
                 취소
               </Button>
             </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 검사 일정 캘린더 모달 */}
      <Dialog open={showCalendarModal} onOpenChange={setShowCalendarModal}>
        <DialogContent className="bg-[#161B22]/80 backdrop-blur-xl border-[#30363D] shadow-2xl max-w-7xl max-h-[95vh] overflow-hidden">
          <DialogHeader className="relative">
            <DialogTitle className="text-white flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-400" />
              검사 일정 관리
            </DialogTitle>
            <Button
              onClick={() => setShowCalendarModal(false)}
              variant="ghost"
              size="sm"
              className="absolute top-0 right-0 text-gray-400 hover:text-white hover:bg-gray-700/50 p-2"
            >
              ✕
            </Button>
          </DialogHeader>
          
          <div className="grid gap-6 h-full overflow-hidden" style={{gridTemplateColumns: '65% 35%'}}>
            {/* 왼쪽: 캘린더 */}
            <div className="space-y-4">
              {/* 캘린더 헤더 */}
              <div className="flex items-center justify-between">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToPreviousMonth}
                  className="border-blue-500/30 text-blue-400 hover:bg-blue-600/10 bg-transparent"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <h2 className="text-xl font-semibold text-white">
                  {formatDate(currentDate)}
                </h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToNextMonth}
                  className="border-blue-500/30 text-blue-400 hover:bg-blue-600/10 bg-transparent"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>

              {/* 캘린더 그리드 */}
              <div className="bg-[#0D1117]/50 rounded-lg p-4 border border-[#30363D]">
              {/* 요일 헤더 */}
              <div className="grid grid-cols-7 gap-1 mb-2">
                {['일', '월', '화', '수', '목', '금', '토'].map((day) => (
                  <div key={day} className="text-center text-sm font-medium text-gray-400 py-2">
                    {day}
                  </div>
                ))}
              </div>

              {/* 날짜 그리드 */}
              <div className="grid grid-cols-7 gap-1">
                {(() => {
                  const { daysInMonth, startingDayOfWeek } = getDaysInMonth(currentDate)
                  const days = []
                  
                  // 이전 달의 마지막 날짜들
                  for (let i = 0; i < startingDayOfWeek; i++) {
                    days.push(<div key={`empty-${i}`} className="h-20"></div>)
                  }
                  
                  // 현재 달의 날짜들
                  for (let day = 1; day <= daysInMonth; day++) {
                    const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day)
                    const inspections = getScheduledInspectionsForDate(date)
                    const isCurrentDay = isToday(date)
                    
                    days.push(
                      <div
                        key={day}
                        className={`h-20 border border-[#30363D] rounded-lg p-2 cursor-pointer transition-all duration-200 ${
                          isCurrentDay 
                            ? 'bg-blue-600/20 border-blue-500/50' 
                            : 'bg-[#161B22]/30 hover:bg-[#21262D]/50'
                        }`}
                        onClick={() => handleDateClick(date)}
                      >
                        <div className={`text-sm font-medium ${
                          isCurrentDay ? 'text-blue-400' : 'text-white'
                        }`}>
                          {day}
                        </div>
                        
                        {/* 예약된 검사 일정 표시 */}
                        {inspections.length > 0 && (
                          <div className="mt-1 space-y-1">
                            {inspections.slice(0, 2).map((inspection, index) => (
                              <div
                                key={index}
                                className="text-xs bg-blue-600/30 text-blue-300 px-1 py-0.5 rounded truncate"
                                title={`${inspection.pcbName} - ${inspection.type} - ${inspection.method} (${inspection.count}개)`}
                              >
                                {inspection.pcbName}
                              </div>
                            ))}
                            {inspections.length > 2 && (
                              <div className="text-xs text-gray-400 text-center">
                                +{inspections.length - 2}개 더
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  }
                  
                  return days
                })()}
              </div>
              </div>
            </div>

            {/* 오른쪽: 예약된 검사 일정 목록 */}
            <div className="flex flex-col h-full">
              <div className="bg-[#0D1117]/50 rounded-lg p-4 border border-[#30363D] flex-1 flex flex-col">
                <h3 className="text-white font-medium mb-3">이번 달 예약된 검사 일정</h3>
                {Array.isArray(scheduledInspections) && scheduledInspections.length > 0 ? (
                  <div className="flex-1 overflow-y-auto space-y-2 pr-2 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-[#161B22] [&::-webkit-scrollbar-thumb]:bg-blue-500/60 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-blue-400/80 [&::-webkit-scrollbar-thumb]:transition-all [&::-webkit-scrollbar-thumb]:duration-300">
                    {scheduledInspections.map((inspection, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-[#161B22]/30 rounded-lg border border-[#30363D]">
                        <div className="flex-1 min-w-0">
                          <div className="text-white font-medium truncate">{inspection.pcbName}</div>
                          <div className="text-gray-400 text-sm">
                            {inspection.date} • {inspection.type}
                          </div>
                          <div className="text-gray-400 text-sm">
                            {inspection.method}
                          </div>
                          <div className="text-gray-500 text-xs mt-1">
                            수량: {inspection.count}개 • 이미지: {inspection.urls.length}개
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <div className="flex flex-col items-end gap-1">
                            <Badge variant="outline" className="border-blue-500/30 text-blue-400 text-xs">
                              {inspection.type}
                            </Badge>
                            <Badge variant="outline" className="border-green-500/30 text-green-400 text-xs">
                              {inspection.method}
                            </Badge>
                          </div>
                          <div className="flex flex-col gap-1">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleSelectInspection(inspection)}
                              className={`border-blue-500/30 text-blue-400 hover:bg-blue-600/10 bg-transparent px-2 py-1 h-8 ${
                                selectedInspection?.id === inspection.id ? 'bg-blue-600/20 border-blue-400' : ''
                              }`}
                              title="검사 대상 선택"
                            >
                              <Check className="w-3 h-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteInspection(inspection.id)}
                              className="border-red-500/30 text-red-400 hover:bg-red-600/10 bg-transparent px-2 py-1 h-8"
                              title="검사 일정 삭제"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center">
                    <div className="text-center text-gray-400">
                      <Calendar className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>예약된 검사 일정이 없습니다.</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Menu2
