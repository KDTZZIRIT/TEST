"use client"

import type { FC } from "react"
import { AlertTriangle, CheckCircle2, Clock, Factory, XCircle, Calendar, FileText, BarChart3, Target, Activity, Cpu, Package, Eye, Settings, LayoutDashboard, CircuitBoard, CalendarCheck, AlignJustify } from 'lucide-react'

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { useInspectionStore } from "@/stores/inspectionStore"
import pcbStore from "@/stores/pcbStore"
import { useEffect, useState } from "react"




// --- Components ---

const PCBDetailTable: FC = () => {
  const { scheduledInspections, inspectionHistory } = pcbStore()
  
  // 더미 데이터
  const dummyPCBData = [
    {
      name: "SM-S901A",
      size: "60×40",
      material: "FR-4",
      smtDensity: "Low",
      boardArea: "2400"
    },
    {
      name: "SM-G992N",
      size: "80×60", 
      material: "FR-4",
      smtDensity: "Medium",
      boardArea: "4800"
    },
    {
      name: "LM-G820K",
      size: "100×70",
      material: "CEM-3",
      smtDensity: "Medium", 
      boardArea: "7000"
    },
    {
      name: "XT2315-2",
      size: "120×80",
      material: "Aluminum",
      smtDensity: "Medium",
      boardArea: "9600"
    },
    {
      name: "CPH2341",
      size: "100×100",
      material: "FR-4",
      smtDensity: "Medium~High",
      boardArea: "10000"
    },
    {
      name: "CPH2451",
      size: "130×90",
      material: "Aluminum",
      smtDensity: "High",
      boardArea: "11700"
    },
    {
      name: "V2312DA",
      size: "150×100",
      material: "Ceramic",
      smtDensity: "Ultra-High",
      boardArea: "15000"
    },
    {
      name: "Pixel-8Pro",
      size: "140×90",
      material: "FR-4",
      smtDensity: "Ultra-High",
      boardArea: "12600"
    },
    {
      name: "XQ-AT52",
      size: "80×50",
      material: "CEM-1",
      smtDensity: "Low",
      boardArea: "4000"
    },
    {
      name: "A3101",
      size: "60×60",
      material: "FR-4",
      smtDensity: "Medium",
      boardArea: "3600"
    }
  ]
  
  // 실제 데이터와 더미 데이터 결합
  const pcbDetailData = [
    ...dummyPCBData,
    // 예약된 검사 데이터
    ...(Array.isArray(scheduledInspections) ? scheduledInspections.map((item: any) => ({
      name: item.pcbName || 'Unknown',
      size: "60mm × 40mm", // 기본값
      material: "FR-4", // 기본값
      smtDensity: "중밀도", // 기본값
      boardArea: "24cm²" // 기본값
    })) : []),
    // 완료된 검사 데이터
    ...(Array.isArray(inspectionHistory) ? inspectionHistory.map((item: any) => ({
      name: item.pcbName || 'Unknown',
      size: "60mm × 40mm", // 기본값
      material: "FR-4", // 기본값
      smtDensity: "중밀도", // 기본값
      boardArea: "24cm²" // 기본값
    })) : [])
  ]
  
  // 중복 제거 및 정렬
  const uniquePCBs = pcbDetailData.reduce((acc: any[], current: any) => {
    const existing = acc.find(item => item.name === current.name)
    if (!existing) {
      acc.push(current)
    }
    return acc
  }, [])

  return (
    <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <AlignJustify className="w-5 h-5 text-purple-400" />
          PCB 리스트
        </CardTitle>
      </CardHeader>
      <CardContent>
        {uniquePCBs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-[#30363D]">
                <tr>
                  <th className="text-center p-3 text-gray-300 font-medium cursor-pointer hover:text-white transition-colors">
                    PCB
                  </th>
                  <th className="text-center p-3 text-gray-300 font-medium cursor-pointer hover:text-white transition-colors">
                    사이즈(mm)
                  </th>
                  <th className="text-center p-3 text-gray-300 font-medium cursor-pointer hover:text-white transition-colors">
                    재질
                  </th>
                  <th className="text-center p-3 text-gray-300 font-medium cursor-pointer hover:text-white transition-colors">
                    SMT 밀도
                  </th>
                  <th className="text-center p-3 text-gray-300 font-medium cursor-pointer hover:text-white transition-colors">
                    기판면적(mm²)
                  </th>
                  <th className="text-center p-3 text-gray-300 font-medium">
                    재고
                  </th>
                </tr>
              </thead>
              <tbody>
                {uniquePCBs.map((pcb: any, index: number) => (
                  <tr 
                    key={index} 
                    className="border-b border-[#30363D]/50 hover:bg-[#21262D]/30 transition-colors"
                  >
                    <td className="p-3 text-white font-medium text-center">{pcb.name}</td>
                    <td className="p-3 text-gray-300 text-center">{pcb.size}</td>
                    <td className="p-3 text-center">
                      <Badge 
                        className={`${
                          pcb.material === 'FR-4' ? 'bg-blue-500' : 
                          pcb.material === 'CEM-3' ? 'bg-green-500' :
                          pcb.material === 'CEM-1' ? 'bg-yellow-500' :
                          pcb.material === 'Aluminum' ? 'bg-gray-500' :
                          pcb.material === 'Ceramic' ? 'bg-purple-500' :
                          'bg-orange-500'
                        }/20 border-none text-xs`}
                        style={{
                          color: pcb.material === 'FR-4' ? '#60a5fa' : 
                                 pcb.material === 'CEM-3' ? '#4ade80' :
                                 pcb.material === 'CEM-1' ? '#facc15' :
                                 pcb.material === 'Aluminum' ? '#9ca3af' :
                                 pcb.material === 'Ceramic' ? '#a855f7' :
                                 '#fb923c'
                        }}
                      >
                        {pcb.material}
                      </Badge>
                    </td>
                    <td className="p-3 text-center">
                      <Badge 
                        className={`${
                          pcb.smtDensity.includes('Ultra-High') ? 'bg-red-600' :
                          pcb.smtDensity.includes('High') ? 'bg-red-500' : 
                          pcb.smtDensity.includes('Medium') ? 'bg-yellow-500' : 
                          'bg-green-500'
                        }/20 border-none text-xs`}
                        style={{
                          color: pcb.smtDensity.includes('Ultra-High') ? '#dc2626' :
                                 pcb.smtDensity.includes('High') ? '#f87171' :
                                 pcb.smtDensity.includes('Medium') ? '#facc15' : 
                                 '#4ade80'
                        }}
                      >
                        {pcb.smtDensity}
                      </Badge>
                    </td>
                    <td className="p-3 text-gray-300 font-mono text-sm text-center">{pcb.boardArea}</td>
                    <td className="p-3 text-center">
                      <span className="text-white font-medium">1</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
              <LayoutDashboard className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-gray-400 text-lg">등록된 PCB가 없습니다.</p>
            <p className="text-gray-500 text-sm mt-1">검사를 예약하거나 완료하면 여기에 표시됩니다.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

const InspectionProgressCard: FC = () => {
  const { inspectionProgress } = useInspectionStore()
  const [currentTime, setCurrentTime] = useState(new Date())
  
  // pcbStore에서 실시간 검사 결과를 가져와서 불량률 계산
  const { inspectionResults, inspectionHistory } = pcbStore()
  
  // 실시간 불량률 계산
  const realTimeDefectRate = Array.isArray(inspectionResults) && inspectionResults.length > 0 
    ? Math.round((inspectionResults.filter(r => r.status === 'defective' || r.status === '불합격').length / inspectionResults.length) * 100 * 10) / 10
    : 0
  
  // 실시간 시간 업데이트
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    
    return () => clearInterval(timer)
  }, [])

  // Zustand store에서 예약된 검사 데이터 가져오기
  const { scheduledInspections } = pcbStore()

  // 모든 예약된 검사를 날짜순으로 정렬
  const allInspections = Array.isArray(scheduledInspections) ? scheduledInspections.sort((a, b) => {
    const dateA = new Date(a.date)
    const dateB = new Date(b.date)
    return dateA.getTime() - dateB.getTime()
  }) : []

  // 날짜별로 그룹화
  const groupedInspections = allInspections.reduce((groups, inspection) => {
    const date = new Date(inspection.date).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(inspection)
    return groups
  }, {} as Record<string, any[]>)

  return (
    <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <CalendarCheck className="w-5 h-5 text-green-400" />
          {inspectionProgress.isRunning ? '불량검사 진행률' : '예약된 검사 일정'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {inspectionProgress.isRunning ? (
          <div className="space-y-4">
            {/* PCB 이름 */}
            {inspectionProgress.pcbName && (
              <div className="text-sm text-gray-300">
                <p className="font-medium text-white">검사 중인 기판 : {inspectionProgress.pcbName}</p>
              </div>
            )}
            
            {/* 진행률 바 */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-400">
                <span>검사 진행률</span>
                <span>{Math.round(inspectionProgress.progress)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-1000"
                  style={{ width: `${inspectionProgress.progress}%` }}
                />
              </div>
            </div>
            
            {/* 실시간 불량률 */}
            <div className="text-sm text-gray-300">
              <p>실시간 불량률: <span className="text-red-400 font-medium">{realTimeDefectRate}%</span></p>
            </div>
            
            {/* 현재 단계 정보 */}
            <div className="text-sm text-gray-300">
              <p>진행 상태: {inspectionProgress.currentStep} / {inspectionProgress.totalSteps}</p>
              <p>상태: {inspectionProgress.status}</p>
              {inspectionProgress.message && (
                <p className="text-blue-400 mt-1">{inspectionProgress.message}</p>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
                          {/* 예약된 검사 카드 목록 */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-gray-300">예약된 검사</h4>
                {Object.entries(groupedInspections).length > 0 ? (
                  <div className="overflow-x-auto [&::-webkit-scrollbar]:h-2 [&::-webkit-scrollbar-track]:bg-[#161B22] [&::-webkit-scrollbar-thumb]:bg-blue-500/60 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-blue-400/80 [&::-webkit-scrollbar-thumb]:transition-all [&::-webkit-scrollbar-thumb]:duration-300">
                    <div className="flex gap-4 pb-2" style={{ width: "max-content" }}>
                      {Object.entries(groupedInspections).map(([date, inspections]) => (
                        <div key={date} className="bg-gray-800/20 border border-gray-700 rounded-lg p-3 min-w-64">
                          <h5 className="text-white font-medium text-sm mb-2">{date}</h5>
                          <div className="space-y-2">
                            {(inspections as any[]).map((inspection: any, index: number) => (
                              <Card 
                                key={inspection.id} 
                                className="bg-[#0D1117]/50 border-[#30363D] hover:border-blue-500/50 transition-all duration-300 cursor-pointer"
                              >
                                <CardContent className="p-3">
                                  <div className="space-y-2">
                                    {/* 기판 종류 */}
                                    <div className="flex items-center gap-2">
                                      <h6 className="text-white font-medium text-sm">{inspection.pcbName}</h6>
                                      <Badge className="text-sm bg-blue-500/20 text-blue-400 border-blue-500/30">
                                        {inspection.type}
                                      </Badge>
                                    </div>
                                    
                                    {/* 기판 정보 */}
                                    <div className="space-y-1 text-sm">
                                      <div className="flex justify-between">
                                        <span className="text-gray-400">개수:</span>
                                        <span className="text-white font-medium">{inspection.count}개</span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-gray-400">검사:</span>
                                        <span className="text-green-400 font-medium">{inspection.method}</span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-gray-400">이미지:</span>
                                        <span className="text-gray-300">{inspection.urls.length}개</span>
                                      </div>
                                    </div>
                                  </div>
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-12 h-12 bg-gray-700/50 rounded-full flex items-center justify-center mx-auto mb-3">
                    <Calendar className="w-6 h-6 text-gray-400" />
                  </div>
                  <p className="text-gray-400 text-sm">예약된 검사가 없습니다.</p>
                </div>
              )}
            </div>

            {/* 통계 정보 */}
            {allInspections.length > 0 && (
              <div className="pt-3 border-t border-[#30363D] mt-4">
                <div className="grid grid-cols-3 gap-4 text-xs">
                  <div className="text-center">
                    <p className="text-white font-bold">{allInspections.length}</p>
                    <p className="text-gray-400">총 예약</p>
                  </div>
                  <div className="text-center">
                    <p className="text-blue-400 font-bold">
                      {allInspections.filter(i => i.type === '입고검사').length}
                    </p>
                    <p className="text-gray-400">입고검사</p>
                  </div>
                  <div className="text-center">
                    <p className="text-white font-bold">
                      {allInspections.reduce((total, inspection) => total + inspection.count, 0)}
                    </p>
                    <p className="text-gray-400">총 개수</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

const InspectionResultsCard: FC = () => {
  const [showModal, setShowModal] = useState(false)
  const [selectedInspectionId, setSelectedInspectionId] = useState<string | null>(null)
  const { inspectionHistory } = pcbStore()
  
  // 최근 검사 이력 (최대 3개)
  const recentInspections = Array.isArray(inspectionHistory) ? inspectionHistory.slice(0, 3) : []
  
  // 마지막 1번의 검사 결과만 가져오기
  const lastInspection = Array.isArray(inspectionHistory) && inspectionHistory.length > 0 
    ? inspectionHistory[0] 
    : null
  
  // 마지막 검사의 통계 계산
  const lastInspectionStats = lastInspection 
    ? {
        totalPassed: lastInspection.passedCount || 0,
        totalDefective: lastInspection.defectiveCount || 0,
        totalInspected: lastInspection.totalInspected || 0
      }
    : { totalPassed: 0, totalDefective: 0, totalInspected: 0 }
  
  const lastInspectionDefectRate = lastInspectionStats.totalInspected > 0 
    ? Math.round((lastInspectionStats.totalDefective / lastInspectionStats.totalInspected) * 100 * 10) / 10 
    : 0
  
  // 마지막 검사에서 불량 유형별 통계 계산
  const lastInspectionDefectTypeStats = lastInspection && Array.isArray(lastInspection.results)
    ? lastInspection.results.reduce((acc: Record<string, number>, result: any) => {
        if (Array.isArray(result.defects)) {
          result.defects.forEach((defect: any) => {
            const type = defect.label || 'Unknown'
            acc[type] = (acc[type] || 0) + 1
          })
        }
        return acc
      }, {} as Record<string, number>)
    : {}
    
  // 마지막 검사의 불량 유형별 데이터 배열로 변환
  const lastInspectionDefectTypesArray = Object.entries(lastInspectionDefectTypeStats)
    .map(([type, count]) => ({ type, count: count as number }))
    .sort((a, b) => b.count - a.count) // 개수 순으로 정렬
    
  const lastInspectionTotalDefects = Object.values(lastInspectionDefectTypeStats).reduce((sum: number, count) => sum + (count as number), 0)
  
  // 마지막 검사의 불량 유형별 퍼센테이지와 색상 계산
  const lastInspectionDefectTypesWithPercentage = lastInspectionDefectTypesArray.map((item, index) => ({
    ...item,
    percentage: lastInspectionTotalDefects > 0 ? Math.round((item.count / lastInspectionTotalDefects) * 100 * 10) / 10 : 0,
    color: [
      "bg-red-500", "bg-orange-500", "bg-yellow-500", 
      "bg-pink-500", "bg-purple-500", "bg-blue-500"
    ][index % 6] // 색상 순환
  }))

  // 모달에서 표시할 선택된 검사 데이터
  const selectedInspection = selectedInspectionId 
    ? inspectionHistory.find(inspection => inspection.id === selectedInspectionId)
    : null
  
  // 선택된 검사의 통계 계산
  const selectedInspectionStats = selectedInspection 
    ? {
        totalPassed: selectedInspection.passedCount || 0,
        totalDefective: selectedInspection.defectiveCount || 0,
        totalInspected: selectedInspection.totalInspected || 0
      }
    : { totalPassed: 0, totalDefective: 0, totalInspected: 0 }
  
  const selectedInspectionDefectRate = selectedInspectionStats.totalInspected > 0 
    ? Math.round((selectedInspectionStats.totalDefective / selectedInspectionStats.totalInspected) * 100 * 10) / 10 
    : 0
  
  // 선택된 검사의 불량 유형별 통계 계산
  const selectedInspectionDefectTypeStats = selectedInspection && Array.isArray(selectedInspection.results)
    ? selectedInspection.results.reduce((acc: Record<string, number>, result: any) => {
        if (Array.isArray(result.defects)) {
          result.defects.forEach((defect: any) => {
            const type = defect.label || 'Unknown'
            acc[type] = (acc[type] || 0) + 1
          })
        }
        return acc
      }, {} as Record<string, number>)
    : {}
    
  // 선택된 검사의 불량 유형별 데이터 배열로 변환
  const selectedInspectionDefectTypesArray = Object.entries(selectedInspectionDefectTypeStats)
    .map(([type, count]) => ({ type, count: count as number }))
    .sort((a, b) => b.count - a.count) // 개수 순으로 정렬
    
  const selectedInspectionTotalDefects = Object.values(selectedInspectionDefectTypeStats).reduce((sum: number, count) => sum + (count as number), 0)
  
  // 선택된 검사의 불량 유형별 퍼센테이지와 색상 계산
  const selectedInspectionDefectTypesWithPercentage = selectedInspectionDefectTypesArray.map((item, index) => ({
    ...item,
    percentage: selectedInspectionTotalDefects > 0 ? Math.round((item.count / selectedInspectionTotalDefects) * 100 * 10) / 10 : 0,
    color: [
      "bg-red-500", "bg-orange-500", "bg-yellow-500", 
      "bg-pink-500", "bg-purple-500", "bg-blue-500"
    ][index % 6] // 색상 순환
  }))
  
  return (
    <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-green-400" />
          최근 검사 결과{lastInspection ? ` ( ${lastInspection.pcbName} )` : ''}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* 마지막 검사 요약 통계 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-4 h-4 text-green-400" />
                <span className="text-green-200 text-sm font-medium">합격</span>
              </div>
              <p className="text-green-100 text-2xl font-bold text-right">{lastInspectionStats.totalPassed}</p>
            </div>

            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-3">
                <XCircle className="w-4 h-4 text-red-400" />
                <span className="text-red-200 text-sm font-medium">불합격</span>
              </div>
              <p className="text-red-100 text-2xl font-bold text-right">{lastInspectionStats.totalDefective}</p>
            </div>

            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4 text-blue-400" />
                <span className="text-blue-200 text-sm font-medium">불량률</span>
              </div>
              <p className="text-blue-100 text-2xl font-bold text-right">{lastInspectionDefectRate}%</p>
            </div>

            <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-purple-400" />
                <span className="text-purple-200 text-sm font-medium">처리량</span>
              </div>
              <p className="text-purple-100 text-2xl font-bold text-right">{lastInspectionStats.totalInspected}</p>
            </div>
          </div>

          {/* 불량 유형 분석 */}
          <div className="bg-[#0D1117]/50 border border-[#30363D] rounded-lg p-4">
            <h4 className="text-white font-medium mb-3 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-yellow-400" />
              주요 불량 유형
            </h4>
            <div className="space-y-3">
              {lastInspectionDefectTypesWithPercentage.length > 0 ? lastInspectionDefectTypesWithPercentage.map((defect, index) => (
                <div key={defect.type} className="space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300 text-sm">{defect.type}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium text-sm">{Number(defect.count)}건</span>
                      <span className="text-gray-400 text-xs">({defect.percentage}%)</span>
                    </div>
                  </div>
                  <div className="w-full bg-[#30363D] rounded-full h-2">
                    <div
                      className={`${defect.color} h-2 rounded-full transition-all duration-700`}
                      style={{ width: `${defect.percentage}%` }}
                    />
                  </div>
                </div>
              )) : (
                <div className="text-center text-gray-400 py-4">
                  <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">불량 데이터가 없습니다.</p>
                </div>
              )}
            </div>
          </div>

          {/* 최근 검사 이력 */}
          <div className="bg-[#0D1117]/50 border border-[#30363D] rounded-lg p-4">
            <h4 className="text-white font-medium mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-400" />
              최근 검사 이력
            </h4>
            <div className="space-y-2">
              {recentInspections.length > 0 ? recentInspections.map((inspection, index) => (
                <div 
                  key={inspection.id} 
                  className="flex items-center justify-between p-2 bg-[#161B22]/50 rounded border border-[#30363D]/50 hover:border-[#40464D] transition-colors cursor-pointer"
                  onClick={() => {
                    setSelectedInspectionId(inspection.id)
                    setShowModal(true)
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      inspection.defectiveCount <= 40 ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <div>
                      <p className="text-white font-medium text-sm">{inspection.pcbName}</p>
                      <p className="text-gray-400 text-xs">
                        불량: {inspection.defectiveCount}개 | 검사시간: {inspection.inspectionTime}초
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge className={`text-xs ${
                      inspection.defectiveCount <= 40
                        ? 'bg-green-500/20 text-green-400 border-green-500/30'
                        : 'bg-red-500/20 text-red-400 border-red-500/30'
                    }`}>
                      {inspection.defectiveCount <= 40 ? '합격' : '불합격'}
                    </Badge>
                    <p className="text-gray-400 text-xs mt-1">
                      {new Date(inspection.completedAt).toLocaleTimeString('ko-KR', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </p>
                  </div>
                </div>
              )) : (
                <div className="text-center text-gray-400 py-4">
                  <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">아직 완료된 검사가 없습니다.</p>
                </div>
              )}
            </div>
          </div>


        </div>
      </CardContent>

      {/* 검사 결과 상세 모달 */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="bg-[#161B22]/95 backdrop-blur-xl border-[#30363D] shadow-2xl max-w-4xl">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-green-400" />
              {selectedInspection ? `${selectedInspection.pcbName} 검사 결과` : '검사 결과'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* 선택된 검사 요약 통계 */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="w-5 h-5 text-green-400" />
                  <span className="text-green-200 text-sm font-medium">합격</span>
                </div>
                <p className="text-green-100 text-2xl font-bold">{selectedInspectionStats.totalPassed}</p>
                <p className="text-green-300 text-sm">
                  전체 대비 {selectedInspectionStats.totalInspected > 0 ? Math.round((selectedInspectionStats.totalPassed / selectedInspectionStats.totalInspected) * 100) : 0}%
                </p>
              </div>

              <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <XCircle className="w-5 h-5 text-red-400" />
                  <span className="text-red-200 text-sm font-medium">불합격</span>
                </div>
                <p className="text-red-100 text-2xl font-bold">{selectedInspectionStats.totalDefective}</p>
                <p className="text-red-300 text-sm">전체 대비 {selectedInspectionDefectRate}%</p>
              </div>

              <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-5 h-5 text-blue-400" />
                  <span className="text-blue-200 text-sm font-medium">불량률</span>
                </div>
                <p className="text-blue-100 text-2xl font-bold">{selectedInspectionDefectRate}%</p>
                <p className="text-blue-300 text-sm">이 검사</p>
              </div>

              <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-5 h-5 text-purple-400" />
                  <span className="text-purple-200 text-sm font-medium">처리량</span>
                </div>
                <p className="text-purple-100 text-2xl font-bold">{selectedInspectionStats.totalInspected}</p>
                <p className="text-purple-300 text-sm">검사 완료</p>
              </div>
            </div>

            {/* 불량 유형 분석 */}
            <div className="bg-[#0D1117]/50 border border-[#30363D] rounded-lg p-6">
              <h4 className="text-white font-medium mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-yellow-400" />
                주요 불량 유형
              </h4>
              <div className="space-y-4">
                {selectedInspectionDefectTypesWithPercentage.length > 0 ? selectedInspectionDefectTypesWithPercentage.map((defect, index) => (
                  <div key={defect.type} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300 font-medium">{defect.type}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-white font-bold">{Number(defect.count)}건</span>
                        <span className="text-gray-400">({defect.percentage}%)</span>
                      </div>
                    </div>
                    <div className="w-full bg-[#30363D] rounded-full h-3">
                      <div
                        className={`${defect.color} h-3 rounded-full transition-all duration-700`}
                        style={{ width: `${defect.percentage}%` }}
                      />
                    </div>
                  </div>
                )) : (
                  <div className="text-center text-gray-400 py-8">
                    <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">이 검사에서 불량 데이터가 없습니다.</p>
                  </div>
                )}
              </div>
            </div>

            {/* 모달 닫기 버튼 */}
            <div className="flex justify-end pt-4">
              <Button
                onClick={() => setShowModal(false)}
                className="bg-[#0D1117] hover:bg-[#21262D] text-white border border-[#30363D] font-medium"
              >
                닫기
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  )
}

// --- Main Dashboard Component ---

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 flex items-center justify-center">
            <CircuitBoard className="w-8 h-8 text-green-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">PCB 대시보드</h1>
          </div>
        </div>
      </div>
      {/* 불량검사 진행률 */}
      <InspectionProgressCard />
      
      {/* 검사 결과 */}
      <InspectionResultsCard />
      
      {/* PCB 상세 목록 */}
      <PCBDetailTable />
    </div>
  )
}