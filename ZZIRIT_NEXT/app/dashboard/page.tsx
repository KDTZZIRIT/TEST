"use client"

import type React from "react"
import { useState, type FC } from "react"
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
  const router = useRouter()

  const handleLogout = () => {
    localStorage.removeItem("auth-token")
    router.push("/")
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
