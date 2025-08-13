"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageCircle, X, Send, Bot, User, Maximize2, Minimize2 } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"

// ✅ 로컬 테스트용 URL 활성화
const GEMINI_API_URL = "http://localhost:5100/api/chat" // 테스트용
// const GEMINI_API_URL = "http://43.201.249.204:5000/api/chat" // Flask 서버 주소 (프로덕션용)

interface Message {
  id: string
  role: "system" | "assistant" | "user"
  content: string
  timestamp: Date
}

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    { 
      role: "system", 
      content: "당신은 친절한 AI 비서입니다.",
      id: "1",
      timestamp: new Date()
    },
    { 
      role: "assistant", 
      content: "안녕하세요! PCB-Manager 챗봇입니다. 무엇을 도와드릴까요?",
      id: "2",
      timestamp: new Date()
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  // 누락된 ref 추가
  const [isExpanded, setIsExpanded] = useState(false)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const toggleChat = () => setIsOpen(!isOpen)
  const toggleExpanded = () => setIsExpanded(!isExpanded) // 누락된 함수 추가

  // 자동 스크롤 효과 추가
  useEffect(() => {
    if (messages.length > 0 && messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (input.trim() === "") return
  
    // ✅ 메시지 객체에 id와 timestamp 추가
    const userMessage = { 
      role: "user", 
      content: input,
      id: Date.now().toString(),
      timestamp: new Date()
    }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput("")
    setIsLoading(true)
  
    try {
      console.log("📤 API 요청 시작:", GEMINI_API_URL)
      console.log("📋 전송 데이터:", { messages: newMessages })
      
      const res = await fetch(GEMINI_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      })
      
      console.log("📡 응답 상태:", res.status, res.statusText)
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }
  
      const result = await res.json()
      console.log("📥 받은 응답:", result)
      
      const answer = result.message?.content || "응답을 받지 못했습니다."
      
      // ✅ AI 응답에도 id와 timestamp 추가
      const assistantMessage = {
        role: "assistant", 
        content: answer,
        id: (Date.now() + 1).toString(),
        timestamp: new Date()
      }
      setMessages([...newMessages, assistantMessage])
    } catch (err) {
      console.error("❌ API 오류:", err)
      const errorMessage = {
        role: "assistant", 
        content: `🚨 **연결 오류**\n\n서버에 연결할 수 없습니다.\n\n**확인사항:**\n- Flask 서버가 실행 중인지 확인 (http://localhost:5100)\n- 서버 로그를 확인해주세요\n\n**오류 상세:** ${err instanceof Error ? err.message : '알 수 없는 오류'}`,
        id: (Date.now() + 1).toString(),
        timestamp: new Date()
      }
      setMessages([...newMessages, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      {/* 챗봇 아이콘 */}
      <div className="fixed bottom-6 right-6 z-50">
        {!isOpen && (
          <Button
            onClick={() => setIsOpen(true)}
            className="w-16 h-16 rounded-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl transition-all duration-300"
            size="icon"
          >
            <MessageCircle className="w-7 h-7 text-white" />
          </Button>
        )}
      </div>

      {/* 챗봇 사이드바 */}
      {isOpen && (
        <>
          {/* 배경 오버레이 */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300"
            onClick={() => setIsOpen(false)}
          />
          
          {/* 사이드바 */}
          <div 
            className={`fixed top-0 right-0 h-full z-50 transition-transform duration-300 ease-in-out ${
              isOpen ? 'translate-x-0' : 'translate-x-full'
            }`}
            style={{
              width: isExpanded ? '500px' : '400px',
              maxWidth: '90vw'
            }}
          >
            <Card className="bg-[#161B22] border-[#30363D] shadow-2xl h-full flex flex-col rounded-none border-r-0">
              <CardHeader className="border-b border-[#30363D]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-blue-700 rounded-full flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <CardTitle className="text-white text-sm">PCB-Manager 챗봇</CardTitle>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      onClick={toggleExpanded}
                      variant="ghost"
                      size="icon"
                      className="w-6 h-6 text-gray-400 hover:text-white"
                    >
                      {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                    </Button>
                    <Button
                      onClick={() => setIsOpen(false)}
                      variant="ghost"
                      size="icon"
                      className="w-6 h-6 text-gray-400 hover:text-white"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="flex-1 flex flex-col p-0 h-full overflow-hidden">
                {/* 메시지 영역 - 고정 높이, 내부 스크롤 */}
                <div 
                  ref={messagesContainerRef} 
                  className="flex-1 overflow-y-auto p-4 space-y-3 chatbot-messages"
                  style={{
                    minHeight: '300px'
                  }}
                >
                  {messages
                    .filter((msg) => msg.role !== "system")
                    .map((message, index) => (
                    <div
                      key={message.id || index}
                      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[80%] p-3 rounded-lg ${
                          message.role === "user"
                            ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white"
                            : "bg-[#0D1117] border border-[#30363D] text-white"
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          {message.role === "assistant" && <Bot className="w-4 h-4 mt-0.5 text-blue-400 flex-shrink-0" />}
                          {message.role === "user" && <User className="w-4 h-4 mt-0.5 text-white flex-shrink-0" />}
                          <div className="flex-1">
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                            <p className="text-xs opacity-70 mt-1">
                              {message.timestamp.toLocaleTimeString("ko-KR", {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-[#0D1117] border border-[#30363D] text-white p-2 rounded-lg max-w-[80%]">
                        <div className="flex items-center gap-2">
                          <Bot className="w-4 h-4 text-blue-400" />
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                            <div
                              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                              style={{ animationDelay: "0.1s" }}
                            ></div>
                            <div
                              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                              style={{ animationDelay: "0.2s" }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>

                {/* 입력 영역 - 하단 고정 */}
                <div className="border-t border-[#30363D] p-2 flex-shrink-0">
                  <div className="flex gap-3">
                    <Input
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSend()}
                      placeholder="메시지를 입력하세요..."
                      className="flex-1 bg-[#0D1117] border-[#30363D] text-white text-sm h-12 px-4 py-3"
                      disabled={isLoading}
                    />
                    <Button
                      onClick={handleSend}
                      size="icon"
                      className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 w-16 h-12 flex-shrink-0"
                      disabled={isLoading || !input.trim()}
                    >
                      <Send className="w-5 h-5" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </>
  )
}