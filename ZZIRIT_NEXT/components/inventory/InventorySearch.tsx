"use client"

import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"

interface InventorySearchProps {
  searchTerm: string
  onSearchChange: (value: string) => void
}

export default function InventorySearch({ searchTerm, onSearchChange }: InventorySearchProps) {
  return (
    <div className="relative w-96">
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
      <Input
        placeholder="검색..."
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        className="pl-10 bg-slate-800 border-slate-700 text-white placeholder:text-slate-400"
      />
    </div>
  )
} 