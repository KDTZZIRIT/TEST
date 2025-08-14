import React, { useState, useEffect, useRef } from "react"
import { X, Send, Bot, User, RefreshCw, AlertTriangle, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
  metadata?: {
    response_time?: number
    data_source?: string
    error?: boolean
  }
}

interface ChatbotModalProps {
  isOpen: boolean
  onClose: () => void
  currentMenu?: string
}

interface PerformanceInfo {
  crawling_time?: number
  ai_response_time?: number
  total_time?: number
}

interface ApiStatus {
  ready: boolean
  api_key_set: boolean
  model_loaded: boolean
  statistics?: {
    total_requests: number
    successful_requests: number
    failed_requests: number
    success_rate: number
  }
}

const ChatbotModal = ({ isOpen, onClose, currentMenu }: ChatbotModalProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "안녕하세요! PCB-Manager AI 어시스트입니다. 전체 시스템 데이터를 실시간으로 분석해드릴 수 있습니다. 어떤 도움이 필요하신가요?",
      isUser: false,
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting' | 'degraded'>('disconnected')
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null)
  const [performanceInfo, setPerformanceInfo] = useState<PerformanceInfo | null>(null)
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 개선된 서버 URL 결정 로직
  const getServerUrl = () => {

    // 2. 현재 호스트 기반 판단
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname
      
      // 로컬 개발 환경
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        console.log('🏠 로컬 개발 환경 감지')
        return "http://localhost:5100"
      }
      
      // 프로덕션 환경
      if (hostname.includes('vercel.app') || hostname.includes('netlify.app')) {
        console.log('☁️ 클라우드 프로덕션 환경 감지')
        return "http://localhost:5100"
      }
    }

    // 3. 기본값 (프로덕션)
    console.log('🌍 기본 프로덕션 서버 사용')
    return "http://localhost:5100"
  }

  // 연결 상태 확인 (개선된 버전)
  const checkConnection = async () => {
    try {
      setConnectionStatus('connecting')
      const serverUrl = getServerUrl()
      console.log('🔍 서버 연결 확인:', serverUrl)
      
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10초 타임아웃
      
      const response = await fetch(`${serverUrl}/api/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (response.ok) {
        const healthData = await response.json()
        console.log('✅ 서버 연결 성공:', healthData)
        
        // 상세한 상태 분석
        const components = healthData.components || {}
        const geminiStatus = components.gemini_api?.status === 'healthy'
        const crawlerStatus = components.crawler?.status === 'working'
        
        if (geminiStatus && crawlerStatus) {
          setConnectionStatus('connected')
        } else {
          setConnectionStatus('degraded')
        }
        
        // API 상태 정보 저장
        if (components.gemini_api?.details) {
          setApiStatus(components.gemini_api.details)
        }
        
        setLastUpdateTime(new Date())
        return true
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error: any) {
      console.warn('⚠️ 서버 연결 실패:', error)
      setConnectionStatus('disconnected')
      setLastUpdateTime(new Date())
      
      if (error.name === 'AbortError') {
        console.log('⏰ 연결 확인 시간 초과')
      }
      
      return false
    }
  }

  // 컴포넌트 마운트시 연결 확인
  useEffect(() => {
    if (isOpen) {
      checkConnection()
      
      // 주기적 상태 확인 (30초마다)
      const interval = setInterval(() => {
        checkConnection()
      }, 30000)
      
      return () => clearInterval(interval)
    }
  }, [isOpen])

  // 메시지 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // 개선된 메시지 전송 함수
  const sendMessageViaHttp = async (message: string) => {
    try {
      const serverUrl = getServerUrl()
      console.log('📤 메시지 전송:', serverUrl)
      
      const requestData = {
        message: message,
        menu: currentMenu || 'overview',
        context: {
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          menu: currentMenu,
          session_id: `session_${Date.now()}`
        }
      }

      console.log('📋 전송 데이터:', requestData)

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 60000) // 60초 타임아웃
      
      const response = await fetch(`${serverUrl}/api/llm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(requestData),
        signal: controller.signal
      })

      clearTimeout(timeoutId)
      console.log('📡 응답 상태:', response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`)
      }

      const data = await response.json()
      console.log('📥 받은 응답:', data)
      
      if (data.success === false) {
        throw new Error(data.error || '서버에서 오류를 반환했습니다.')
      }
      
      // 성능 정보 저장
      if (data.performance) {
        setPerformanceInfo(data.performance)
      }
      
      // API 상태 정보 업데이트
      if (data.api_status) {
        setApiStatus(data.api_status)
      }
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response || "응답을 받지 못했습니다.",
        isUser: false,
        timestamp: new Date(),
        metadata: {
          response_time: data.performance?.ai_response_time,
          data_source: data.data_metadata?.data_sources ? 'api' : 'fallback',
          error: false
        }
      }
      
      setMessages(prev => [...prev, aiMessage])
      setConnectionStatus('connected')
      setLastUpdateTime(new Date())
      
    } catch (error: any) {
      console.error("❌ HTTP 요청 오류:", error)
      setConnectionStatus('disconnected')
      
      let errorMessage = "알 수 없는 오류가 발생했습니다."
      let isTimeout = false
      
      if (error.name === 'AbortError') {
        errorMessage = `⏰ **응답 시간 초과**\n\n서버 응답이 60초를 초과했습니다.\n\n**가능한 원인:**\n- 서버 과부하\n- 대용량 데이터 처리 중\n- 네트워크 지연\n\n잠시 후 다시 시도해주세요.`
        isTimeout = true
      } else if (error instanceof Error) {
        const errorStr = error.message.toLowerCase()
        
        if (errorStr.includes('fetch') || errorStr.includes('network')) {
          errorMessage = `🌐 **네트워크 연결 오류**\n\n서버에 연결할 수 없습니다.\n\n**확인사항:**\n- 인터넷 연결 상태 확인\n- 서버 주소: ${getServerUrl()}\n- 방화벽 설정 확인\n\n잠시 후 다시 시도해주세요.`
        } else if (errorStr.includes('cors')) {
          errorMessage = `🔒 **CORS 오류**\n\n브라우저 보안 정책으로 인한 접근 제한입니다.\n\n**해결방법:**\n- 서버 관리자에게 문의\n- 브라우저 캐시 삭제 후 재시도`
        } else if (errorStr.includes('500')) {
          errorMessage = `🔧 **서버 내부 오류**\n\n서버에서 처리 중 문제가 발생했습니다.\n\n관리자에게 문의해주세요.`
        } else if (errorStr.includes('503')) {
          errorMessage = `⚠️ **서비스 일시 중단**\n\nAI 시스템이 일시적으로 사용할 수 없습니다.\n\n잠시 후 다시 시도해주세요.`
        } else {
          errorMessage = `❌ **오류 발생**\n\n${error.message}\n\n**서버 정보:**\n- URL: ${getServerUrl()}\n- 현재 메뉴: ${currentMenu}\n- 시간: ${new Date().toLocaleString()}\n\n잠시 후 다시 시도해주세요.`
        }
      }
      
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: errorMessage,
        isUser: false,
        timestamp: new Date(),
        metadata: {
          error: true,
          response_time: isTimeout ? 60 : undefined
        }
      }
      
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  // 메시지 전송 함수
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputMessage,
      isUser: true,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const messageToSend = inputMessage
    setInputMessage("")
    setIsLoading(true)

    // HTTP 방식으로 메시지 전송
    await sendMessageViaHttp(messageToSend)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 연결 재시도 함수
  const handleReconnect = async () => {
    const success = await checkConnection()
    if (success) {
      const reconnectMessage: Message = {
        id: Date.now().toString(),
        text: "✅ 서버 연결이 복구되었습니다. 다시 질문해주세요!",
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, reconnectMessage])
    }
  }

  // 대화 기록 초기화
  const handleClearChat = () => {
    setMessages([
      {
        id: "1",
        text: "대화 기록이 초기화되었습니다. 새로운 질문을 해주세요!",
        isUser: false,
        timestamp: new Date()
      }
    ])
    setPerformanceInfo(null)
  }

  // 연결 상태 표시 색상
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500'
      case 'connecting': return 'bg-yellow-500 animate-pulse'
      case 'degraded': return 'bg-orange-500'
      case 'disconnected': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  // 연결 상태 텍스트
  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return '정상 연결'
      case 'connecting': return '연결 중...'
      case 'degraded': return '제한적 연결'
      case 'disconnected': return '연결 끊김'
      default: return '알 수 없음'
    }
  }

  // 연결 상태 아이콘
  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'connecting': return <RefreshCw className="w-4 h-4 text-yellow-400 animate-spin" />
      case 'degraded': return <AlertTriangle className="w-4 h-4 text-orange-400" />
      case 'disconnected': return <X className="w-4 h-4 text-red-400" />
      default: return null
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* 배경 오버레이 */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* 챗봇 모달 */}
      <div className="relative w-1/3 h-full bg-[#0D1117] border-l border-[#30363D] shadow-2xl flex flex-col">
        {/* 헤더 (개선된 버전) */}
        <div className="flex items-center justify-between p-4 border-b border-[#30363D] bg-[#161B22] flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="text-white font-semibold">PCB-Manager AI</h3>
              <div className="flex items-center gap-2">
                <p className="text-xs text-gray-400">
                  {currentMenu ? `메뉴: ${currentMenu}` : "전체 시스템"}
                </p>
                <div className="flex items-center gap-1">
                  {getStatusIcon()}
                  <span className={`text-xs ${
                    connectionStatus === 'connected' ? 'text-green-400' : 
                    connectionStatus === 'connecting' ? 'text-yellow-400' : 
                    connectionStatus === 'degraded' ? 'text-orange-400' : 'text-red-400'
                  }`}>
                    {getStatusText()}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {connectionStatus === 'disconnected' && (
              <button
                onClick={handleReconnect}
                className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                title="다시 연결"
              >
                재연결
              </button>
            )}
            <button
              onClick={handleClearChat}
              className="px-3 py-1 text-xs bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
              title="대화 기록 초기화"
            >
              초기화
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-[#21262D] rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400 hover:text-white" />
            </button>
          </div>
        </div>

        {/* 상태 정보 바 */}
        {(apiStatus || performanceInfo) && (
          <div className="bg-[#0D1117] border-b border-[#30363D] p-2 text-xs">
            <div className="flex items-center justify-between text-gray-400">
              {apiStatus && (
                <div className="flex items-center gap-4">
                  <span>API: {apiStatus.ready ? '준비됨' : '대기중'}</span>
                  {apiStatus.statistics && (
                    <span>성공률: {apiStatus.statistics.success_rate}%</span>
                  )}
                </div>
              )}
              {performanceInfo && (
                <div className="flex items-center gap-2">
                  {performanceInfo.total_time && (
                    <span>응답시간: {performanceInfo.total_time.toFixed(1)}초</span>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.isUser ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`flex items-start gap-2 max-w-[80%] ${
                  message.isUser ? "flex-row-reverse" : "flex-row"
                }`}
              >
                <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.isUser 
                    ? "bg-blue-600" 
                    : message.metadata?.error 
                      ? "bg-red-600"
                      : "bg-gradient-to-br from-purple-600 to-blue-600"
                }`}>
                  {message.isUser ? (
                    <User className="w-3 h-3 text-white" />
                  ) : message.metadata?.error ? (
                    <AlertTriangle className="w-3 h-3 text-white" />
                  ) : (
                    <Bot className="w-3 h-3 text-white" />
                  )}
                </div>
                <div
                  className={`px-3 py-2 rounded-lg text-sm whitespace-pre-wrap ${
                    message.isUser
                      ? "bg-blue-600 text-white"
                      : message.metadata?.error
                        ? "bg-red-600/20 text-red-200 border border-red-600/30"
                        : "bg-[#21262D] text-gray-200"
                  }`}
                >
                  {message.text}
                  <div className="flex items-center justify-between text-xs opacity-60 mt-2">
                    <span>
                      {message.timestamp.toLocaleTimeString("ko-KR", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                    {message.metadata?.response_time && (
                      <span className="ml-2">
                        {message.metadata.response_time.toFixed(1)}초
                      </span>
                    )}
                    {message.metadata?.data_source && (
                      <span className="ml-2">
                        {message.metadata.data_source === 'api' ? '🌐' : '📄'}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
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
                    AI가 시스템 데이터를 분석하고 있습니다...
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 입력 영역 */}
        <div className="p-4 border-t border-[#30363D] bg-[#161B22] flex-shrink-0">
          <div className="flex gap-2">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                connectionStatus === 'connected' 
                  ? "메시지를 입력하세요..." 
                  : connectionStatus === 'connecting'
                    ? "연결 중입니다..."
                    : "연결을 확인하세요..."
              }
              className="flex-1 bg-[#0D1117] border-[#30363D] text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500/50"
              disabled={isLoading || connectionStatus === 'disconnected' || connectionStatus === 'connecting'}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading || connectionStatus === 'disconnected' || connectionStatus === 'connecting'}
              className="px-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          
          {/* 상태 정보 */}
          <div className="mt-2 text-xs text-gray-500 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span>서버: {getServerUrl()}</span>
              <div className={`w-1 h-1 rounded-full ${getStatusColor()}`}></div>
            </div>
            {lastUpdateTime && (
              <span>업데이트: {lastUpdateTime.toLocaleTimeString()}</span>
            )}
          </div>
          
          {/* 도움말 */}
          {connectionStatus === 'connected' && !isLoading && (
            <div className="mt-2 text-xs text-gray-400">
              <div className="flex flex-wrap gap-2">
                <span className="bg-[#0D1117] px-2 py-1 rounded">💡 팁:</span>
                <span className="bg-[#0D1117] px-2 py-1 rounded">PCB 상태 질문</span>
                <span className="bg-[#0D1117] px-2 py-1 rounded">불량률 분석</span>
                <span className="bg-[#0D1117] px-2 py-1 rounded">재고 현황</span>
                <span className="bg-[#0D1117] px-2 py-1 rounded">부품 정보</span>
                <span className="bg-[#0D1117] px-2 py-1 rounded">흡습 자재</span>
              </div>
              <div className="mt-1 text-xs text-gray-500">
                예: "CL02A104K2NNNC 부품 정보 알려줘", "흡습 필요한 부품 목록", "재고 부족한 부품은?"
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ChatbotModal