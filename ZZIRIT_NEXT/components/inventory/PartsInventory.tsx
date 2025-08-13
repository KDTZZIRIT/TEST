"use client"

import { useState, useEffect, useCallback, useMemo } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { toast, Toaster } from "sonner"
import { InventoryItem, initialInventoryData } from "./utils"
import InventorySearch from "./InventorySearch"
import InventoryForm from "./InventoryForm"
import InventoryTable from "./InventoryTable"
import InventoryButtons from "./InventoryButtons"


export default function PartsInventory() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [showAddForm, setShowAddForm] = useState(false)
  const [inventoryItems, setInventoryItems] = useState<InventoryItem[]>([])
  const [newItem, setNewItem] = useState<Omit<InventoryItem, "id">>({
    partId: "",
    product: "",
    type: "",
    size: "",
    receivedDate: "",
    moistureAbsorption: false,
    moistureMaterials: "불필요",
    actionRequired: "-",
    manufacturer: "",
    quantity: 0,
    minimumStock: 0,
    orderRequired: "-",
  })

  // ✅ useCallback으로 setNewItem 최적화
  const handleSetNewItem = useCallback((item: Omit<InventoryItem, "id"> | ((prev: Omit<InventoryItem, "id">) => Omit<InventoryItem, "id">)) => {
    setNewItem(item)
  }, [])

  // ✅ 공통 fetch 함수 정의
  const fetchInventoryItems = useCallback(async () => {
    try {
      const response = await fetch("http://43.201.249.204:5000/api/user/pcb-parts")
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()

      const mapped = data.map((row: any) => ({
        id: row.id || `part-${row.part_id ?? `${Date.now()}-${Math.random()}`}`,
        partId: row.partId || row.part_id || -1,
        product: row.product || row.part_number || "",
        type: row.type || row.category || "",
        size: row.size || "",
        receivedDate: row.receivedDate || row.received_date || "",
        moistureAbsorption: row.moistureAbsorption || false,
        moistureMaterials: row.moistureMaterials || "불필요",
        actionRequired: row.actionRequired || "-",
        manufacturer: row.manufacturer || "",
        quantity: row.quantity || 0,
        minimumStock: row.minimumStock || row.min_stock || 0,
        orderRequired: row.orderRequired || "-",
      }));

      setInventoryItems(mapped)
    } catch (error) {
      console.error("📛 백엔드 API 연결 실패:", error)
      setInventoryItems([])
      throw error // 에러를 다시 던져서 상위 컴포넌트에서 처리할 수 있도록 함
    }
  }, [])

  // ✅ URL 파라미터에서 카테고리 읽어오기
  useEffect(() => {
    const categoryFromUrl = searchParams.get('category')
    if (categoryFromUrl) {
      setSelectedCategory(categoryFromUrl)
      console.log("🔗 URL에서 카테고리 자동 선택:", categoryFromUrl)
    }
  }, [searchParams])

  // ✅ 최초 로딩 시 fetch
  useEffect(() => {
    fetchInventoryItems()
  }, [fetchInventoryItems])

  // ✅ 모달에서 부품 추가 후 재요청
  const handleAddItem = useCallback(() => {
    fetchInventoryItems() // 동일한 fetch 함수 재사용
  }, [fetchInventoryItems])

  // ✅ useMemo로 필터링된 데이터 최적화
  const filteredData = useMemo(() => {
    return inventoryItems.filter(
      (item) => {
        const term = searchTerm.toLowerCase()
        const matchesSearch = (
          item.product?.toLowerCase().includes(term) ||
          item.type?.toLowerCase().includes(term) ||
          item.manufacturer?.toLowerCase().includes(term)
        )
        
        const matchesCategory = selectedCategory === "all" || item.type === selectedCategory
        
        return matchesSearch && matchesCategory
      }
    )
  }, [inventoryItems, searchTerm, selectedCategory])

  // ✅ 카테고리 목록 추출
  const categories = useMemo(() => {
    const uniqueCategories = [...new Set(inventoryItems.map(item => item.type).filter(Boolean))]
    return uniqueCategories.sort()
  }, [inventoryItems])

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <Toaster position="top-right" richColors />
      {/* Main Content */}
      <div className="p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <InventorySearch 
            searchTerm={searchTerm} 
            onSearchChange={setSearchTerm}
          />
        </div>

        {/* Title Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-16">
            <h1 className="text-2xl font-bold">부품 재고 현황</h1>
            <Button className="bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-600" onClick={() => setShowAddForm(true)}>
              <Plus className="w-4 h-4 mr-2" />새 부품 추가
            </Button>
          </div>

          {/* Quick Decrease Buttons */}
          <InventoryButtons 
            inventoryItems={inventoryItems}
            setInventoryItems={setInventoryItems}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            categories={categories}
          />
        </div>

        {/* Add Item Dialog */}
        <InventoryForm
          showAddForm={showAddForm}
          setShowAddForm={setShowAddForm}
          newItem={newItem}
          setNewItem={handleSetNewItem}
          onAddItem={handleAddItem}
        />

        {/* Inventory Table */}
        <InventoryTable data={filteredData} />
      </div>
    </div>
  )
}