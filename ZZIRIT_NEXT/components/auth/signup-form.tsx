"use client"

import type React from "react"
import { Button } from "@/components/ui/button"
import InputWithIcon from "@/components/auth/input-with-icon"
import { Mail, Lock, User, Briefcase, Building } from "lucide-react"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

export default function SignUpForm({
  isActive,
  onSignupSuccess,
}: {
  isActive: boolean
  onSignupSuccess: () => void
}) {
  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault()
    // 여기에 실제 회원가입 API 호출 로직을 추가합니다.
    // 성공 시 onSignupSuccess() 호출
    console.log("회원가입 시도")
    onSignupSuccess()
  }

  return (
    <form
      onSubmit={handleSignup}
      className={`w-full max-w-xs mx-auto transition-opacity duration-500 ${isActive ? "opacity-100 pointer-events-auto" : "opacity-20 pointer-events-none"}`}
      tabIndex={isActive ? 0 : -1}
    >
      <h2 className="text-2xl font-bold mb-6 text-center text-white">회원가입</h2>
      <InputWithIcon icon={<User size={16} />} placeholder="이름" />
      <InputWithIcon icon={<Mail size={16} />} type="email" placeholder="이메일" />
      <InputWithIcon icon={<Building size={16} />} placeholder="회사명" />
      <Select>
        <SelectTrigger className="w-full bg-gray-800/50 border-gray-700 h-12 mb-4">
          <div className="flex items-center gap-2 text-gray-400">
            <Briefcase size={16} />
            <SelectValue placeholder="직무 선택" />
          </div>
        </SelectTrigger>
        <SelectContent className="bg-[#101629] text-white border-gray-700">
          <SelectItem value="engineer">엔지니어</SelectItem>
          <SelectItem value="manager">관리자</SelectItem>
          <SelectItem value="operator">오퍼레이터</SelectItem>
        </SelectContent>
      </Select>
      <InputWithIcon icon={<Lock size={16} />} type="password" placeholder="비밀번호" />
      <InputWithIcon icon={<Lock size={16} />} type="password" placeholder="비밀번호 확인" />
      <div className="flex items-center space-x-2 my-4 bg-gray-800/30 p-3 rounded-lg border border-gray-600/50">
        <Checkbox id="terms" className="data-[state=checked]:bg-cyan-500" />
        <Label htmlFor="terms" className="text-xs text-gray-200 leading-relaxed">
          <a href="#" className="underline hover:text-cyan-400 text-cyan-300">
            이용약관
          </a>{" "}
          및{" "}
          <a href="#" className="underline hover:text-cyan-400 text-cyan-300">
            개인정보처리방침
          </a>
          에 동의합니다.
        </Label>
      </div>
      <Button type="submit" className="w-full bg-cyan-500 hover:bg-cyan-600 text-white h-12">
        계정 생성
      </Button>
    </form>
  )
}
