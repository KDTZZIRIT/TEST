"use client"

import React, { useEffect, useRef, useState } from "react"
import { motion, useAnimation, useInView } from "framer-motion"
import { FileText, Search, FlaskConical, Cpu, BarChart2, User, Database } from "lucide-react"

// 각 단계를 정의합니다.
const nodes = [
  { id: "actor", label: "Actor", icon: <User size={32} /> },
  { id: "request", label: "발주 요청", icon: <FileText size={32} /> },
  { id: "inventory", label: "재고 조회", icon: <Search size={32} /> },
  { id: "flask", label: "Flask 연동", icon: <FlaskConical size={32} /> },
  { id: "ai", label: "AI 모델 연동", icon: <Cpu size={32} /> },
  { id: "frontend", label: "프론트엔드 데이터 표시", icon: <BarChart2 size={32} /> },
]

// 각 단계를 표시하는 컴포넌트입니다.
const ProcessNode = React.forwardRef<HTMLDivElement, { node: any; isActor?: boolean; controls?: any }>(
  ({ node, isActor = false, controls }, ref) => (
    <div ref={ref} className="flex flex-col items-center text-center z-10">
      <motion.div
        animate={controls}
        className={`w-24 h-24 rounded-full flex items-center justify-center ${
          isActor ? "bg-gray-700 text-cyan-400" : "bg-cyan-900/50 border-2 border-cyan-500 text-cyan-300"
        }`}
      >
        {node.icon}
      </motion.div>
      <span className="mt-2 font-semibold w-28">{node.label}</span>
    </div>
  ),
)
ProcessNode.displayName = "ProcessNode"

// 메인 컴포넌트입니다.
export default function DevProcess() {
  const containerRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(containerRef, { once: true, amount: 0.5 })

  const nodeRefs = useRef<React.RefObject<HTMLDivElement>[]>(nodes.map(() => React.createRef()))
  const flyingIconControls = useAnimation()
  const searchIconControls = useAnimation()
  const lineControls = useAnimation()

  const [flyingIcon, setFlyingIcon] = useState<React.ReactNode>(null)

  useEffect(() => {
    if (isInView) {
      const animateSequence = async () => {
        const getPos = (index: number) => {
          const el = nodeRefs.current[index].current
          if (!el || !containerRef.current) return { x: 0, y: 0 }
          const containerRect = containerRef.current.getBoundingClientRect()
          const elRect = el.getBoundingClientRect()
          return {
            x: elRect.left - containerRect.left + elRect.width / 2,
            y: elRect.top - containerRect.top + elRect.height / 2,
          }
        }

        // 시퀀스 시작 전 잠시 대기
        await new Promise((res) => setTimeout(res, 500))

        // 1. Actor -> 발주 요청 (데이터 아이콘)
        setFlyingIcon(<Database size={24} className="text-cyan-300" />)
        const pos0 = getPos(0)
        const pos1 = getPos(1)
        await flyingIconControls.start({
          x: [pos0.x, (pos0.x + pos1.x) / 2, pos1.x],
          y: [pos0.y, pos0.y - 80, pos1.y],
          opacity: [0, 1, 1, 0],
          scale: [0.5, 1, 1, 0.5],
          transition: { duration: 1.2, ease: "easeInOut", times: [0, 0.1, 0.9, 1] },
        })

        // 2. 발주 요청 -> 재고 조회 (파일 아이콘)
        setFlyingIcon(<FileText size={24} className="text-cyan-300" />)
        const pos2 = getPos(2)
        await flyingIconControls.start({
          x: [pos1.x, (pos1.x + pos2.x) / 2, pos2.x],
          y: [pos1.y, pos1.y - 80, pos2.y],
          opacity: [0, 1, 1, 0],
          scale: [0.5, 1, 1, 0.5],
          transition: { duration: 1.2, ease: "easeInOut", times: [0, 0.1, 0.9, 1] },
        })

        // 3. 재고 조회 (돋보기 애니메이션)
        await searchIconControls.start({
          rotate: [0, -15, 15, -15, 15, 0],
          transition: { duration: 3, ease: "easeInOut" },
        })

        // 4. 재고 조회 -> Flask 연동 (데이터 아이콘)
        setFlyingIcon(<Database size={24} className="text-cyan-300" />)
        const pos3 = getPos(3)
        await flyingIconControls.start({
          x: [pos2.x, (pos2.x + pos3.x) / 2, pos3.x],
          y: [pos2.y, pos2.y - 80, pos3.y],
          opacity: [0, 1, 1, 0],
          scale: [0.5, 1, 1, 0.5],
          transition: { duration: 1.2, ease: "easeInOut", times: [0, 0.1, 0.9, 1] },
        })

        // 5. Flask -> AI (전류 애니메이션)
        await lineControls.start({
          pathLength: [0, 1, 1, 0],
          transition: { duration: 1.2, ease: "easeInOut", times: [0, 0.2, 0.8, 1] },
        })

        // 6. AI -> Frontend (그래프 아이콘)
        setFlyingIcon(<BarChart2 size={24} className="text-cyan-300" />)
        const pos4 = getPos(4)
        const pos5 = getPos(5)
        await flyingIconControls.start({
          x: [pos4.x, (pos4.x + pos5.x) / 2, pos5.x],
          y: [pos4.y, pos4.y - 80, pos5.y],
          opacity: [0, 1, 1, 0],
          scale: [0.5, 1, 1, 0.5],
          transition: { duration: 1.2, ease: "easeInOut", times: [0, 0.1, 0.9, 1] },
        })
      }
      animateSequence()
    }
  }, [isInView, flyingIconControls, searchIconControls, lineControls])

  return (
    <div className="w-full flex justify-center py-12">
      <div ref={containerRef} className="w-full max-w-7xl relative">
        <motion.div className="absolute z-20" style={{ x: -12, y: -12, opacity: 0 }} animate={flyingIconControls}>
          {flyingIcon}
        </motion.div>

        <div className="w-full flex justify-between items-center">
          {nodes.map((node, index) => (
            <React.Fragment key={node.id}>
              <ProcessNode
                ref={nodeRefs.current[index]}
                node={node}
                isActor={index === 0}
                controls={index === 2 ? searchIconControls : undefined}
              />
              {index < nodes.length - 1 && (
                <div className="flex-1 h-0.5 bg-gray-600 relative mx-2">
                  {index === 3 && (
                    <svg className="absolute w-full h-full top-0 left-0 overflow-visible" style={{ y: "-50%" }}>
                      <defs>
                        <linearGradient id="electric-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#22d3ee" stopOpacity="0" />
                          <stop offset="50%" stopColor="#22d3ee" stopOpacity="1" />
                          <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
                        </linearGradient>
                      </defs>
                      <motion.line
                        x1="0"
                        y1="50%"
                        x2="100%"
                        y2="50%"
                        stroke="url(#electric-gradient)"
                        strokeWidth="3"
                        initial={{ pathLength: 0 }}
                        animate={lineControls}
                      />
                    </svg>
                  )}
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  )
}
