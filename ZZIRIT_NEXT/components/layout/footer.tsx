import { CircuitBoard } from "lucide-react"

export default function Footer() {
  return (
    <footer className="absolute bottom-0 left-0 w-full bg-[#101629] border-t border-gray-800">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center text-gray-500">
        <div className="flex items-center justify-center gap-2 mb-2">
          <CircuitBoard className="w-6 h-6 text-cyan-400" />
          <span className="font-bold text-lg text-white">PCB-Manager</span>
        </div>
        <p>&copy; {new Date().getFullYear()} PCB-Manager. All rights reserved.</p>
      </div>
    </footer>
  )
}
