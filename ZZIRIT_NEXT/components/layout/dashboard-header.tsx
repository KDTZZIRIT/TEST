"use client"

import { Button } from "@/components/ui/button"
import { User, Bell } from "lucide-react"
import { useRouter } from "next/navigation"

export default function DashboardHeader() {
  const router = useRouter()

  const handleLogout = () => {
    localStorage.removeItem("auth-token")
    router.push("/")
  }

  return (
    <header className="bg-[#101629] border-b border-gray-800 p-4 flex justify-end items-center">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon">
          <Bell className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon">
          <User className="h-5 w-5" />
        </Button>
        <Button onClick={handleLogout} variant="outline" className="border-cyan-500 text-cyan-500 bg-transparent">
          로그아웃
        </Button>
      </div>
    </header>
  )
}
