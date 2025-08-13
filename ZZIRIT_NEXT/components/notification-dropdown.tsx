"use client"

import { useState, useRef, useEffect } from "react"
import { Bell, X, AlertCircle, CheckCircle, Info, AlertTriangle } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface Notification {
  id: string
  type: "info" | "success" | "warning" | "error"
  title: string
  message: string
  timestamp: string
  isRead: boolean
}

interface NotificationDropdownProps {
  isLoggedIn: boolean
}

export default function NotificationDropdown({ isLoggedIn }: NotificationDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: "1",
      type: "warning",
      title: "재고 부족 알림",
      message: "저항 10kΩ 부품의 재고가 부족합니다. 주문이 필요합니다.",
      timestamp: "5분 전",
      isRead: false
    },
    {
      id: "2", 
      type: "success",
      title: "불량 검사 완료",
      message: "PCB-001 기판의 불량 검사가 완료되었습니다.",
      timestamp: "10분 전",
      isRead: false
    },
    {
      id: "3",
      type: "info",
      title: "시스템 업데이트",
      message: "새로운 기능이 추가되었습니다. 확인해보세요.",
      timestamp: "1시간 전",
      isRead: true
    },
    {
      id: "4",
      type: "error",
      title: "장비 오류",
      message: "SMT 라인 #2에서 오류가 감지되었습니다.",
      timestamp: "2시간 전",
      isRead: false
    }
  ])
  
  const dropdownRef = useRef<HTMLDivElement>(null)

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  if (!isLoggedIn) return null

  const unreadCount = notifications.filter(n => !n.isRead).length
  const displayCount = unreadCount > 99 ? "99+" : unreadCount.toString()

  const getIcon = (type: string) => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-400" />
      default:
        return <Info className="w-4 h-4 text-blue-400" />
    }
  }

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, isRead: true } : n)
    )
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, isRead: true })))
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* 알림 버튼 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 hover:bg-[#21262D]/50 rounded-lg transition-colors duration-200"
      >
        <Bell className="w-5 h-5 text-gray-400 hover:text-white transition-colors" />
        
        {/* 알림 카운트 배지 */}
        {unreadCount > 0 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full min-w-5 h-5 flex items-center justify-center px-1"
          >
            {displayCount}
          </motion.div>
        )}
      </button>

      {/* 드롭다운 메뉴 */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="absolute right-0 top-full mt-2 w-80 bg-[#161B22] border border-[#30363D] rounded-xl shadow-2xl shadow-black/50 z-50 overflow-hidden"
          >
            {/* 헤더 */}
            <div className="p-4 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-b border-[#30363D] flex items-center justify-between">
              <h3 className="font-medium text-white">알림</h3>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  모두 읽음
                </button>
              )}
            </div>

            {/* 알림 목록 */}
            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-gray-400">
                  <Bell className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>새로운 알림이 없습니다</p>
                </div>
              ) : (
                <div className="divide-y divide-[#30363D]">
                  {notifications.map((notification) => (
                    <motion.div
                      key={notification.id}
                      layout
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className={`p-4 hover:bg-[#21262D]/50 transition-colors relative group ${
                        !notification.isRead ? "bg-blue-500/5" : ""
                      }`}
                      onClick={() => markAsRead(notification.id)}
                    >
                      <div className="flex items-start gap-3">
                        {/* 아이콘 */}
                        <div className="flex-shrink-0 mt-1">
                          {getIcon(notification.type)}
                        </div>

                        {/* 내용 */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <h4 className={`text-sm font-medium ${
                              !notification.isRead ? "text-white" : "text-gray-300"
                            }`}>
                              {notification.title}
                            </h4>
                            
                            {/* 삭제 버튼 */}
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                removeNotification(notification.id)
                              }}
                              className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-500/20 rounded-md"
                            >
                              <X className="w-3 h-3 text-gray-400 hover:text-red-400" />
                            </button>
                          </div>
                          
                          <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                            {notification.message}
                          </p>
                          
                          <div className="flex items-center justify-between mt-2">
                            <span className="text-xs text-gray-500">
                              {notification.timestamp}
                            </span>
                            {!notification.isRead && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                            )}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* 푸터 */}
            {notifications.length > 0 && (
              <div className="p-3 bg-[#0D1117] border-t border-[#30363D] text-center">
                <button className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
                  모든 알림 보기
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
} 