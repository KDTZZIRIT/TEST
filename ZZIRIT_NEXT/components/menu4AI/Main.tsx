"use client"

import React, { useEffect, useMemo, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Bot,
  CheckCircle2,
  Cpu,
  Database,
  Loader2,
  TriangleAlert,
} from "lucide-react"

const API =
  typeof window !== "undefined"
    ? `${window.location.protocol}//${window.location.hostname}:5200`  // 포트 5200으로 수정
    : "http://localhost:5200";

type PredictItem = {
  part_id: number
  category: string
  size: string
  manufacturer: string
  today_usage: number
  opening_stock: number
  predicted_order_qty: number
  predicted_days_to_depletion: number
  warning: boolean
  recommendations_top3?: Array<{ day_offset: number; quantity: number; expected_total_cost: number }>
  predicted_best_order_day?: number
  best_day_top3?: Array<{ day_offset: number; prob: number }>
}

type PredictResponse = {
  generated_at: string
  n_parts: number
  items: PredictItem[]
  summary: { categories?: Array<{ category: string; days_possible: number | null }> }
}

type ModelState = "loading" | "ok" | "error"

export default function Main() {
  // ──────────────────────────────────────────────────────────────────────────────
  // 상태
  // ──────────────────────────────────────────────────────────────────────────────
  const [modelMeta, setModelMeta] = useState<any>(null)
  const [modelState, setModelState] = useState<ModelState>("loading")
  const [modelWarming, setModelWarming] = useState<boolean>(true) // 가용 준비 중 오버레이
  const modelPollRef = useRef<NodeJS.Timeout | null>(null)

  const [data, setData] = useState<PredictResponse | null>(null)
  const [predicting, setPredicting] = useState(false) // 버튼 비활성/상태 가드

  // 새 예측 오버레이(큰 로딩 + 체크-오프 페이드)
  const [predictOverlayOpen, setPredictOverlayOpen] = useState(false)

  // 앱 첫 진입 로딩 (오버레이: 1→DB, 2→로봇대기, 3→체크리스트, 4 완료)
  const [initStep, setInitStep] = useState<number>(1)
  const initTimerRef = useRef<NodeJS.Timeout | null>(null)

  // 발주 모달 및 진행 시각화
  const [orderOpen, setOrderOpen] = useState(false)
  const [orderTarget, setOrderTarget] = useState<PredictItem | null>(null)
  const [orderQty, setOrderQty] = useState("")
  const [orderDate, setOrderDate] = useState("")
  const [orderProgressOpen, setOrderProgressOpen] = useState(false)
  const [orderProgressStep, setOrderProgressStep] = useState(0)

  // LED 색상 결정 (초록색/주황색/빨간색)
  const getLedColor = () => {
    if (modelState === "error") return "red"
    if (modelState === "loading" || modelWarming || predictOverlayOpen || orderProgressOpen) return "orange"
    return "green"
  }

  // 예측 요청 취소/동기화 가드
  const predictAbortRef = useRef<AbortController | null>(null)
  const fetchDoneRef = useRef(false)

  // ──────────────────────────────────────────────────────────────────────────────
  // API
  // ──────────────────────────────────────────────────────────────────────────────
  async function fetchMetaAndPoll() {
    // 최초 진입/재시작 시 상태 초기화
    setModelState("loading")
    setModelWarming(true)
    try {
      const r = await fetch(`${API}/api/model/meta`)
      if (!r.ok) throw new Error(`META ${r.status}`)
      const j = await r.json()
      setModelMeta(j)
      if (j?.available) {
        setModelState("ok")
        setModelWarming(false)
        if (modelPollRef.current) clearInterval(modelPollRef.current)
        modelPollRef.current = null
      } else {
        // 폴링 시작(2초 주기)
        if (modelPollRef.current) clearInterval(modelPollRef.current)
        modelPollRef.current = setInterval(async () => {
          try {
            const r2 = await fetch(`${API}/api/model/meta`)
            const j2 = await r2.json()
            setModelMeta(j2)
            if (j2?.available) {
              setModelState("ok")
              setModelWarming(false)
              if (modelPollRef.current) clearInterval(modelPollRef.current)
              modelPollRef.current = null
            }
          } catch (e) {
            // 폴링 에러는 무시하고 계속 시도
          }
        }, 2000)
      }
    } catch {
      setModelState("error")
      setModelWarming(false)
    }
  }

  async function runPredict(showOverlay = true) {
    if (predicting) return // 더블클릭 가드
    setPredicting(true)
    fetchDoneRef.current = false

    // 오버레이 열기 및 카테고리 준비(기존 요약이 있으면 활용, 없으면 기본값)
    const catData = data?.summary?.categories?.map((c) => c.category) ?? defaultCats
    const overlayId = Symbol("predict-overlay") // 현재 세션 식별자

    if (showOverlay) setPredictOverlayOpen(true)

    // 예측 호출(취소 가능)
    if (predictAbortRef.current) predictAbortRef.current.abort()
    const ac = new AbortController()
    predictAbortRef.current = ac

    try {
      const r = await fetch(`${API}/api/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          years: [2022, 2023, 2024],
          service_days: 14,
          pack_size: 100,
          moq: 0,
          holding_rate_per_day: 0.0005,
          penalty_multiplier: 5.0,
        }),
        signal: ac.signal,
      })
      if (!r.ok) {
        const txt = await r.text().catch(()=> "")
        throw new Error(`PREDICT ${r.status} ${txt}`)
      }
      const j: PredictResponse = await r.json()
      setData(j)
      fetchDoneRef.current = true
      document.dispatchEvent(new CustomEvent("predict-overlay-fetch-done", { detail: { overlayId } }))
    } catch (e: any) {
      if (e?.name === "AbortError") return
      // 에러 메시지를 콘솔에만 출력하고 UI에는 표시하지 않음
      console.error("예측 실패:", e?.message || "예측 실패")
      fetchDoneRef.current = true
      document.dispatchEvent(new CustomEvent("predict-overlay-fetch-done", { detail: { overlayId, error: true } }))
    } finally {
      setPredicting(false)
    }

    return () => {
      if (predictAbortRef.current) predictAbortRef.current.abort()
    }
  }

  // ──────────────────────────────────────────────────────────────────────────────
  // 마운트: 초기 로딩 오버레이 + 메타 조회/폴링 + 최초 예측(백그라운드)
  // ──────────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    const schedule = [900, 1200, 900] // 각 단계 지속(ms)
    let step = 1
    const go = () => {
      if (step >= 3) { setInitStep(4); return }
      step += 1
      setInitStep(step)
      initTimerRef.current = setTimeout(go, schedule[step - 1])
    }
    initTimerRef.current = setTimeout(go, schedule[0])

    ;(async () => {
      await fetchMetaAndPoll() // 가용될 때까지 전체 오버레이 유지
      await runPredict(false) // 첫 진입은 오버레이 없이 백그라운드 실행
    })()

    return () => {
      if (initTimerRef.current) clearTimeout(initTimerRef.current)
      if (modelPollRef.current) clearInterval(modelPollRef.current)
    }
  }, [])

  // ──────────────────────────────────────────────────────────────────────────────
  // 파생 데이터
  // ──────────────────────────────────────────────────────────────────────────────
  const hasPositiveReco = (r: PredictItem) => {
    const recos = r.recommendations_top3 || []
    return recos.some((x) => (x?.quantity || 0) > 0 && (x?.expected_total_cost || 0) > 0)
  }

  const top5 = useMemo(() => {
    const items = (data?.items || []).filter(hasPositiveReco)
    const score = (r: PredictItem) => {
      const d = Math.max(0.1, r.predicted_days_to_depletion || 999)
      const top = r.recommendations_top3?.[0]
      const qty = top?.quantity || 0
      const cost = top?.expected_total_cost || 0
      return (r.warning ? 1000 : 0) + 1000 / d + qty * 0.01 + cost * 0.00001
    }
    return items.slice().sort((a, b) => score(b) - score(a)).slice(0, 5)
  }, [data])

  // === 부품 기준 임박/주의 집계 ===
  const allItems = data?.items || []

  const imminentAll = allItems.filter(
    (r) => (r.predicted_days_to_depletion ?? 999) <= 3
  )
  const watchAll = allItems.filter(
    (r) => (r.predicted_days_to_depletion ?? 999) > 3 &&
          (r.predicted_days_to_depletion ?? 999) <= 7
  )

  // 카드에 보여줄 Top 리스트 (최대 8개)
  const imminentTop = imminentAll
    .slice()
    .sort((a,b) => a.predicted_days_to_depletion - b.predicted_days_to_depletion)
    .slice(0, 8)

  const watchTop = watchAll
    .slice()
    .sort((a,b) => a.predicted_days_to_depletion - b.predicted_days_to_depletion)
    .slice(0, 8)

  // 카드의 숫자(이제 '카테고리'가 아니라 '부품' 기준)
  const count3 = imminentAll.length
  const count7 = watchAll.length


  
  const idLabel = (r?: Partial<PredictItem> | null) => {
    if (!r) return ""
    const id: any = (r as any)?.part_id ?? (r as any)?.partId ?? (r as any)?.id
    return id === 0 || id ? String(id) : ""
  }

  // ──────────────────────────────────────────────────────────────────────────────
  // 동작 핸들러
  // ──────────────────────────────────────────────────────────────────────────────
  const openOrderModal = (r: PredictItem) => {
    const o = r.recommendations_top3?.[0]
    setOrderTarget(r)
    setOrderQty(String(o?.quantity || ""))
    setOrderDate("")
    setOrderOpen(true)
  }

  const submitOrder = async () => {
    const pid = idLabel(orderTarget)
    setOrderOpen(false)

    // 발주 진행 모달 시작
    setOrderProgressStep(0)
    setOrderProgressOpen(true)
    const phases = ["요청 준비", "DB/규정 확인", "가격·MOQ 계산", "요청 전송", "완료"]
    let step = 0
    const t = setInterval(() => {
      step += 1
      setOrderProgressStep(step)
      if (step >= phases.length - 1) {
        clearInterval(t)
        const order = {
          part_id: pid,
          qty: Number(orderQty || 0),
          eta: orderDate || null,
          at: new Date().toISOString(),
        }
        const prev = JSON.parse(localStorage.getItem("orders") || "[]")
        localStorage.setItem("orders", JSON.stringify([order, ...prev]))
        setTimeout(() => setOrderProgressOpen(false), 600)
      }
    }, 700)
  }

  const exportCSV = () => {
    const rows = data?.items || []
    const esc = (s: any) => `"${String(s ?? "").replace(/"/g, '""')}"`
    const header = [
      "part_id",
      "category",
      "size",
      "manufacturer",
      "today_usage",
      "opening_stock",
      "predicted_order_qty",
      "predicted_days_to_depletion",
      "top1_day",
      "top1_qty",
      "top1_cost",
      "top2_day",
      "top2_qty",
      "top2_cost",
      "top3_day",
      "top3_qty",
      "top3_cost",
    ].map(esc).join(",")

    const body = rows.map((r) => {
      const t1 = r.recommendations_top3?.[0]
      const t2 = r.recommendations_top3?.[1]
      const t3 = r.recommendations_top3?.[2]
      return [
        r.part_id,
        r.category,
        r.size,
        r.manufacturer,
        r.today_usage,
        r.opening_stock,
        Math.round(r.predicted_order_qty),
        r.predicted_days_to_depletion?.toFixed?.(2) ?? "",
        t1?.day_offset ?? "",
        t1?.quantity ?? "",
        t1?.expected_total_cost ?? "",
        t2?.day_offset ?? "",
        t2?.quantity ?? "",
        t2?.expected_total_cost ?? "",
        t3?.day_offset ?? "",
        t3?.quantity ?? "",
        t3?.expected_total_cost ?? "",
      ].map(esc).join(",")
    })
    const csv = [header, ...body].join("\n")
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `predict_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  // ──────────────────────────────────────────────────────────────────────────────
  // UI
  // ──────────────────────────────────────────────────────────────────────────────
  const currentCats = (data?.summary?.categories?.map((c) => c.category) ?? defaultCats)

  return (
    <div className="p-4 space-y-6 relative">
      {/* 모델 가용(워밍업) 오버레이 - 전체 화면 블로킹 */}
      {modelWarming && <ModelAvailabilityOverlay meta={modelMeta} />}

      {/* 초기 오버레이 (초기 UI 연출) */}
      {initStep < 4 && <InitialOverlay step={initStep} />}

      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-white">AI 인벤토리 예측/발주</h1>
          <LedDot color={getLedColor()} />
          <Button
            size="sm"
            className="bg-green-600 hover:bg-green-700 text-white"
            onClick={async () => {
              setInitStep(1)
              await fetchMetaAndPoll()
              setTimeout(() => setInitStep(2), 600)
              setTimeout(() => setInitStep(3), 1200)
              setTimeout(() => setInitStep(4), 1800)
            }}
          >
            모델 새로 생성
          </Button>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => runPredict(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
            disabled={predicting || modelWarming}
          >
            {predicting ? (
              <span className="inline-flex items-center gap-2"><Loader2 size={16} className="animate-spin"/> 예측 중...</span>
            ) : (
              "예측 실행"
            )}
          </Button>
          <Button onClick={exportCSV} disabled={!data || modelWarming}>
            CSV 내보내기
          </Button>
        </div>
      </div>

      {/* 모델 상태 카드 */}
      <Card>
        <CardHeader>
          <CardTitle>모델 상태</CardTitle>
        </CardHeader>
        <CardContent className="text-sm flex flex-wrap gap-6">
          <div>가용: {modelMeta?.available ? "예" : modelWarming ? "준비 중" : "아니오"}</div>
          <div>생성시각: {modelMeta?.meta?.created_at || "-"}</div>
          <div>
            학습연도:
            {Array.isArray(modelMeta?.meta?.train_years)
              ? " " + modelMeta.meta.train_years.join(", ")
              : " -"}
          </div>
          <div>갱신: {modelMeta?.updated_at || "-"}</div>
        </CardContent>
      </Card>

      {/* 2장 카드: 3일 / 7일 (AI 요약봇 제거) */}
      <Card>
        <CardHeader>
          <CardTitle>재고 커버 요약</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* 3일 이하 */}
            <SummaryCard
              title="3일 이하 임박"
              value={`${count3}개 부품`}
              tone="danger"
              icon={<TriangleAlert size={22} />}
              desc="즉시 발주 검토가 필요합니다."
            >
              <ul className="text-xs text-gray-300 space-y-1">
                {imminentTop.length ? (
                  imminentTop.map((p) => (
                    <li key={idLabel(p)} className="flex justify-between">
                      <span className="font-mono">#{idLabel(p)} {p.category}/{p.size}</span>
                      <span className="tabular-nums">{p.predicted_days_to_depletion.toFixed(1)}일</span>
                    </li>
                  ))
                ) : (
                  <li className="text-gray-500">임박 부품 없음</li>
                )}
              </ul>
            </SummaryCard>

            {/* 7일 이하 */}
            <SummaryCard
              title="7일 이하 주의"
              value={`${count7}개 부품`}
              tone="warn"
              icon={<TriangleAlert size={22} />}
              desc="단기 모니터링 및 발주 준비 권장."
            >
              <ul className="text-xs text-gray-300 space-y-1">
                {watchTop.length ? (
                  watchTop.map((p) => (
                    <li key={idLabel(p)} className="flex justify-between">
                      <span className="font-mono">#{idLabel(p)} {p.category}/{p.size}</span>
                      <span className="tabular-nums">{p.predicted_days_to_depletion.toFixed(1)}일</span>
                    </li>
                  ))
                ) : (
                  <li className="text-gray-500">주의 부품 없음</li>
                )}
              </ul>
            </SummaryCard>

          </div>
        </CardContent>
      </Card>

      {/* 발주 추천 Top-5 */}
      <Card>
        <CardHeader>
          <CardTitle>발주 추천 Top-5</CardTitle>
        </CardHeader>
        <CardContent>
          {!top5.length ? (
            <div className="text-sm text-gray-500">추천 대상이 없습니다.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {top5.map((r, idx) => {
                const o = r.recommendations_top3?.[0]
                const highlight = idx < 3
                return (
                  <div
                    key={idLabel(r)}
                    className={`border rounded p-3 transition ${
                      highlight ? "ring-2 ring-purple-400 shadow-lg" : ""
                    }`}
                  >
                    <div className="text-sm font-medium flex items-center justify-between">
                      <span>
                        #{idLabel(r)} {r.category}/{r.size}
                      </span>
                      {r.warning ? <Badge className="ml-2 bg-red-600">경고</Badge> : null}
                    </div>
                    <div className="text-[11px] text-gray-500 mt-1">
                      오늘사용 {r.today_usage.toLocaleString()} / 시작재고 {r.opening_stock.toLocaleString()}
                    </div>
                    <div className="mt-2 text-sm min-h-[40px]">
                      {o ? (
                        <>
                          권장안: D+{o.day_offset}, {o.quantity.toLocaleString()}개, 총비용≈₩
                          {o.expected_total_cost.toLocaleString()}
                        </>
                      ) : (
                        "권장안 없음"
                      )}
                    </div>
                    <div className="mt-3">
                      <Button onClick={() => openOrderModal(r)}>발주요청</Button>
                    </div>
                  </div>
                )}
            )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 발주요청 입력 모달 */}
      <Dialog open={orderOpen} onOpenChange={setOrderOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>발주요청</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="text-sm">
              대상: #{idLabel(orderTarget)} {(orderTarget?.category) || ""}/{(orderTarget?.size) || ""}
            </div>
            <div>
              <label className="text-sm block mb-1">수량</label>
              <Input value={orderQty} onChange={(e) => setOrderQty(e.target.value)} placeholder="주문 수량" />
            </div>
            <div>
              <label className="text-sm block mb-1">도착요청일</label>
              <Input type="date" value={orderDate} onChange={(e) => setOrderDate(e.target.value)} />
            </div>
            <div className="pt-2">
              <Button onClick={submitOrder}>제출</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 발주 진행 모달 (단계 연출) */}
      <Dialog
        open={orderProgressOpen}
        onOpenChange={(open) => {
          if (!open && orderProgressStep < 4) return
          setOrderProgressOpen(open)
        }}
      >
        <DialogContent
          onInteractOutside={(e) => { if (orderProgressStep < 4) e.preventDefault() }}
          onEscapeKeyDown={(e) => { if (orderProgressStep < 4) e.preventDefault() }}
        >
          <DialogHeader>
            <DialogTitle>발주 처리 중...</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            <StepRow step={0} cur={orderProgressStep} label="요청 준비" />
            <StepRow step={1} cur={orderProgressStep} label="DB/규정 확인" />
            <StepRow step={2} cur={orderProgressStep} label="가격·MOQ 계산" />
            <StepRow step={3} cur={orderProgressStep} label="요청 전송" />
            <StepRow step={4} cur={orderProgressStep} label="완료" />
          </div>
        </DialogContent>
      </Dialog>

      {/* ★ 새 예측 실행 오버레이: 큰 로딩 + 리스트 체크오프 페이드아웃 */}
      <PredictProgressOverlay
        open={predictOverlayOpen}
        onOpenChange={setPredictOverlayOpen}
        categories={currentCats}
        fetchDoneRef={fetchDoneRef}
      />

      {/* 전역 스타일 (LED, 스캔, 오버레이, 새 로더, 모델가용 오비트) */}
      <style jsx global>{`
        @keyframes ledBlink { 0%, 49% { opacity: 0.15; } 50%, 100% { opacity: 1; } }
        @keyframes scanMove { 0% { transform: translateY(-100%); opacity: 0.0; } 15% { opacity: 0.9; } 100% { transform: translateY(100%); opacity: 0.0; } }
        @keyframes scanPulse { 0% { opacity: .5 } 50% { opacity: 1 } 100% { opacity: .5 } }
        .animate-scan { animation: scanPulse 1.2s ease-in-out infinite; }
        
        /* LED 색상별 스타일 */
        .led-dot { 
          width: 10px; 
          height: 10px; 
          border-radius: 9999px; 
          transition: all 0.3s ease;
        }
        .led-dot.green { 
          background: radial-gradient(closest-side, #22c55e, #065f46 70%, #000 100%); 
          box-shadow: 0 0 10px rgba(34, 197, 94, 0.8); 
        }
        .led-dot.orange { 
          background: radial-gradient(closest-side, #f59e0b, #92400e 70%, #000 100%); 
          box-shadow: 0 0 10px rgba(245, 158, 11, 0.8); 
        }
        .led-dot.red { 
          background: radial-gradient(closest-side, #ef4444, #991b1b 70%, #000 100%); 
          box-shadow: 0 0 10px rgba(239, 68, 68, 0.8); 
        }
        .led-dot.blinking { 
          animation: ledBlink 1.2s infinite; 
        }
        
        .scan-surface::before { content: ""; position: absolute; inset: 0; background: repeating-linear-gradient(180deg, rgba(96,165,250,0.08) 0px, rgba(96,165,250,0.08) 2px, transparent 3px, transparent 6px ); }
        .scan-line { position: absolute; left: 0; right: 0; height: 28px; top: 0; background: linear-gradient(90deg, transparent, rgba(34,197,94,0.25), transparent); border-top: 1px solid rgba(34,197,94,0.5); border-bottom: 1px solid rgba(34,197,94,0.5); animation: scanMove 1.6s linear infinite; }

        /* === Big loader styling (V0 느낌) === */
        .big-loader { position: relative; width: 128px; height: 128px; border-radius: 9999px; isolation: isolate; background: conic-gradient(from 0deg, rgba(99,102,241,.9), rgba(20,184,166,.9), rgba(34,197,94,.9), rgba(99,102,241,.9)); animation: rotate360 2.2s linear infinite; box-shadow: 0 0 40px rgba(34,197,94,.35), inset 0 0 25px rgba(0,0,0,.5); }
        .big-loader::before { content: ""; position: absolute; inset: 16px; border-radius: 9999px; background: #0B0F17; box-shadow: inset 0 0 24px rgba(0,0,0,.6); }
        .big-loader::after { content: ""; position: absolute; inset: -10px; border-radius: 9999px; filter: blur(10px); background: radial-gradient(closest-side, rgba(34,197,94,.35), transparent 70%); }
        @keyframes rotate360 { to { transform: rotate(360deg); } }

        /* list item animation */
        .check-item { will-change: transform, opacity, max-height, margin, padding; transition: opacity .35s ease, transform .35s ease, max-height .35s ease, margin .35s ease, padding .35s ease; }
        .check-item.done { opacity: 0; transform: translateX(8px); max-height: 0; margin: 0; padding-top: 0; padding-bottom: 0; }

        /* overlay glass */
        .glass-panel { background: rgba(8,12,20,.72); backdrop-filter: blur(10px); border: 1px solid rgba(99,102,241,.25); box-shadow: 0 10px 40px rgba(0,0,0,.45), inset 0 0 0 1px rgba(255,255,255,.02); }

        /* === Model Availability (orbit viz) === */
        @keyframes pulseCore { 0%, 100% { transform: scale(1); opacity: .85 } 50% { transform: scale(1.06); opacity: 1 } }
        .orbit-wrap { position: relative; width: 220px; height: 220px; }
        .core { position: absolute; inset: 50% auto auto 50%; transform: translate(-50%, -50%); width: 18px; height: 18px; border-radius: 9999px; background: radial-gradient(closest-side, #22c55e, #065f46 70%); box-shadow: 0 0 24px rgba(34,197,94,.6); animation: pulseCore 1.8s ease-in-out infinite; }
        .ring { position: absolute; inset: 0; border-radius: 9999px; border: 1px dashed rgba(99,102,241,.25); }
        .ring.r2 { inset: 18px; }
        .ring.r3 { inset: 36px; }
        .sat { position: absolute; width: 8px; height: 8px; border-radius: 9999px; background: #a78bfa; box-shadow: 0 0 12px rgba(167,139,250,.8); top: 50%; left: 50%; transform-origin: -80px 0; }
        .sat::after { content:""; position: absolute; inset: -6px; border-radius: 9999px; background: radial-gradient(circle, rgba(167,139,250,.35), transparent 60%); filter: blur(8px); }
        @keyframes orbitA { to { transform: rotate(360deg); } }
        @keyframes orbitB { to { transform: rotate(-360deg); } }
        @keyframes orbitC { to { transform: rotate(360deg); } }
        .pathA { position: absolute; inset: 0; animation: orbitA 10s linear infinite; }
        .pathB { position: absolute; inset: 18px; animation: orbitB 14s linear infinite; }
        .pathC { position: absolute; inset: 36px; animation: orbitC 20s linear infinite; }
      `}</style>
    </div>
  )
}

// ────────────────────────────────────────────────────────────────────────────────
// 새 예측 오버레이 컴포넌트
// ────────────────────────────────────────────────────────────────────────────────
function PredictProgressOverlay({
  open,
  onOpenChange,
  categories,
  fetchDoneRef,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  categories: string[]
  fetchDoneRef: React.MutableRefObject<boolean>
}) {
  type LI = { id: number; label: string; status: "pending" | "checking" | "done" }
  const [items, setItems] = useState<LI[]>([])
  const stepTimerRef = useRef<NodeJS.Timeout | null>(null)
  const sessionRef = useRef(0)
  const speedRef = useRef(260) // 체크-오프 간격(ms)

  // 페치 완료 이벤트 수신(조건 만족 시 닫기)
  useEffect(() => {
    const onFetchDone = () => {
      const canClose = items.every((i) => i.status === "done")
      if (canClose) onOpenChange(false)
    }
    document.addEventListener("predict-overlay-fetch-done", onFetchDone as any)
    return () => document.removeEventListener("predict-overlay-fetch-done", onFetchDone as any)
  }, [items, onOpenChange])

  // 오버레이 열릴 때 아이템 초기화
  useEffect(() => {
    if (!open) {
      if (stepTimerRef.current) { clearInterval(stepTimerRef.current); stepTimerRef.current = null }
      return
    }

    sessionRef.current += 1
    const cur = sessionRef.current

    const init: LI[] = categories.map((label, idx) => ({ id: idx, label, status: "pending" }))
    setItems(init)

    if (stepTimerRef.current) clearInterval(stepTimerRef.current)
    stepTimerRef.current = setInterval(() => {
      setItems((prev) => {
        if (sessionRef.current !== cur) return prev
        const next = [...prev]
        const idx = next.findIndex((x) => x.status === "pending")
        if (idx === -1) {
          if (fetchDoneRef.current) onOpenChange(false)
          if (stepTimerRef.current) { clearInterval(stepTimerRef.current); stepTimerRef.current = null }
          return next
        }
        next[idx] = { ...next[idx], status: "checking" }
        setTimeout(() => {
          setItems((curList) => {
            const arr = [...curList]
            const i2 = arr.findIndex((x) => x.id === next[idx].id)
            if (i2 !== -1) arr[i2] = { ...arr[i2], status: "done" }
            return arr
          })
        }, 220)
        return next
      })
    }, speedRef.current)

    return () => {
      if (stepTimerRef.current) { clearInterval(stepTimerRef.current); stepTimerRef.current = null }
    }
  }, [open, categories, fetchDoneRef, onOpenChange])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[720px] glass-panel">
        <DialogHeader>
          <DialogTitle>예측 실행 중...</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-1 md:grid-cols-[160px_1fr] gap-4 items-start">
          {/* big spinner */}
          <div className="flex justify-center md:justify-start items-center md:items-start">
            <div className="big-loader" aria-label="loading" />
          </div>

          {/* checklist area */}
          <div className="max-h-[320px] overflow-y-auto pr-1">
            {items.map((it) => (
              <div key={it.id} className={`check-item flex items-center gap-2 py-2 ${it.status === "done" ? "done" : ""}`}>
                {it.status === "pending" && <Loader2 size={14} className="animate-spin text-gray-400" />}
                {it.status === "checking" && <CheckCircle2 size={16} className="text-green-500" />}
                {it.status === "done" && <CheckCircle2 size={16} className="text-green-600" />}
                <span className={`text-xs ${it.status === "done" ? "line-through text-gray-500" : it.status === "checking" ? "text-green-300" : "text-gray-300"}`}>
                  {it.label}
                </span>
              </div>
            ))}
            {!items.length && (
              <div className="text-xs text-gray-400">카테고리 로드 중...</div>
            )}
          </div>
        </div>
        <div className="text-[11px] text-gray-400 mt-1">
          DB에서 데이터를 가져오고, 모델이 돌아가는 중입니다... 완료되면 자동으로 닫힙니다.
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ────────────────────────────────────────────────────────────────────────────────
// 모델 가용(워밍업) 전체 오버레이
// ────────────────────────────────────────────────────────────────────────────────
function ModelAvailabilityOverlay({ meta }: { meta: any }) {
  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="w-[min(92vw,840px)] rounded-2xl glass-panel p-6">
        <div className="flex flex-col md:flex-row items-center gap-6">
          {/* Orbit viz */}
          <div className="orbit-wrap">
            <div className="ring r1" />
            <div className="ring r2" />
            <div className="ring r3" />
            <div className="core" />
            <div className="pathA"><div className="sat" style={{ transformOrigin: "-100px 0" }} /></div>
            <div className="pathB"><div className="sat" style={{ transformOrigin: "-80px 0", background: "#34d399" }} /></div>
            <div className="pathC"><div className="sat" style={{ transformOrigin: "-60px 0", background: "#60a5fa" }} /></div>
          </div>

          {/* Copy */}
          <div className="text-center md:text-left">
            <div className="text-lg font-semibold flex items-center justify-center md:justify-start gap-2">
              <Loader2 className="animate-spin" size={18} />
              <span>모델 가용 중…</span>
            </div>
            <div className="text-sm text-gray-300 mt-2">
              엔진을 기동하고 가중치를 로드하는 중입니다. 잠시만 기다려 주세요.
            </div>
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-gray-400">
              <div>• 엔진: {meta?.meta?.name || "-"}</div>
              <div>• 버전: {meta?.meta?.version || "-"}</div>
              <div>• 최근 갱신: {meta?.updated_at || "-"}</div>
              <div>• 학습연도: {Array.isArray(meta?.meta?.train_years) ? meta.meta.train_years.join(", ") : "-"}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ────────────────────────────────────────────────────────────────────────────────
// 보조 컴포넌트들
// ────────────────────────────────────────────────────────────────────────────────
function LedDot({ color }: { color: "green" | "orange" | "red" }) {
  const shouldBlink = color === "orange" || color === "red"
  return (
    <div 
      className={`led-dot ${color} ${shouldBlink ? "blinking" : ""}`} 
      title={
        color === "green" ? "연결됨" : 
        color === "orange" ? "연결 중" : 
        "연결 실패"
      } 
    />
  )
}

function StepRow({ step, cur, label }: { step: number; cur: number; label: string }) {
  const active = cur >= step
  return (
    <div className="flex items-center gap-2">
      {active ? <CheckCircle2 size={16} className="text-green-500" /> : <Loader2 size={16} className="animate-spin text-gray-400" />}
      <span className={active ? "text-green-400" : "text-gray-300"}>{label}</span>
    </div>
  )
}

function SummaryCard({
  title,
  value,
  tone,
  icon,
  desc,
  children,  // ← 추가
}: {
  title: string
  value: string
  tone: "danger" | "warn" | "ok" | "info"
  icon: React.ReactNode
  desc?: string
  children?: React.ReactNode // ← 추가
}) {
  const toneClass =
    tone === "danger"
      ? "border-red-600/50 bg-red-950/20"
      : tone === "warn"
      ? "border-yellow-600/50 bg-yellow-950/20"
      : tone === "ok"
      ? "border-green-600/50 bg-green-950/20"
      : "border-blue-600/50 bg-blue-950/20"
  return (
    <Card className={`border ${toneClass}`}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          {icon}
          <div className="font-semibold">{title}</div>
        </div>
        <div className="text-2xl font-bold mt-1">{value}</div>
        {desc ? <div className="text-xs text-gray-400 mt-1">{desc}</div> : null}
        {children ? <div className="mt-2">{children}</div> : null}
      </CardContent>
    </Card>
  )
}


function InitialOverlay({ step }: { step: number }) {
  // 1: DB → 2: 로봇(…) → 3: 체크리스트
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-[360px] rounded-xl border border-[#30363D] bg-[#0D1117] p-5 shadow-2xl">
        <div className="flex items-center gap-2 text-sm text-gray-300 mb-4">
          <Cpu size={16} />
          <span>초기화 중 (모델 준비)</span>
        </div>
        <div className="space-y-3">
          <Row icon={<Database size={16} />} label="DB 읽는 중" active={step >= 1} spin={step < 1} />
          <Row icon={<Bot size={16} />} label="로봇 대기 (...)" active={step >= 2} spin={step < 2} />
          <Row icon={<CheckCircle2 size={16} />} label="체크리스트 완료" active={step >= 3} spin={step < 3} />
        </div>
        <div className="mt-4 text-[11px] text-gray-500">
          초기화가 완료되면 자동으로 대시보드가 표시됩니다.
        </div>
      </div>
    </div>
  )
}

function Row({
  icon,
  label,
  active,
  spin,
}: {
  icon: React.ReactNode
  label: string
  active: boolean
  spin?: boolean
}) {
  return (
    <div className="flex items-center gap-2">
      {active ? (
        <CheckCircle2 size={16} className="text-green-500" />
      ) : spin ? (
        <Loader2 size={16} className="animate-spin text-gray-400" />
      ) : (
        icon
      )}
      <span className={active ? "text-green-400" : "text-gray-300"}>{label}</span>
    </div>
  )
}

// 예측 진행 모달에서 카테고리 리스트가 없을 때 사용할 기본 값
const defaultCats = [
  "Capacitor",
  "Resistor",
  "IC",
  "Connector",
  "Inductor",
  "Transistor",
  "Diode",
  "Crystal",
  "Sensor",
  "Module",
]