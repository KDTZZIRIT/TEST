"use client"

import type React from "react"
import { useState, useEffect, type FC } from "react"
import { useRouter } from "next/navigation"

// Import separated components
import Header from "@/components/menu/header"
import Menu1 from "@/components/menu/menu1"
import Menu2 from "@/components/menu/menu2"
import Menu3 from "@/components/menu/menu3"
import Menu4 from "@/components/menu/menu4"
import MSE from "@/components/menu/mse"

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("overview")
  const [searchTerm, setSearchTerm] = useState("")
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  // 인증 검증
  useEffect(() => {
    const token = localStorage.getItem("auth-token")
    
    if (!token) {
      // 토큰이 없으면 로그인 페이지로 리다이렉트
      router.push("/login")
    } else {
      // 토큰이 있으면 인증 완료
      setIsAuthenticated(true)
    }
    
    setIsLoading(false)
  }, [router])

  const handleLogout = () => {
    // 토큰과 사용자 정보 모두 삭제
    localStorage.removeItem("auth-token")
    localStorage.removeItem("user-info")
    router.push("/")
  }

  // 로딩 중이거나 인증되지 않은 경우
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0D1117] flex items-center justify-center">
        <div className="text-white text-lg">로딩 중...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null // 리다이렉트 중이므로 아무것도 렌더링하지 않음
  }

  return (
    <div className="min-h-screen bg-[#0D1117] text-gray-200 font-sans">
      <div className="w-full">
        <Header
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          isLoggedIn={true}
          onLogout={handleLogout}
        />

        <main className="p-6">
          {activeTab === "overview" && <Menu1 />}
          {activeTab === "defects" && <Menu2 />}
          {activeTab === "analytics" && <Menu3 />}
          {activeTab === "inventory" && <Menu4 />}
          {activeTab === "mes" && <MSE />}
        </main>
      </div>
    </div>
  )
}
