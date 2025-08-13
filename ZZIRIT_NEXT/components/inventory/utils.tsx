import { Badge } from "@/components/ui/badge"

export interface InventoryItem {
  id: string
  partId: string
  product: string
  type: string
  size: string
  receivedDate: string
  moistureAbsorption: boolean
  moistureMaterials: string
  actionRequired: "-" | "필요"
  manufacturer: string
  quantity: number
  minimumStock: number
  orderRequired: string
}

export const getStatusBadge = (status: string) => {
  return <Badge className="bg-transparent text-slate-300 border-transparent">{status}</Badge>
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const yyyy = date.getFullYear()
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const dd = String(date.getDate()).padStart(2, '0')
  return `${yyyy}.${mm}.${dd}`
}

export const initialInventoryData: InventoryItem[] = [
  
] 