"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import InputWithIcon from "@/components/auth/input-with-icon"
import { Mail, Lock } from "lucide-react"
import { useRouter } from "next/navigation"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

export default function LoginForm({
  isActive,
  onLoginSuccess,
}: {
  isActive: boolean
  onLoginSuccess: () => void
}) {
  const router = useRouter()
  const [goToDashboard, setGoToDashboard] = useState(true)

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    localStorage.setItem("auth-token", "demo-token")
    onLoginSuccess()
    if (goToDashboard) {
      router.push("/dashboard")
    } else {
      router.push("/")
    }
  }

  return (
    <form
      onSubmit={handleLogin}
      className={`w-full max-w-xs mx-auto transition-opacity duration-500 ${isActive ? "opacity-100" : "opacity-0 pointer-events-none"}`}
    >
      <h2 className="text-2xl font-bold mb-6 text-center text-white">로그인</h2>
      <InputWithIcon icon={<Mail size={16} />} type="email" placeholder="이메일" />
      <InputWithIcon icon={<Lock size={16} />} type="password" placeholder="비밀번호" />
      <div className="flex items-center space-x-2 my-4">
        <Checkbox
          id="goToDashboard"
          checked={goToDashboard}
          onCheckedChange={(checked) => setGoToDashboard(Boolean(checked))}
          className="data-[state=checked]:bg-cyan-500"
        />
        <Label htmlFor="goToDashboard" className="text-sm font-medium leading-none text-white">
          로그인 후 대시보드로 바로가기
        </Label>
      </div>
      <Button type="submit" className="w-full bg-cyan-500 hover:bg-cyan-600 text-white h-12">
        로그인
      </Button>
    </form>
  )
}
