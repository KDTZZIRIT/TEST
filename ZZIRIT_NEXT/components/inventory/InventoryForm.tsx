"use client"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { InventoryItem } from "./utils"

interface InventoryFormProps {
  showAddForm: boolean
  setShowAddForm: (show: boolean) => void
  newItem: Omit<InventoryItem, "id">
  setNewItem: (item: Omit<InventoryItem, "id"> | ((prev: Omit<InventoryItem, "id">) => Omit<InventoryItem, "id">)) => void
  onAddItem: () => void
}

export default function InventoryForm({ 
  showAddForm, 
  setShowAddForm, 
  newItem, 
  setNewItem, 
  onAddItem 
}: InventoryFormProps) {
  const [isLoading, setIsLoading] = useState(false)

  // ✅ 최적화된 핸들러 - newItem 의존성 제거
  const handleInputChange = useCallback(
    (field: keyof Omit<InventoryItem, "id">, value: any) => {
      setNewItem((prevItem: Omit<InventoryItem, "id">) => ({ ...prevItem, [field]: value }));
    },
    [setNewItem] // newItem 의존성 제거
  );

  const handleAddItem = async () => {
    // 필수 필드 검증
    if (!newItem.product || !newItem.type) {
      alert('제품명과 종류는 필수 입력 항목입니다.')
      return
    }

    setIsLoading(true)

    try {
      const payload = {
        product: newItem.product,
        type: newItem.type,
        size: newItem.size,
        receivedDate: newItem.receivedDate,
        moistureAbsorption: newItem.moistureAbsorption,
        moistureMaterials: newItem.moistureMaterials,
        manufacturer: newItem.manufacturer,
        quantity: newItem.quantity,
        minimumStock: newItem.minimumStock,
      }

      const response = await fetch("http://43.201.249.204:5000/api/user/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error('부품 추가에 실패했습니다.')
      }

      // ✅ 리스트 즉시 새로고침
      onAddItem();

      // 폼 초기화
      setNewItem({
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

      // 모달 닫기
      setShowAddForm(false)
      
      // 성공 알림
      // (toast가 있다면 여기에 추가)
      // toast.success("부품이 추가되었습니다.");

    } catch (error) {
      console.error('❌ 부품 추가 중 오류 발생:', error)
      alert('부품 추가 중 오류가 발생했습니다. 다시 시도해주세요.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={showAddForm} onOpenChange={setShowAddForm}>
      <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-4xl">
        <DialogHeader>
          <DialogTitle className="text-lg font-semibold">새 부품 추가</DialogTitle>
        </DialogHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">제품</label>
            <Input
              value={newItem.product}
              onChange={(e) => handleInputChange('product', e.target.value)}
              className="bg-slate-700 border-slate-600 text-white"
              placeholder="제품명을 입력하세요"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">종류</label>
            <select
              value={newItem.type}
              onChange={(e) => handleInputChange('type', e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="" className="bg-slate-700 text-slate-300">종류를 선택하세요</option>
              <option value="Capacitor" className="bg-slate-700 text-slate-300">Capacitor</option>
              <option value="Ferrite Bead" className="bg-slate-700 text-slate-300">Ferrite Bead</option>
              <option value="Inductor" className="bg-slate-700 text-slate-300">Inductor</option>
              <option value="Misc IC / Unknown" className="bg-slate-700 text-slate-300">Misc IC / Unknown</option>
              <option value="PMIC / Power IC" className="bg-slate-700 text-slate-300">PMIC / Power IC</option>
              <option value="RF Filter / Duplexer" className="bg-slate-700 text-slate-300">RF Filter / Duplexer</option>
              <option value="RF Front-End / PA" className="bg-slate-700 text-slate-300">RF Front-End / PA</option>
              <option value="Resistor" className="bg-slate-700 text-slate-300">Resistor</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Size</label>
            <select
              value={newItem.size}
              onChange={(e) => handleInputChange('size', e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="" className="bg-slate-700 text-slate-300">크기를 선택하세요</option>
              <option value="0402" className="bg-slate-700 text-slate-300">0402</option>
              <option value="0604" className="bg-slate-700 text-slate-300">0604</option>
              <option value="1008" className="bg-slate-700 text-slate-300">1008</option>
              <option value="2520" className="bg-slate-700 text-slate-300">2520</option>
              <option value="2015" className="bg-slate-700 text-slate-300">2015</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">흡습여부</label>
            <select
              value={newItem.moistureAbsorption ? "O" : "X"}
              onChange={(e) => handleInputChange('moistureAbsorption', e.target.value === "O")}
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="X" className="bg-slate-700 text-slate-300">X</option>
              <option value="O" className="bg-slate-700 text-slate-300">O</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">흡습필요자재</label>
            <select
              value={newItem.moistureMaterials}
              onChange={(e) => handleInputChange('moistureMaterials', e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="" className="bg-slate-700 text-slate-300">선택하세요</option>
              <option value="불필요" className="bg-slate-700 text-slate-300">불필요</option>
              <option value="필요" className="bg-slate-700 text-slate-300">필요</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">제조사</label>
            <select
              value={newItem.manufacturer}
              onChange={(e) => handleInputChange('manufacturer', e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="" className="bg-slate-700 text-slate-300">제조사를 선택하세요</option>
              <option value="samsung" className="bg-slate-700 text-slate-300">samsung</option>
              <option value="murata" className="bg-slate-700 text-slate-300">murata</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">재고</label>
            <Input
              type="number"
              value={newItem.quantity === 0 ? "" : newItem.quantity}
              onChange={(e) => handleInputChange('quantity', Number.parseInt(e.target.value) || 0)}
              className="bg-slate-700 border-slate-600 text-white [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              placeholder="재고 수량을 입력하세요"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">최소재고</label>
            <Input
              type="number"
              value={newItem.minimumStock === 0 ? "" : newItem.minimumStock}
              onChange={(e) => handleInputChange('minimumStock', Number.parseInt(e.target.value) || 0)}
              className="bg-slate-700 border-slate-600 text-white [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              placeholder="최소재고 수량을 입력하세요"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">입고날짜</label>
            <Input
              type="date"
              value={newItem.receivedDate}
              onChange={(e) => handleInputChange('receivedDate', e.target.value)}
              className="bg-slate-700 border-slate-600 text-white"
            />
          </div>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={handleAddItem} 
            disabled={isLoading}
            className="bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-600"
          >
            {isLoading ? '추가 중...' : '추가'}
          </Button>
          <Button
            onClick={() => setShowAddForm(false)}
            variant="outline"
            disabled={isLoading}
            className="bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
          >
            취소
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
} 