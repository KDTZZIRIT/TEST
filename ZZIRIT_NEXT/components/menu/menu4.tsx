"use client"

import React, { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Package,
  RefreshCw,
  Brain,
  TrendingUp,
  AlertTriangle,
  BarChart3,
  Zap,
  Bot,
  Send,
  Minus,
  ChevronDown,
  ChevronUp,
} from "lucide-react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

// Main4AI 컴포넌트 임포트
import Main4AI from "@/components/menu4AI/Main"

import type { FC } from "react"

// --- Data Types ---
interface CategoryStats {
  category: string
  normal: number
  lowStock: number
  moistureSensitive: number
  total: number
}

// 재고 아이템 인터페이스
interface InventoryItem {
  id: string
  partId: string
  product: string
  type: string
  size: string
  receivedDate: string
  moistureAbsorption: boolean
  moistureMaterials: string
  actionRequired: "-" | "필요"
  manufacturer: string
  quantity: number
  minimumStock: number
  defectCount: number
  unitCost: number
  orderRequired: string
}

// --- Components ---
const CategoryPieChart: FC<{ 
  categoryStats: CategoryStats
}> = ({ categoryStats }) => {
  const router = useRouter()
  
  const handlePieChartClick = () => {
    // inventory 페이지로 이동하면서 카테고리 정보를 URL 파라미터로 전달
    router.push(`/inventory?category=${encodeURIComponent(categoryStats.category)}`)
  }
  const { category, normal, lowStock, moistureSensitive, total } = categoryStats
  
  if (total === 0) {
    return (
      <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
        <CardContent className="p-4 text-center">
          <h3 className="text-white font-bold text-sm mb-2">{category}</h3>
          <div className="text-gray-400 text-xs">No parts available</div>
        </CardContent>
      </Card>
    )
  }
  
  const radius = 60
  const centerX = 70
  const centerY = 70
  let currentAngle = 0
  
  const createSlice = (count: number, status: string, color: string) => {
    if (count === 0) return null
    
    const percentage = count / total
    const angle = percentage * 360
    const startAngle = currentAngle
    const endAngle = currentAngle + angle
    
    const startAngleRad = (startAngle * Math.PI) / 180
    const endAngleRad = (endAngle * Math.PI) / 180
    
    const x1 = centerX + radius * Math.cos(startAngleRad)
    const y1 = centerY + radius * Math.sin(startAngleRad)
    const x2 = centerX + radius * Math.cos(endAngleRad)
    const y2 = centerY + radius * Math.sin(endAngleRad)
    
    const largeArcFlag = angle > 180 ? 1 : 0
    
    const pathData = [
      `M ${centerX} ${centerY}`,
      `L ${x1} ${y1}`,
      `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
      'Z'
    ].join(' ')
    
    currentAngle += angle
    
    return (
      <path
        key={`${category}-${status}`}
        d={pathData}
        fill={color}
        stroke="#1f2937"
        strokeWidth="1"
        className="transition-all duration-200 hover:opacity-80"
      />
    )
  }
  
  // 전체 원 그리기 (한 항목만 있을 때 사용)
  const createFullCircle = (color: string) => {
    return (
      <circle
        cx={centerX}
        cy={centerY}
        r={radius}
        fill={color}
        stroke="#1f2937"
        strokeWidth="1"
      />
    )
  }
  
  const slices = [
    createSlice(normal, 'Normal', '#10b981'),
    createSlice(lowStock, 'Low Stock', '#ef4444'),
    createSlice(moistureSensitive, 'Moisture Sensitive', '#3b82f6')
  ].filter(Boolean)
  
  // 슬라이스가 있는지 확인 (여러 항목이 있을 때)
  const hasMultipleSlices = slices.length > 1

  return (
    <Card 
      className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl hover:shadow-2xl transition-all duration-300 cursor-pointer hover:scale-105"
      onClick={handlePieChartClick}
    >
      <CardContent className="p-4">
        <h3 className="text-white font-bold text-lg mb-3 text-center">{category}</h3>
        <div className="flex flex-col items-center">
          <svg width="140" height="140" className="mb-3">
            {hasMultipleSlices ? (
              // 여러 항목이 있을 때: 슬라이스로 나눈 파이차트
              <>
                {slices}
                
                {/* Center circle with total count */}
                <circle
                  cx={centerX}
                  cy={centerY}
                  r="25"
                  fill="#161B22"
                  stroke="#30363D"
                  strokeWidth="1"
                />
                <text
                  x={centerX}
                  y={centerY - 2}
                  textAnchor="middle"
                  className="fill-white text-sm font-bold"
                >
                  {total}
                </text>
                <text
                  x={centerX}
                  y={centerY + 10}
                  textAnchor="middle"
                  className="fill-gray-400 text-xs"
                >
                  parts
                </text>
              </>
            ) : (
              // 한 항목만 있을 때: 해당 항목 색으로 전체 원 채우기
              <>
                {createFullCircle(
                  normal > 0 ? '#10b981' :      // 정상만 있으면 초록
                  lowStock > 0 ? '#ef4444' :     // 부족만 있으면 빨강
                  moistureSensitive > 0 ? '#3b82f6' : // 흡습만 있으면 파랑
                  '#10b981' // 기본색 (정상)
                )}
                
                {/* Center circle with total count */}
                <circle
                  cx={centerX}
                  cy={centerY}
                  r="25"
                  fill="#161B22"
                  stroke="#30363D"
                  strokeWidth="1"
                />
                <text
                  x={centerX}
                  y={centerY - 2}
                  textAnchor="middle"
                  className="fill-white text-sm font-bold"
                >
                  {total}
                </text>
                <text
                  x={centerX}
                  y={centerY + 10}
                  textAnchor="middle"
                  className="fill-gray-400 text-xs"
                >
                  parts
                </text>
              </>
            )}
          </svg>
          
          {/* Status indicators - 항상 3개 항목 표시 */}
          <div className="space-y-1 w-full">
            {/* 정상 */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <span className="text-gray-300">정상</span>
              </div>
              <span className="text-white font-bold">{normal}</span>
            </div>
            {/* 부족 */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-red-500 rounded-full" />
                <span className="text-gray-300">부족</span>
              </div>
              <span className="text-white font-bold">{lowStock}</span>
            </div>
            {/* 흡습 */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full" />
                <span className="text-gray-300">흡습</span>
              </div>
              <span className="text-white font-bold">{moistureSensitive}</span>
            </div>
          </div>
    </div>
      </CardContent>
    </Card>
  )
}

const Menu4 = () => {
  const router = useRouter()
  const [inventoryItems, setInventoryItems] = useState<InventoryItem[]>([])
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [showOrderModal, setShowOrderModal] = useState(false)
  const [showChatbotModal, setShowChatbotModal] = useState(false)
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null)
  const [orderData, setOrderData] = useState({
    orderPart: "",
    orderQuantity: "",
    deliveryDate: "",
    amount: ""
  })

  // 예측 모델 관련 상태
  const [isPredicting, setIsPredicting] = useState(false)
  const [showPredictionResult, setShowPredictionResult] = useState(false)

  // 챗봇 관련 상태
  const [chatMessages, setChatMessages] = useState([
    {
      id: '1',
      content: `안녕하세요! 재고 관리 AI 어시스턴트입니다. 🤖

다음과 같은 질문들을 도와드릴 수 있습니다:
• 특정 부품의 재고 현황
• 부족한 재고 알림
• 흡습 관리가 필요한 부품
• 발주 추천 및 최적화

무엇을 도와드릴까요?`,
      isUser: false,
      timestamp: new Date()
    }
  ])
  const [currentMessage, setCurrentMessage] = useState("")
  const [isChatLoading, setIsChatLoading] = useState(false)

  
  // 전체 재고 목록 조회
  const fetchInventoryItems = async () => {
    try {
      const apiUrl = "http://43.201.249.204:5000/api/user"
      const response = await fetch(`${apiUrl}/pcb-parts`)
      const data = await response.json()
      
      if (Array.isArray(data)) {
        // 데이터 구조 검증 및 변환
        const validatedData = data.map(item => {
          const isHumiditySensitive = Boolean(item?.moistureAbsorption || item?.is_humidity_sensitive)
          const needsHumidityControl = Boolean(item?.needs_humidity_control)
          
          // is_humidity_sensitive가 false이고 needs_humidity_control이 true일 때만 '필요'
          const actionRequired: "-" | "필요" = (!isHumiditySensitive && needsHumidityControl) ? "필요" : "-"
          
          // quantity가 min_stock보다 낮으면 '필요'
          const quantity = Number(item?.quantity || 0)
          const minStock = Number(item?.minimumStock || item?.min_stock || 0)
          const orderRequired: "-" | "필요" = quantity < minStock ? "필요" : "-"
          
          return {
            id: item?.id || item?.part_id || "",
            partId: item?.partId || item?.part_id || item?.part_number || "",
            product: item?.product || item?.part_number || "",
            type: item?.type || item?.category || "",
            size: item?.size || "",
            receivedDate: item?.receivedDate || item?.received_date || "",
            moistureAbsorption: isHumiditySensitive,
            moistureMaterials: item?.moistureMaterials || (needsHumidityControl ? "필요" : "불필요"),
            actionRequired: actionRequired,
            manufacturer: item?.manufacturer || "",
            quantity: quantity,
            minimumStock: minStock,
            defectCount: Number(item?.defectCount || 0),
            unitCost: Number(item?.unitCost || 0),
            orderRequired: orderRequired
          }
        })
        setInventoryItems(validatedData)
        console.log("✅ menu4 데이터 변환 완료:", validatedData.length, "개 항목")
      } else {
        console.log("API 응답이 배열이 아님:", data)
        setInventoryItems([])
      }
    } catch (error) {
      console.error('재고 데이터 조회 실패:', error)
      // 에러 시 빈 배열 사용
      setInventoryItems([])
    }
  }

  // 발주요청 버튼 클릭 핸들러 (새로운 모달 열기)
  const handleOrderRequest = (item: InventoryItem) => {
    setSelectedItem(item)
    setOrderData({
      orderPart: item.product,
      orderQuantity: "",
      deliveryDate: "",
      amount: ""
    })
    setShowOrderModal(true)
  }

  // 발주요청 제출 핸들러
  const handleSubmitOrder = () => {
    console.log("발주요청 제출:", orderData)
    // TODO: API 호출 로직 추가
    setShowOrderModal(false)
    setSelectedItem(null)
    setOrderData({
      orderPart: "",
      orderQuantity: "",
      deliveryDate: "",
      amount: ""
    })
  }

  // 예측 모델 실행 핸들러
  const handlePrediction = async () => {
    setIsPredicting(true)
    
    try {
      console.log("🔮 예측 모델 실행 준비...")
      
      // 즉시 결과 표시 (로딩 시간 제거)
      setIsPredicting(false)
      setShowPredictionResult(true)
      
    } catch (error) {
      console.error('예측 모델 실행 오류:', error)
      setIsPredicting(false)
    }
  }

  // 예측 결과 닫기 핸들러
  const handleClosePrediction = () => {
    setShowPredictionResult(false)
  }

  // 챗봇 메시지 전송
  const handleSendChatMessage = async () => {
    if (!currentMessage.trim() || isChatLoading) return

    const userMessage = {
      id: Date.now().toString(),
      content: currentMessage,
      isUser: true,
      timestamp: new Date()
    }

    setChatMessages(prev => [...prev, userMessage])
    setCurrentMessage("")
    setIsChatLoading(true)

    try {
      const apiUrl = "http://localhost:5100"
      const response = await fetch(`${apiUrl}/api/inventory-chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentMessage,
          context: {
            menu: 'inventory',
            timestamp: new Date().toISOString()
          }
        })
      })

      const data = await response.json()

      if (data.success) {
        const aiMessage = {
          id: (Date.now() + 1).toString(),
          content: data.response,
          isUser: false,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, aiMessage])
      } else {
        throw new Error(data.error || '응답을 받을 수 없습니다.')
      }
    } catch (error) {
      console.error('챗봇 메시지 전송 실패:', error)
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        content: '죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        isUser: false,
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsChatLoading(false)
    }
  }

  // 빠른 액션 처리
  const handleQuickAction = async (action: string, question: string) => {
    const userMessage = {
      id: Date.now().toString(),
      content: question,
      isUser: true,
      timestamp: new Date()
    }

    setChatMessages(prev => [...prev, userMessage])
    setIsChatLoading(true)

    try {
      const apiUrl = "http://localhost:5100"
      const response = await fetch(`${apiUrl}/api/quick-actions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action })
      })

      const data = await response.json()

      if (data.success) {
        const aiMessage = {
          id: (Date.now() + 1).toString(),
          content: data.response,
          isUser: false,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, aiMessage])
      }
    } catch (error) {
      console.error('빠른 액션 실패:', error)
    } finally {
      setIsChatLoading(false)
    }
  }

  useEffect(() => {
    fetchInventoryItems()
  }, [])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await fetchInventoryItems()
    } catch (error) {
      console.error('새로고침 실패:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 헤더 & 부품 목록 확인 버튼 */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 flex items-center justify-center">
            <Package className="w-8 h-8 text-orange-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">부품 재고 관리 대시보드</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* 새로고침 버튼 */}
          <Button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-lg text-sm sm:text-base flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? '새로고침 중...' : '새로고침'}
          </Button>
          {/* 부품 목록 확인 버튼 */}
          <Button
            onClick={() => router.push('/inventory')}
            className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white shadow-lg text-sm sm:text-base"
          >
            <Package className="w-4 h-4 mr-2" />
            부품 목록 확인
          </Button>
          {/* 챗봇 버튼 */}
          <Button
            onClick={() => setShowChatbotModal(true)}
            className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-lg text-sm sm:text-base"
          >
            <Bot className="w-4 h-4 mr-2" />
            재고 AI 상담
          </Button>
        </div>
      </div>

      {/* AI 재고 예측 블럭 */}
      <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl transition-all duration-1000 ease-in-out overflow-hidden">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-white flex items-center gap-3">
                <Brain className="w-6 h-6 text-purple-400" />
                AI 재고 예측 시스템
              </CardTitle>
              <p className="text-gray-300 text-sm mt-2">
                머신러닝 모델을 통해 부품 재고 부족을 미리 예측하고 최적의 발주 시점을 제안합니다
              </p>
            </div>
            {showPredictionResult && (
              <Button
                onClick={handleClosePrediction}
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white hover:bg-gray-700/50 h-8 w-8 p-0"
              >
                {showPredictionResult ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 예측 실행 버튼 - 항상 표시 */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <Button
              onClick={handlePrediction}
              disabled={isPredicting}
              className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-lg flex items-center gap-2 min-w-[200px]"
              size="lg"
            >
              <Zap className={`w-5 h-5 ${isPredicting ? 'animate-pulse' : ''}`} />
              {isPredicting ? 'AI 분석 중...' : 'AI 예측 실행'}
            </Button>
            <div className="text-sm text-gray-300">
              <span className="font-medium">분석 대상:</span> {inventoryItems.length}개 부품
            </div>
          </div>

          {/* AI 예측 결과 표시 영역 - Main4AI 컴포넌트 임베드 */}
          <div 
            className={`overflow-hidden transition-all ease-in-out ${
              showPredictionResult 
                ? 'max-h-screen opacity-100' 
                : 'max-h-0 opacity-0'
            }`}
            style={{ transitionDuration: '1000ms' }}
          >
            <div className="space-y-6 pt-4">
              {/* Main4AI 컴포넌트 임베드 */}
              <div className="bg-[#0D1117]/50 border border-[#30363D] rounded-lg p-6">
                <Main4AI />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 파이차트 섹션 - 맨 위에 배치 */}
      <div className="space-y-4">
        {/* 파이차트 그리드 - 정상/부족만 */}
        <div className="space-y-4 mt-8">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {(() => {
              // 실제 데이터에서 고유한 카테고리 추출
              const uniqueCategories = [...new Set(inventoryItems.map(item => item.type).filter(Boolean))]
              
              return uniqueCategories.map((category) => {
                // 해당 카테고리의 실제 데이터 필터링
                const categoryItems = inventoryItems.filter(item => {
                  const itemType = item.type?.toLowerCase().trim()
                  const categoryLower = category.toLowerCase().trim()
                  
                  return itemType === categoryLower || 
                         itemType?.includes(categoryLower) || 
                         categoryLower.includes(itemType)
                })
                
                // 정상과 부족만 계산 (흡습 제외)
                const normal = categoryItems.filter(item => item.quantity >= item.minimumStock).length
                const lowStock = categoryItems.filter(item => item.quantity < item.minimumStock).length
                const total = categoryItems.length
                
                // test2용 CategoryStats (흡습 제외)
                const test2Stats: CategoryStats = {
                  category,
                  normal,
                  lowStock,
                  moistureSensitive: 0, // 흡습 항목 제거
                  total
                }
                
                return (
                  <CategoryPieChart
                    key={`test2-${category}`}
                    categoryStats={test2Stats}
                  />
                )
              })
            })()}
          </div>
        </div>
      </div>

      {/* 새로운 발주요청 모달 - 추천발주와 직접발주 탭 구성 */}
      <Dialog open={showOrderModal} onOpenChange={setShowOrderModal}>
        <DialogContent className="bg-[#161B22]/80 backdrop-blur-xl border-[#30363D] shadow-2xl max-w-[600px] mx-4">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Package className="w-5 h-5 text-orange-400" />
              발주요청 - {selectedItem?.product}
            </DialogTitle>
          </DialogHeader>
          
          <Tabs defaultValue="recommended" className="w-full">
            <TabsList className="grid w-full grid-cols-2 bg-[#0D1117]/50">
              <TabsTrigger 
                value="recommended" 
                className="data-[state=active]:bg-purple-600 data-[state=active]:text-white"
              >
                AI 추천 발주
              </TabsTrigger>
              <TabsTrigger 
                value="manual" 
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
              >
                직접 발주
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="recommended" className="space-y-4 mt-4">
              {/* AI 추천 발주 섹션 */}
              <div className="bg-[#0D1117]/50 border border-purple-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="w-5 h-5 text-purple-400" />
                  <h3 className="text-white font-semibold">AI 추천 사항</h3>
                </div>
                
                <div className="space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-gray-400">추천 수량:</span>
                      <span className="text-white font-bold ml-2">
                        {Math.max(100, (selectedItem?.minimumStock || 0) * 2)}개
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">예상 비용:</span>
                      <span className="text-green-400 font-bold ml-2">
                        ₩{(Math.max(100, (selectedItem?.minimumStock || 0) * 2) * 1000).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-gray-400">추천 발주일:</span>
                      <span className="text-white font-bold ml-2">
                        {new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toLocaleDateString('ko-KR')}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">도착 예정일:</span>
                      <span className="text-blue-400 font-bold ml-2">
                        {new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toLocaleDateString('ko-KR')}
                      </span>
                    </div>
                  </div>
                  
                  <div className="bg-[#161B22]/50 border border-[#30363D] rounded p-3 mt-3">
                    <div className="text-gray-400 text-xs mb-2">AI 분석 근거:</div>
                    <ul className="text-xs text-gray-300 space-y-1">
                      <li>• 현재 재고: {selectedItem?.quantity || 0}개</li>
                      <li>• 최소 재고: {selectedItem?.minimumStock || 0}개</li>
                      <li>• 예상 소진 기간: 14일</li>
                      <li>• 납기 고려 안전 재고: 2배수 권장</li>
                    </ul>
                  </div>
                </div>
                
                <div className="flex gap-2 mt-4">
                  <Button 
                    onClick={() => {
                      // AI 추천 사항으로 발주 처리
                      console.log("AI 추천 발주 실행:", {
                        item: selectedItem?.product,
                        quantity: Math.max(100, (selectedItem?.minimumStock || 0) * 2),
                        type: "ai_recommended"
                      })
                      setShowOrderModal(false)
                    }}
                    className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
                  >
                    AI 추천으로 발주
                  </Button>
                  <Button
                    onClick={() => setShowOrderModal(false)}
                    variant="outline"
                    className="border-gray-600 text-gray-300 hover:bg-gray-700"
                  >
                    취소
                  </Button>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="manual" className="space-y-4 mt-4">
              {/* 직접 발주 섹션 */}
              <div className="bg-[#0D1117]/50 border border-blue-500/30 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Package className="w-5 h-5 text-blue-400" />
                  <h3 className="text-white font-semibold">직접 발주 입력</h3>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="text-white block mb-2 text-sm">발주 부품</label>
                    <Input
                      value={orderData.orderPart}
                      onChange={(e) => setOrderData(prev => ({ ...prev, orderPart: e.target.value }))}
                      className="bg-[#0D1117]/50 backdrop-blur-sm border-[#30363D] text-white"
                      placeholder="발주할 부품명"
                      disabled
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-white block mb-2 text-sm">발주 수량</label>
                      <Input
                        type="number"
                        value={orderData.orderQuantity}
                        onChange={(e) => setOrderData(prev => ({ ...prev, orderQuantity: e.target.value }))}
                        className="bg-[#0D1117]/50 backdrop-blur-sm border-[#30363D] text-white [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        placeholder="수량 입력"
                      />
                    </div>
                    
                    <div>
                      <label className="text-white block mb-2 text-sm">예상 단가(₩)</label>
                      <Input
                        type="number"
                        value={orderData.amount}
                        onChange={(e) => setOrderData(prev => ({ ...prev, amount: e.target.value }))}
                        className="bg-[#0D1117]/50 backdrop-blur-sm border-[#30363D] text-white [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        placeholder="단가 입력"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-white block mb-2 text-sm">도착 요청일</label>
                    <Input
                      type="date"
                      value={orderData.deliveryDate}
                      onChange={(e) => setOrderData(prev => ({ ...prev, deliveryDate: e.target.value }))}
                      className="bg-[#0D1117]/50 backdrop-blur-sm border-[#30363D] text-white"
                    />
                  </div>
                  
                  {/* 예상 총 비용 표시 */}
                  {orderData.orderQuantity && orderData.amount && (
                    <div className="bg-[#161B22]/50 border border-[#30363D] rounded p-3">
                      <div className="text-sm text-gray-400">예상 총 비용:</div>
                      <div className="text-lg font-bold text-green-400">
                        ₩{(Number(orderData.orderQuantity) * Number(orderData.amount)).toLocaleString()}
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2 mt-4">
                  <Button
                    onClick={handleSubmitOrder}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                    disabled={!orderData.orderPart || !orderData.orderQuantity || !orderData.deliveryDate || !orderData.amount}
                  >
                    직접 발주 요청
                  </Button>
                  <Button
                    onClick={() => setShowOrderModal(false)}
                    variant="outline"
                    className="border-gray-600 text-gray-300 hover:bg-gray-700"
                  >
                    취소
                  </Button>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

      {/* 재고 AI 상담 챗봇 모달 */}
      <Dialog open={showChatbotModal} onOpenChange={setShowChatbotModal}>
        <DialogContent className="bg-[#0D1117]/95 backdrop-blur-xl border-[#30363D] shadow-2xl max-w-[600px] max-h-[700px] mx-4">
          <DialogHeader className="border-b border-[#30363D] pb-4">
            <DialogTitle className="text-white flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <div className="text-lg font-semibold">재고 관리 AI 어시스턴트</div>
                <div className="text-sm text-gray-400 font-normal">부품 재고와 관련된 질문을 도와드립니다</div>
              </div>
            </DialogTitle>
          </DialogHeader>
          
          <div className="flex flex-col h-[500px]">
            {/* 메시지 영역 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#161B22]/30 rounded-lg">
              {chatMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.isUser ? "justify-end" : "justify-start"}`}
                >
                  <div className={`flex items-start gap-2 max-w-[80%] ${message.isUser ? "flex-row-reverse" : "flex-row"}`}>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.isUser 
                        ? "bg-blue-600" 
                        : "bg-gradient-to-br from-purple-600 to-blue-600"
                    }`}>
                      {message.isUser ? (
                        <div className="w-3 h-3 bg-white rounded-full" />
                      ) : (
                        <Bot className="w-3 h-3 text-white" />
                      )}
                    </div>
                    <div className={`px-3 py-2 rounded-lg text-sm whitespace-pre-wrap ${
                      message.isUser
                        ? "bg-blue-600 text-white"
                        : "bg-[#21262D] text-gray-200"
                    }`}>
                      {message.content}
                      <div className="text-xs opacity-60 mt-1">
                        {message.timestamp.toLocaleTimeString("ko-KR", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {/* 로딩 상태 */}
              {isChatLoading && (
                <div className="flex justify-start">
                  <div className="flex items-start gap-2">
                    <div className="w-6 h-6 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center">
                      <Bot className="w-3 h-3 text-white" />
                    </div>
                    <div className="px-3 py-2 rounded-lg bg-[#21262D] text-gray-200">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                      </div>
                      <div className="text-xs opacity-60 mt-1">
                        AI가 재고 데이터를 분석하고 있습니다...
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* 입력 영역 */}
            <div className="p-4 border-t border-[#30363D]">
              <div className="flex gap-2">
                <Input
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendChatMessage()
                    }
                  }}
                  placeholder="재고 관리에 대해 궁금한 점을 물어보세요..."
                  className="flex-1 bg-[#161B22] border-[#30363D] text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500/50"
                  disabled={isChatLoading}
                />
                <Button
                  onClick={handleSendChatMessage}
                  disabled={!currentMessage.trim() || isChatLoading}
                  className="px-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              
              {/* 빠른 질문 버튼들 */}
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs border-[#30363D] text-gray-300 hover:bg-[#21262D]"
                  disabled={isChatLoading}
                  onClick={() => handleQuickAction("low_stock", "부족한 재고 확인해줘")}
                >
                  부족한 재고 확인
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs border-[#30363D] text-gray-300 hover:bg-[#21262D]"
                  disabled={isChatLoading}
                  onClick={() => handleQuickAction("moisture_management", "흡습 관리 필요한 부품 알려줘")}
                >
                  흡습 관리 필요 부품
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs border-[#30363D] text-gray-300 hover:bg-[#21262D]"
                  disabled={isChatLoading}
                  onClick={() => handleQuickAction("ordering_recommendation", "발주 추천해줘")}
                >
                  발주 추천
                </Button>
              </div>
              
              {/* 상태 표시 */}
              <div className="mt-2 text-xs text-gray-500 text-center">
                💬 재고 관리 AI가 실시간으로 답변해드립니다
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Menu4