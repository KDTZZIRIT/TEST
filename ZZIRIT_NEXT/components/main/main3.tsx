"use client"

import { motion } from "framer-motion"
import { ScanLine, FileText, Archive } from "lucide-react"

const processSteps = [
  { icon: <ScanLine size={32} />, name: "PCB 분석" },
  { icon: <FileText size={32} />, name: "결과 리포트" },
  { icon: <Archive size={32} />, name: "데이터 저장" },
]

export default function ProcessSection() {
  return (
    <section className="w-full">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">자동화된 분석 프로세스</h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            컨베이어 벨트 위에서 진행되는 PCB 기판의 분석, 결과 도출, 저장까지의 전 과정을 시각화합니다.
          </p>
        </div>
        <div className="relative w-full h-40 flex items-center justify-center overflow-hidden">
          {/* Conveyor Belt */}
          <div className="absolute w-full h-2 bg-gray-700 rounded-full" />
          <div className="absolute w-full h-12 bg-gray-800/50 top-1/2 -translate-y-1/2" />

          {/* PCB Motion */}
          <motion.div
            className="absolute w-20 h-20 bg-green-900 border-2 border-yellow-300 rounded-md flex items-center justify-center"
            animate={{
              x: ["-20vw", "20vw"],
            }}
            transition={{
              duration: 5,
              ease: "easeInOut",
              repeat: Number.POSITIVE_INFINITY,
              repeatType: "mirror",
            }}
          >
            <div className="w-4 h-4 bg-gray-700 rounded-sm" />
          </motion.div>

          {/* Process Steps */}
          <div className="relative flex justify-between w-full max-w-3xl">
            {processSteps.map((step, index) => (
              <div key={index} className="flex flex-col items-center gap-2 text-center">
                <div className="w-16 h-16 rounded-full bg-cyan-900/50 border-2 border-cyan-500 flex items-center justify-center text-cyan-400">
                  {step.icon}
                </div>
                <p className="font-semibold">{step.name}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
