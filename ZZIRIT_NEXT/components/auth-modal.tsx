"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogClose, DialogTitle } from "@/components/ui/dialog"
import AuthSliderPanel from "@/components/auth/auth-slider-panel"
import { X } from "lucide-react"

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  initialMode: "login" | "signup"
  onLoginSuccess: () => void
}

export default function AuthModal({ isOpen, onClose, initialMode, onLoginSuccess }: AuthModalProps) {
  const [mode, setMode] = useState(initialMode)

  useEffect(() => {
    if (isOpen) {
      setMode(initialMode)
    }
  }, [isOpen, initialMode])

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="w-auto max-w-none p-0 border-0 bg-transparent shadow-none">
        <DialogTitle className="sr-only">
          {mode === "login" ? "로그인" : "회원가입"}
        </DialogTitle>
        <AuthSliderPanel mode={mode} setMode={setMode} onLoginSuccess={onLoginSuccess} />
        <DialogClose className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground z-30">
          <X className="h-6 w-6 text-white" />
          <span className="sr-only">Close</span>
        </DialogClose>
      </DialogContent>
    </Dialog>
  )
}
