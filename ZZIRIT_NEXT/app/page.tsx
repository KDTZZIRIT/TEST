"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {
  Cpu,
  BarChart3,
  Database,
  User,
  FileText,
  Search,
  FlaskRoundIcon as Flask,
  Cog,
  TrendingUp,
} from "lucide-react"
import { useRouter } from "next/navigation"
// import Chatbot from "@/components/chatbot"
import Header from "@/components/layout/header"
import HeroSection from "@/components/main/main1"
import FeaturesSection from "@/components/main/main2"
import ProcessSection from "@/components/main/main3"
import TeamSection from "@/components/main/main4"
import Footer from "@/components/layout/footer"
import AuthModal from "@/components/auth-modal"
import Chatbot from "@/components/chatbot/chatbot"

function LandingPage() {
  const [isLoginOpen, setIsLoginOpen] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const router = useRouter()

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    // 간단한 로그인 처리 (실제로는 인증 로직 필요)
    if (email && password) {
      setIsLoginOpen(false)
      router.push("/dashboard")
    }
  }

  const handleDashboardClick = () => {
    router.push("/dashboard")
  }
}
export default function HomePage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [authMode, setAuthMode] = useState<"login" | "signup">("login")
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  // 페이지 로드 시 로그인 상태 확인
  useEffect(() => {
    const token = localStorage.getItem("auth-token")
    if (token) {
      setIsLoggedIn(true)
    }
  }, [])

  const openModal = (mode: "login" | "signup") => {
    setAuthMode(mode)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
  }

  const handleLoginSuccess = () => {
    setIsLoggedIn(true)
    closeModal()
  }

  const handleLogout = () => {
    localStorage.removeItem("auth-token")
    setIsLoggedIn(false)
    // 로그아웃 후 로그인 모달을 다시 띄울 수 있도록 상태를 초기화합니다.
    setTimeout(() => openModal("login"), 100)
  }

  return (
    <div className="bg-[#0A0E1A] text-white">
      <Header isLoggedIn={isLoggedIn} onLogout={handleLogout} />
      <main className="h-screen overflow-y-scroll snap-y snap-mandatory no-scrollbar">
        <section className="snap-start h-screen w-full">
          <HeroSection
            onLogin={() => openModal("login")}
            onSignup={() => openModal("signup")}
            isLoggedIn={isLoggedIn}
            onLogout={handleLogout}
          />
        </section>
        <section className="snap-start h-screen w-full flex items-center justify-center bg-[#0A0E1A] relative">
          <div
            className="absolute inset-0 z-0 bg-cover bg-center opacity-30"
            style={{ backgroundImage: `url(/images/futuristic-pcb-bg.png)` }}
          />
          <div className="relative z-10 w-full">
            <FeaturesSection />
          </div>
        </section>
        <section className="snap-start h-screen w-full flex items-center justify-center bg-[#0A0E1A]">
          <ProcessSection />
        </section>
        <section className="snap-start h-screen w-full flex items-center justify-center bg-[#101629]">
          <TeamSection />
        </section>
        <section className="snap-start h-screen w-full relative">
          <Footer />
        </section>
      </main>
      <AuthModal isOpen={isModalOpen} onClose={closeModal} initialMode={authMode} onLoginSuccess={handleLoginSuccess} />
      <Chatbot />
    </div>
  )
}
