import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import UserProfileDropdown from "@/components/user-profile-dropdown"
import NotificationDropdown from "@/components/notification-dropdown"
import ChatbotModal from "@/components/chatbot/ChatbotModal"
import {
  Cpu,
  Search,
  LayoutDashboard,
  ClipboardList,
  AlertTriangle,
  Package,
  Activity,
  Clock,
  AlertCircle,
  Bot,
  CircuitBoard,
  Zap,
  Brain,
  BotMessageSquare,
} from "lucide-react"

interface HeaderProps {
  activeTab: string
  setActiveTab: (tab: string) => void
  searchTerm: string
  setSearchTerm: (term: string) => void
  isLoggedIn?: boolean
  onLogout?: () => void
}

const Header = ({ activeTab, setActiveTab, searchTerm, setSearchTerm, isLoggedIn = true, onLogout }: HeaderProps) => {
  const router = useRouter()
  const [isSearchVisible, setIsSearchVisible] = useState(false)
  const [isChatbotOpen, setIsChatbotOpen] = useState(false)

  const handleLogoClick = () => {
    router.push("/")
  }

  const handleAIAssistClick = () => {
    setIsChatbotOpen(true)
  }

  return (
    <>
      <header className="bg-[#161B22]/80 backdrop-blur-xl border-b border-[#30363D] p-4 sticky top-0 z-40">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div 
              className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity duration-200"
              onClick={handleLogoClick}
            >
              <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center shadow-lg">
                <Cpu className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-white">PCB-Manager</span>
            </div>
            <nav className="flex items-center gap-2 p-1 bg-[#0D1117]/50 backdrop-blur-sm rounded-lg border border-[#30363D]">
              {[
                { id: "overview", label: "PCB Monitor", sublabel: "(PCB 모니터링)", icon: CircuitBoard },
                { id: "defects", label: "Inspection", sublabel: "(불량검사)", icon: Zap },
                { id: "analytics", label: "Management", sublabel: "(불량관리)", icon: AlertTriangle },
                { id: "inventory", label: "Component", sublabel: "(부품재고관리)", icon: Package },
                { id: "mes", label: "MEMS", sublabel: "(공정환경 모니터링)", icon: Activity },
              ].map(({ id, label, sublabel, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-200 ${
                    activeTab === id
                      ? "bg-gradient-to-r from-blue-600/20 to-blue-700/20 text-white border border-blue-500/30 shadow-lg"
                      : "text-gray-400 hover:bg-[#21262D]/50 hover:text-white"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <div className="flex flex-col items-center">
                    <span>{label}</span>
                    {sublabel && <span className="text-xs opacity-70">{sublabel}</span>}
                  </div>
                </button>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            {/* 검색 기능 */}
            <div className="flex items-center gap-2">
              {isSearchVisible && (
                <Input
                  placeholder="검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-64 bg-[#0D1117]/50 backdrop-blur-sm border-[#30363D] rounded-lg text-sm focus:ring-2 focus:ring-blue-500/50"
                  onBlur={() => setIsSearchVisible(false)}
                  autoFocus
                />
              )}
              <button
                onClick={() => setIsSearchVisible(!isSearchVisible)}
                className="p-2 hover:bg-[#21262D]/50 rounded-lg transition-colors duration-200"
              >
                <Search className="w-5 h-5 text-gray-400 hover:text-white transition-colors" />
              </button>
            </div>

            {/* AI 어시스트 버튼 */}
            <Button
              onClick={handleAIAssistClick}
              variant="ghost"
              size="sm"
              className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-purple-600/20 to-blue-600/20 hover:from-purple-600/30 hover:to-blue-600/30 border border-purple-500/30 hover:border-purple-500/50 text-white rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              <BotMessageSquare className="w-4 h-4" />
              <span className="text-sm font-medium">AI 어시스트</span>
            </Button>

            {/* 알림과 프로필 드롭다운 */}
            <div className="flex items-center gap-2">
              <NotificationDropdown isLoggedIn={isLoggedIn} />
              <UserProfileDropdown isLoggedIn={isLoggedIn} onLogout={onLogout || (() => {})} />
            </div>
          </div>
        </div>
      </header>

      {/* 챗봇 모달 */}
      <ChatbotModal 
        isOpen={isChatbotOpen} 
        onClose={() => setIsChatbotOpen(false)}
        currentMenu={activeTab}
      />
    </>
  )
}

export default Header

