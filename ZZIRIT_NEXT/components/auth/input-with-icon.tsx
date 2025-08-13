"use client"

import { Input } from "@/components/ui/input"
import type { ReactNode } from "react"

interface InputWithIconProps {
  icon: ReactNode
  [key: string]: any
}

export default function InputWithIcon({ icon, ...props }: InputWithIconProps) {
  return (
    <div className="relative mb-4">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
        {icon}
      </div>
      <Input
        className="pl-10 bg-gray-800/50 border-gray-700 h-12 placeholder:text-gray-400"
        {...props}
      />
    </div>
  )
}
