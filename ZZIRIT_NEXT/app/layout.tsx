import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "PCB-Manager - 차세대 PCB 제조 관리 솔루션",
  description: "복잡한 PCB 제조 공정을 한 곳에서, 스마트한 관리, 효율적인 생산을 경험하세요.",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
