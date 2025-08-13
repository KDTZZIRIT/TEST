"use client"

import { memo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { InventoryItem } from "./utils"
import * as XLSX from 'xlsx'

interface InventoryButtonsProps {
  inventoryItems: InventoryItem[]
  setInventoryItems: (items: InventoryItem[]) => void
  selectedCategory: string
  onCategoryChange: (value: string) => void
  categories: string[]
}

const InventoryButtons = memo(function InventoryButtons({ 
  inventoryItems, 
  setInventoryItems,
  selectedCategory,
  onCategoryChange,
  categories
}: InventoryButtonsProps) {

         


         const handleExportToExcel = () => {
           try {
             // 엑셀에 포함할 데이터 준비
             const excelData = inventoryItems.map(item => {
               // 입고날짜 형식 변환 (YYYY-MM-DD)
               let formattedDate = item.receivedDate
               if (item.receivedDate) {
                 const date = new Date(item.receivedDate)
                 if (!isNaN(date.getTime())) {
                   formattedDate = date.toISOString().split('T')[0]
                 }
               }

               return {
                 'Part ID': item.partId,
                 '제품': item.product,
                 '종류': item.type,
                 'Size': item.size,
                 '입고날짜': formattedDate,
                 '흡습여부': item.moistureAbsorption ? 'O' : 'X',
                 '흡습필요자재': item.moistureMaterials,
                 '조치필요여부': item.actionRequired,
                 '제조사': item.manufacturer,
                 '재고': item.quantity,
                 '최소재고': item.minimumStock,
                 '주문 필요여부': item.orderRequired
               }
             })

             // 워크북 생성
             const workbook = XLSX.utils.book_new()
             const worksheet = XLSX.utils.json_to_sheet(excelData)

             // 열 너비 자동 조정
             const columnWidths = [
               { wch: 10 }, // Part ID
               { wch: 20 }, // 제품
               { wch: 15 }, // 종류
               { wch: 10 }, // Size
               { wch: 12 }, // 입고날짜
               { wch: 10 }, // 흡습여부
               { wch: 15 }, // 흡습필요자재
               { wch: 15 }, // 조치필요여부
               { wch: 15 }, // 제조사
               { wch: 8 },  // 재고
               { wch: 10 }, // 최소재고
               { wch: 15 }  // 주문 필요여부
             ]
             worksheet['!cols'] = columnWidths

             // 워크시트를 워크북에 추가
             XLSX.utils.book_append_sheet(workbook, worksheet, '부품재고현황')

             // 파일 다운로드
             const fileName = `부품재고현황_${new Date().toISOString().split('T')[0]}.xlsx`
             XLSX.writeFile(workbook, fileName)
           } catch (error) {
             console.error("엑셀 다운로드 중 오류 발생:", error)
           }
         }

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {/* 카테고리 선택 */}
      <div className="w-48">
        <Select value={selectedCategory} onValueChange={onCategoryChange}>
          <SelectTrigger className="bg-slate-800 border-slate-700 text-white h-10 px-4 py-2 text-sm">
            <SelectValue placeholder="카테고리 선택" />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-700">
            <SelectItem value="all" className="text-white hover:bg-slate-700">
              ALL
            </SelectItem>
            {categories.map((category) => (
              <SelectItem 
                key={category} 
                value={category}
                className="text-white hover:bg-slate-700"
              >
                {category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      <div className="ml-auto flex gap-2">
        <Button 
          onClick={handleExportToExcel}
          className="bg-slate-800 border border-slate-600 text-slate-300 hover:bg-slate-700 px-3 py-1 text-sm"
        >
          엑셀로 받기
        </Button>
      </div>
    </div>
  )
})

export default InventoryButtons 