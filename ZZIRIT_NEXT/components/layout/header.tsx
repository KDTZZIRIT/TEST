"use client"

import Link from "next/link"
import { useState, useEffect } from "react"
import { CircuitBoard } from "lucide-react"
import { cn } from "@/lib/utils"
import UserProfileDropdown from "@/components/user-profile-dropdown"
import NotificationDropdown from "@/components/notification-dropdown"

interface HeaderProps {
  isLoggedIn?: boolean
  onLogout?: () => void
}

export default function Header({ isLoggedIn = false, onLogout }: HeaderProps) {
  const [hasScrolled, setHasScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setHasScrolled(window.scrollY > 10)
    }
    // This assumes the main element is the scroll container
    const scrollContainer = document.querySelector("main")
    if (scrollContainer) {
      scrollContainer.addEventListener("scroll", handleScroll)
      return () => scrollContainer.removeEventListener("scroll", handleScroll)
    }
  }, [])

  return (
    <header
      className={cn(
        "fixed top-0 left-0 w-full z-50 transition-all duration-300",
        hasScrolled ? "bg-[#101629] shadow-lg" : "bg-transparent",
      )}
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          <Link href="/" className="flex items-center gap-3 text-2xl font-bold">
            <CircuitBoard className="w-10 h-10 text-cyan-400" />
            <span>PCB-Manager</span>
          </Link>

          {/* 우측 사용자 메뉴 */}
          {isLoggedIn && (
            <div className="flex items-center gap-4">
              <NotificationDropdown isLoggedIn={isLoggedIn} />
              <UserProfileDropdown isLoggedIn={isLoggedIn} onLogout={onLogout || (() => {})} />
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
