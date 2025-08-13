"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useRef, useEffect, useState } from "react"
import { useMotionValue, useTransform, animate } from "framer-motion"

interface HeroSectionProps {
  onLogin: () => void
  onSignup: () => void
  isLoggedIn: boolean
  onLogout: () => void
}

// GradientText 컴포넌트를 내부에 정의
function GradientText({ children, className }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  const backgroundX = useTransform(mouseX, [0, 1], ["0%", "100%"])
  const backgroundY = useTransform(mouseY, [0, 1], ["0%", "100%"])

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      if (ref.current) {
        const rect = ref.current.getBoundingClientRect()
        const newMouseX = (event.clientX - rect.left) / rect.width
        const newMouseY = (event.clientY - rect.top) / rect.height

        animate(mouseX, newMouseX, { type: "spring", stiffness: 100, damping: 20 })
        animate(mouseY, newMouseY, { type: "spring", stiffness: 100, damping: 20 })
      }
    }

    window.addEventListener("mousemove", handleMouseMove)
    return () => window.removeEventListener("mousemove", handleMouseMove)
  }, [mouseX, mouseY])

  return (
    <span ref={ref} className={className}>
      <motion.span
        className="inline-block bg-clip-text text-transparent"
        style={{
          background: useTransform(
            [backgroundX, backgroundY],
            ([x, y]) => `radial-gradient(circle at ${x}% ${y}%, #67e8f9, #06b6d4, #0891b2)`
          ),
        }}
      >
        {children}
      </motion.span>
    </span>
  )
}

export default function HeroSection({ onLogin, onSignup, isLoggedIn, onLogout }: HeroSectionProps) {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  return (
    <section className="relative h-screen w-full flex flex-col items-center justify-center text-center bg-[#0A0E1A] overflow-hidden">
      {/* 배경 그리드 패턴 - 전체 화면에 적용 */}
      <div className="absolute inset-0 bg-[#0A0E1A]">
        <div 
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `
              linear-gradient(rgba(6, 182, 212, 0.1) 1px, transparent 1px),
              linear-gradient(200deg, rgba(6, 182, 212, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px'
          }}
        />
        {/* 방사형 그라데이션 오버레이 - 전체 화면에 적용 */}
        <div 
          className="absolute inset-0"
          style={{
            background: `radial-gradient(ellipse at center, rgba(6, 182, 212, 0.15) 0%, rgba(10, 14, 26, 0.8) 70%)`
          }}
        />
      </div>

      {/* 중앙 슬림 비디오 - 전체 화면에 적용 */}
      <div className="absolute inset-0 z-0">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover"
          style={{
            filter: "brightness(0.4) contrast(1.2) saturate(1.1)",
          }}
        >
          <source src="/videos/111.mp4" type="video/mp4" />
          Your browser does not support the video tag.
        </video>
        {/* 비디오 위 그라데이션 오버레이 - 전체 화면에 적용 */}
        <div 
          className="absolute inset-0"
          style={{
            background: `linear-gradient(
              45deg,
              rgba(6, 182, 212, 0.1) 0%,
              rgba(16, 22, 41, 0.6) 30%,
              rgba(10, 14, 26, 0.8) 70%,
              rgba(6, 182, 212, 0.1) 100%
            )`
          }}
        />
      </div>

      {/* 파티클 효과 - 전체 화면에 적용 (클라이언트 사이드에서만 렌더링) */}
      {isClient && (
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(30)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-cyan-400 rounded-full opacity-40"
              initial={{
                x: Math.random() * (typeof window !== 'undefined' ? window.innerWidth : 1200),
                y: Math.random() * (typeof window !== 'undefined' ? window.innerHeight : 800),
              }}
              animate={{
                y: [null, -100, null],
                opacity: [0.4, 0.8, 0.4],
              }}
              transition={{
                duration: 4 + Math.random() * 3,
                repeat: Infinity,
                delay: Math.random() * 3,
              }}
            />
          ))}
        </div>
      )}

      {/* 텍스트/버튼 컨테이너 - 정확히 중앙에 배치 */}
      <div className="absolute inset-0 flex items-center justify-center z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          className="w-full flex flex-col items-center"
          style={{
            background: "rgba(10, 14, 26, 0.3)",
            backdropFilter: "blur(20px)",
            borderRadius: "32px",
            border: "1px solid rgba(6, 182, 212, 0.2)",
            boxShadow: `
              0 20px 60px rgba(6, 182, 212, 0.1),
              inset 0 1px 0 rgba(255, 255, 255, 0.1)
            `,
            padding: "48px 32px",
            maxWidth: "1100px",
            margin: "0 auto",
            pointerEvents: "auto",
          }}
        >
          {/* 메인 제목 - 고체 파란색으로 변경 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.3 }}
          >
            <h1 className="text-4xl sm:text-5xl md:text-7xl font-extrabold tracking-tight mb-4 block leading-tight text-blue-400">
              차세대 PCB 제조 관리 솔루션
            </h1>
          </motion.div>

          {/* 서브 텍스트 - 고체 흰색으로 변경 */}
          <motion.p 
            className="max-w-3xl mx-auto text-lg md:text-xl text-white mb-8 leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.6 }}
          >
            복잡한 PCB 제조 공정을 한 곳에서. 
            <br className="hidden sm:block" />
            <span className="text-cyan-300 font-medium">스마트한 관리</span>, <span className="text-cyan-300 font-medium">효율적인 생산</span>을 경험하세요.
          </motion.p>

          {/* 버튼 그룹 */}
          <motion.div 
            className="flex flex-col sm:flex-row justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.9 }}
          >
            {isLoggedIn ? (
              <>
                <Button 
                  size="lg" 
                  className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white shadow-2xl shadow-cyan-500/25 border-0 px-8 py-4 text-lg font-medium transition-all duration-300 hover:scale-105 hover:shadow-cyan-500/40" 
                  asChild
                >
                  <Link href="/dashboard">🚀 대시보드로 이동</Link>
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="border-2 border-cyan-400/50 text-cyan-300 hover:bg-cyan-400/10 hover:text-white hover:border-cyan-400 bg-transparent backdrop-blur-sm px-8 py-4 text-lg font-medium transition-all duration-300 hover:scale-105"
                  onClick={onLogout}
                >
                  로그아웃
                </Button>
              </>
            ) : (
              <>
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white shadow-2xl shadow-cyan-500/25 border-0 px-8 py-4 text-lg font-medium transition-all duration-300 hover:scale-105 hover:shadow-cyan-500/40"
                  onClick={onLogin}
                >
                  🔐 로그인
                </Button>
                <Button 
                  size="lg" 
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-2xl shadow-blue-500/25 border-0 px-8 py-4 text-lg font-medium transition-all duration-300 hover:scale-105 hover:shadow-blue-500/40" 
                  onClick={onSignup}
                >
                  ✨ 회원가입
                </Button>
                {/* 개발 모드용 대시보드 버튼 */}
                <Button 
                  size="lg" 
                  className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white shadow-2xl shadow-green-500/25 border-0 px-8 py-4 text-lg font-medium transition-all duration-300 hover:scale-105 hover:shadow-green-500/40" 
                  asChild
                >
                  <Link href="/dashboard">⚡ 대시보드 (개발모드)</Link>
                </Button>
              </>
            )}
          </motion.div>

          {/* 하단 정보 텍스트 */}
          <motion.div
            className="mt-8 text-center text-sm text-gray-400"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 1.2 }}
          >
            <p>AI 기반 실시간 분석 • 자동화된 품질 관리 • 통합 재고 시스템</p>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}
