import { ShieldCheck, Cpu, BarChart3 } from "lucide-react"

const features = [
  {
    icon: <Cpu className="w-10 h-10 text-cyan-400" />,
    title: "AI 기반 불량 분석",
    description: "CNN 머신러닝 모델이 PCB 이미지를 실시간으로 분석하여 미세한 결함까지 정확하게 감지합니다.",
  },
  {
    icon: <BarChart3 className="w-10 h-10 text-cyan-400" />,
    title: "스마트 재고 관리",
    description: "부품 수명 예측 알고리즘을 통해 최적의 재고를 유지하고, 자동 발주 시스템으로 관리 비용을 절감합니다.",
  },
  {
    icon: <ShieldCheck className="w-10 h-10 text-cyan-400" />,
    title: "통합 대시보드",
    description: "생산 현황, 불량률, 재고 상태 등 모든 데이터를 한눈에 파악하고 신속한 의사결정을 지원합니다.",
  },
]

export default function FeaturesSection() {
  return (
    <section className="bg-transparent">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">주요 기능</h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            PCB-Manager는 최신 기술을 통합하여 제조 공정의 효율성을 극대화합니다.
          </p>
        </div>
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-[#0A0E1A] p-8 rounded-lg text-center border border-gray-800 hover:border-cyan-500 transition-colors"
            >
              <div className="flex justify-center mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
