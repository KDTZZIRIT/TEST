"use client"

import { memo } from "react"
import { MoreHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { getStatusBadge } from "./utils"

export interface InventoryItem {
  id: number | string
  partId: number | string
  product: string
  type: string
  size: string
  receivedDate: string
  moistureAbsorption: boolean
  moistureMaterials: string
  actionRequired: string
  manufacturer: string
  quantity: number
  minimumStock: number
  orderRequired: string
}

interface InventoryTableProps {
  data: InventoryItem[]
}


const InventoryTable = memo(function InventoryTable({ data }: InventoryTableProps) {
  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
      <div className="relative h-[600px] overflow-hidden">
        {/* 테이블 헤더 */}
        <Table className="table-fixed w-full">
          <TableHeader className="sticky top-0 z-20 bg-slate-800 border-b border-slate-700">
            <TableRow className="border-slate-700 hover:bg-slate-700/50">
              <TableHead className="text-slate-300 font-medium w-[100px] text-left bg-slate-800">Part ID</TableHead>
              <TableHead className="text-slate-300 font-medium w-[120px] text-left bg-slate-800">제품</TableHead>
              <TableHead className="text-slate-300 font-medium w-[80px] text-center bg-slate-800">종류</TableHead>
              <TableHead className="text-slate-300 font-medium w-[80px] text-center bg-slate-800">Size</TableHead>
              <TableHead className="text-slate-300 font-medium w-[100px] text-center bg-slate-800">입고날짜</TableHead>
              <TableHead className="text-slate-300 font-medium w-[80px] text-center bg-slate-800">흡습여부</TableHead>
              <TableHead className="text-slate-300 font-medium w-[100px] text-center bg-slate-800">흡습필요자재</TableHead>
              <TableHead className="text-slate-300 font-medium w-[100px] text-center bg-slate-800">조치필요여부</TableHead>
              <TableHead className="text-slate-300 font-medium w-[100px] text-center bg-slate-800">제조사</TableHead>
              <TableHead className="text-slate-300 font-medium w-[80px] text-center bg-slate-800">재고</TableHead>
              <TableHead className="text-slate-300 font-medium w-[80px] text-center bg-slate-800">최소재고</TableHead>
              <TableHead className="text-slate-300 font-medium w-[100px] text-center bg-slate-800">주문 필요여부</TableHead>
              <TableHead className="text-slate-300 font-medium w-[100px] text-center bg-slate-800">기타</TableHead>
            </TableRow>
          </TableHeader>
        </Table>

        {/* 테이블 바디 */}
        <div className="h-[calc(600px-57px)] overflow-y-auto overflow-x-auto no-scrollbar">
          <Table className="table-fixed w-full">
            <TableBody>
              {data.map((item) => (
                <TableRow
                key={item.id}
                  className="border-slate-700 hover:bg-slate-700/30"
                >
                  <TableCell className="font-medium text-white w-[100px]">
                    <div className="truncate" title={item.partId?.toString() || ""}>
                      {item.partId ?? "-"}
                    </div>
                  </TableCell>
                  <TableCell className="font-medium text-white w-[120px]">
                    <div className="truncate" title={item.product || ""}>
                      {item.product || "-"}
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300 w-[80px] text-center">
                    <div className="truncate" title={item.type || ""}>
                      {item.type || "-"}
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300 w-[80px] text-center">
                    <div className="truncate" title={item.size || ""}>
                      {item.size || "-"}
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300 w-[100px] text-center">
                    <div
                      className="truncate"
                      title={item.receivedDate ? item.receivedDate.slice(0, 10) : "-"}
                    >
                      {item.receivedDate ? item.receivedDate.slice(0, 10) : "-"}
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300 w-[80px] text-center">
                    <div className="truncate" title={item.moistureAbsorption ? "O" : "X"}>
                      {item.moistureAbsorption ? "O" : "X"}
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300 w-[100px] text-center">
                    <div className="truncate" title={item.moistureMaterials || ""}>
                      {item.moistureMaterials || "-"}
                    </div>
                  </TableCell>
                  <TableCell className="w-[100px] text-center">
                    {getStatusBadge(item.actionRequired)}
                  </TableCell>
                  <TableCell className="text-slate-300 w-[100px] text-center">
                    <div className="truncate" title={item.manufacturer || ""}>
                      {item.manufacturer || "-"}
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300 font-medium w-[80px] text-center">
                    <div className="truncate" title={item.quantity?.toString() || "-"}>
                      {item.quantity ?? "-"}
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-300 w-[80px] text-center">
                    <div className="truncate" title={item.minimumStock?.toString() || "-"}>
                      {item.minimumStock ?? "-"}
                    </div>
                  </TableCell>
                  <TableCell className="w-[100px] text-center">
                    <div className="truncate" title={item.orderRequired || ""}>
                      {item.orderRequired || "-"}
                    </div>
                  </TableCell>
                  <TableCell className="w-[100px] text-center">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          className="h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-slate-700"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
                        <DropdownMenuItem className="text-slate-300 hover:bg-slate-700 hover:text-white cursor-pointer">
                          수정
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-slate-300 hover:bg-slate-700 hover:text-white cursor-pointer">
                          삭제
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-slate-300 hover:bg-slate-700 hover:text-white cursor-pointer">
                          상세보기
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
})

export default InventoryTable
