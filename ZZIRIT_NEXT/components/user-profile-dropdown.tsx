"use client"

import { useState, useRef, useEffect } from "react"
import { User, Settings, LogOut, Database } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface UserInfo {
  name: string
  email: string
  position: string
}

interface UserProfileDropdownProps {
  isLoggedIn: boolean
  onLogout: () => void
}

export default function UserProfileDropdown({ isLoggedIn, onLogout }: UserProfileDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // localStorage에서 사용자 정보 로드
  useEffect(() => {
    if (isLoggedIn) {
      const storedUserInfo = localStorage.getItem("user-info")
      if (storedUserInfo) {
        try {
          setUserInfo(JSON.parse(storedUserInfo))
        } catch (error) {
          console.error("사용자 정보 파싱 오류:", error)
        }
      }
    }
  }, [isLoggedIn])

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

  return (
    <div className="relative" ref={dropdownRef}>
      {/* 프로필 아바타 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1 rounded-full hover:bg-[#21262D]/50 transition-colors duration-200"
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg">
          <User className="w-4 h-4 text-white" />
        </div>
        <div className="hidden sm:block text-left">
          <p className="text-sm font-medium text-white">{userInfo?.name || "사용자"}</p>
          <p className="text-xs text-gray-400">{userInfo?.email || ""}</p>
        </div>
      </button>

      {/* 드롭다운 메뉴 */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="absolute right-0 top-full mt-2 w-64 bg-[#161B22] border border-[#30363D] rounded-xl shadow-2xl shadow-black/50 z-50 overflow-hidden"
          >
            {/* 헤더 */}
            <div className="p-4 bg-gradient-to-r from-cyan-500/10 to-blue-600/10 border-b border-[#30363D]">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="font-medium text-white">{userInfo?.name || "사용자"}</p>
                  <p className="text-sm text-gray-400">{userInfo?.position || ""}</p>
                </div>
              </div>
            </div>

            {/* 이메일 */}
            <div className="px-4 py-2 border-b border-[#30363D]">
              <p className="text-sm text-gray-300">{userInfo?.email || ""}</p>
            </div>

            {/* 메뉴 항목들 */}
            <div className="py-2">
              <button className="w-full px-4 py-3 text-left hover:bg-[#21262D] transition-colors duration-200 flex items-center gap-3 text-gray-300 hover:text-white">
                <User className="w-4 h-4" />
                <span>프로필</span>
              </button>
              <button className="w-full px-4 py-3 text-left hover:bg-[#21262D] transition-colors duration-200 flex items-center gap-3 text-gray-300 hover:text-white">
                <Settings className="w-4 h-4" />
                <span>설정</span>
              </button>
              <button className="w-full px-4 py-3 text-left hover:bg-[#21262D] transition-colors duration-200 flex items-center gap-3 text-gray-300 hover:text-white">
                <Database className="w-4 h-4" />
                <span>데이터 관리</span>
              </button>
            </div>

            {/* 로그아웃 */}
            <div className="border-t border-[#30363D] p-2">
              <button
                onClick={() => {
                  onLogout()
                  setIsOpen(false)
                }}
                className="w-full px-4 py-3 text-left hover:bg-red-500/10 hover:text-red-400 transition-colors duration-200 flex items-center gap-3 text-gray-300 rounded-lg"
              >
                <LogOut className="w-4 h-4" />
                <span>로그아웃</span>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
} 