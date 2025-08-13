"use client"

import type { FC } from "react"
import { AlertTriangle, Clock, Thermometer, Droplets, Wind, Activity, Factory, Download, Filter, AlertCircle } from 'lucide-react'
import { useState, useEffect, useMemo } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { io, Socket } from "socket.io-client"


// 소켓 통신 데이터 타입 지정
interface FactoryEnvData {
  id: number;
  timestamp: string;
  temperature_c: number;
  humidity_percent: number;
  pm25_ug_m3: number;
  pm10_ug_m3: number;
  co2_ppm: number;
}

interface FactoryDataWrapper {
  from: string;
  data: FactoryEnvData[];
  index: number;
}

let socket: Socket;



// --- Data Mocks ---
const environmentData = {
  temperature: { current: 23.5, status: "normal", trend: [22.1, 22.8, 23.2, 23.5, 23.1, 22.9, 23.5] },
  humidity: { current: 65.2, status: "warning", trend: [62.1, 64.2, 66.8, 68.1, 67.5, 65.8, 65.2] },
  pm25: { current: 12.3, status: "normal", trend: [10.2, 11.5, 12.1, 12.3, 11.8, 12.0, 12.3] },
  pm10: { current: 18.7, status: "normal", trend: [16.2, 17.1, 18.2, 18.7, 17.9, 18.1, 18.7] },
  co2: { current: 420, status: "normal", trend: [410, 415, 418, 420, 422, 419, 420] }
}

const moistureSensitiveMaterials = [
  { name: "MLCC", optimalRange: "30-50%", currentHumidity: 45.2, status: "normal", warehouse: "A동" },
  { name: "BGA", optimalRange: "20-40%", currentHumidity: 52.1, status: "warning", warehouse: "B동" },
  { name: "FPC", optimalRange: "35-55%", currentHumidity: 38.7, status: "normal", warehouse: "C동" },
  { name: "QFN", optimalRange: "25-45%", currentHumidity: 48.3, status: "normal", warehouse: "A동" }
]



// --- Components ---

const EnvironmentCard: FC<{ title: string; value: number; unit: string; status: string; trend: number[]; icon: any; threshold?: string }> = ({ 
  title, value, unit, status, trend, icon: Icon, threshold 
}) => {
  // 센서별 기준값 설정
  const getScaleInfo = (title: string) => {
    switch (title) {
      case '온도':
        return { min: 15, max: 30, optimal: [18, 25] }; // 15-30°C 범위, 18-25°C가 최적
      case '습도':
        return { min: 0, max: 100, optimal: [0, 70] }; // 0-100% 범위, 70% 이하가 최적
      case 'PM2.5':
        return { min: 0, max: 100, optimal: [0, 50] }; // 0-100㎍/m³ 범위, 50 이하가 최적
      case 'PM10':
        return { min: 0, max: 150, optimal: [0, 100] }; // 0-150㎍/m³ 범위, 100 이하가 최적
      case 'CO₂':
        return { min: 300, max: 1500, optimal: [300, 1000] }; // 300-1500ppm 범위, 1000 이하가 최적
      default:
        return { min: 0, max: 100, optimal: [0, 100] };
    }
  };

  const scaleInfo = getScaleInfo(title);
  
  return (
  <Card className={`bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] hover:shadow-xl transition-all duration-300 ${
    status === "warning" ? "ring-1 ring-yellow-500/50" : status === "danger" ? "ring-1 ring-red-500/50" : ""
  }`}>
    <CardContent className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${
            status === "warning" ? "bg-yellow-500/20" : status === "danger" ? "bg-red-500/20" : "bg-blue-500/20"
          }`}>
            <Icon className={`w-6 h-6 ${
              status === "warning" ? "text-yellow-400" : status === "danger" ? "text-red-400" : "text-blue-400"
            }`} />
          </div>
          <h3 className="text-white font-semibold text-lg">{title}</h3>
        </div>
        {status !== "normal" && (
          <AlertTriangle className={`w-5 h-5 ${status === "warning" ? "text-yellow-400" : "text-red-400"} animate-pulse`} />
        )}
      </div>
      
      <div className="space-y-4">
        <div className="flex items-baseline gap-2">
          <span className={`text-4xl font-bold ${
            status === "warning" ? "text-yellow-400" : status === "danger" ? "text-red-400" : "text-white"
          }`}>
            {value}
          </span>
          <span className="text-gray-400 text-lg">{unit}</span>
        </div>
        
        {threshold && (
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              status === "warning" ? "bg-yellow-400" : status === "danger" ? "bg-red-400" : "bg-green-400"
            }`} />
            <p className="text-sm text-gray-300">기준: {threshold}</p>
          </div>
        )}
        
        {/* Clean line chart with gradient fill and scale-based Y-axis */}
        <div className="h-16 w-full bg-[#0D1117] rounded-lg p-2">
          <svg viewBox="0 0 100 50" className="w-full h-full" preserveAspectRatio="none">
            <defs>
              <linearGradient id={`gradient-${title}`} x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor={status === "warning" ? "#f59e0b" : status === "danger" ? "#ef4444" : "#3b82f6"} stopOpacity="0.3" />
                <stop offset="70%" stopColor={status === "warning" ? "#f59e0b" : status === "danger" ? "#ef4444" : "#3b82f6"} stopOpacity="0.1" />
                <stop offset="100%" stopColor={status === "warning" ? "#f59e0b" : status === "danger" ? "#ef4444" : "#3b82f6"} stopOpacity="0" />
              </linearGradient>
            </defs>
            
            {/* 기준선 표시 (최적 범위) */}
            {scaleInfo.optimal && (
              <>
                {/* 최적 범위 배경 */}
                <rect
                  x="0"
                  y={50 - ((scaleInfo.optimal[1] - scaleInfo.min) / (scaleInfo.max - scaleInfo.min)) * 40}
                  width="100"
                  height={((scaleInfo.optimal[1] - scaleInfo.optimal[0]) / (scaleInfo.max - scaleInfo.min)) * 40}
                  fill="#22c55e"
                  fillOpacity="0.1"
                />
                {/* 최적 범위 상한선 */}
                <line
                  x1="0"
                  y1={50 - ((scaleInfo.optimal[1] - scaleInfo.min) / (scaleInfo.max - scaleInfo.min)) * 40}
                  x2="100"
                  y2={50 - ((scaleInfo.optimal[1] - scaleInfo.min) / (scaleInfo.max - scaleInfo.min)) * 40}
                  stroke="#22c55e"
                  strokeWidth="1"
                  strokeDasharray="2,2"
                  strokeOpacity="0.6"
                />
              </>
            )}
            
            {trend.length > 0 && (
              <>
                {/* Area fill (gradient) */}
                <path
                  d={`M 0,${50 - ((trend[0] - scaleInfo.min) / (scaleInfo.max - scaleInfo.min)) * 40} ${trend.map((val, i) => 
                    `L ${trend.length > 1 ? (i / (trend.length - 1)) * 100 : 50},${50 - ((val - scaleInfo.min) / (scaleInfo.max - scaleInfo.min)) * 40}`
                  ).join(' ')} L 100,50 L 0,50 Z`}
                  fill={`url(#gradient-${title})`}
                />
                
                {/* Line chart */}
                <path
                  d={`M 0,${50 - ((trend[0] - scaleInfo.min) / (scaleInfo.max - scaleInfo.min)) * 40} ${trend.map((val, i) => 
                    `L ${trend.length > 1 ? (i / (trend.length - 1)) * 100 : 50},${50 - ((val - scaleInfo.min) / (scaleInfo.max - scaleInfo.min)) * 40}`
                  ).join(' ')}`}
                  fill="none"
                  stroke={status === "warning" ? "#f59e0b" : status === "danger" ? "#ef4444" : "#3b82f6"}
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                
                {/* Data points */}
                {trend.map((val, i) => {
                  const cx = trend.length > 1 ? (i / (trend.length - 1)) * 100 : 50;
                  const cy = 50 - ((val - scaleInfo.min) / (scaleInfo.max - scaleInfo.min)) * 40;
                  
                  // NaN 체크
                  if (isNaN(cx) || isNaN(cy)) return null;
                  
                  return (
                    <circle
                      key={i}
                      cx={cx}
                      cy={cy}
                      r="1.5"
                      fill={status === "warning" ? "#f59e0b" : status === "danger" ? "#ef4444" : "#3b82f6"}
                    />
                  );
                })}
              </>
            )}
          </svg>
        </div>
      </div>
    </CardContent>
  </Card>
);
}

const MaterialCard: FC<{ material: typeof moistureSensitiveMaterials[0] }> = ({ material }) => (
  <div className={`p-3 rounded-lg border transition-all duration-300 ${
    material.status === "warning" 
      ? "bg-yellow-500/10 border-yellow-500/30" 
      : "bg-[#161B22]/50 border-[#30363D]"
  }`}>
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center gap-2">
        <h4 className="text-white font-medium text-base">{material.name}</h4>
        {material.status === "warning" && (
          <AlertCircle className="w-4 h-4 text-yellow-400 animate-pulse" />
        )}
      </div>
      <Badge className="text-xs bg-gray-700/50 text-gray-300">
        {material.warehouse}
      </Badge>
    </div>
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-gray-400">적정 범위: {material.optimalRange}</span>
        <span className={`font-bold ${material.status === "warning" ? "text-yellow-400" : "text-white"}`}>
          {material.currentHumidity}%
        </span>
      </div>
      <div className="w-full bg-[#30363D] rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-700 ${
            material.status === "warning" ? "bg-yellow-500" : "bg-green-500"
          }`}
          style={{ width: `${(material.currentHumidity / 100) * 100}%` }}
        />
      </div>
    </div>
  </div>
)



// --- Main Dashboard Component ---

export default function DashboardPage() {

  const [factoryEnvData, setFactoryEnvData] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [dataHistory, setDataHistory] = useState<FactoryEnvData[]>([]); // 히스토리 저장
  const [lastRecordTime, setLastRecordTime] = useState<number>(0); // 마지막 기록 시간
  

  // 소켓 통신 연결 (공장 환경 데이터 실시간 수신)
  useEffect(() => {
    socket = io("http://localhost:3100");

    socket.on("connect", () => {
      setIsConnected(true);
      socket.emit("factorydata", { from: "client", data: [] });
    });

         // 소켓 서버에서 보내는 데이터 수신
     socket.on("factorydata", (data: any) => {
       setFactoryEnvData([{ ...data, timestamp: Date.now() }]);
       
               // 1초마다 히스토리 데이터 업데이트 (실제 센서 데이터만)
        if (data?.data?.data && Array.isArray(data.data.data) && data.data.data.length > 0) {
          const sensorData = data.data.data[0];
          const currentTime = Date.now();
          
          // 1초(1000ms) 간격으로 기록
          if (currentTime - lastRecordTime >= 1000) {
            console.log("📊 센서 데이터 추가:", sensorData);
            setDataHistory(prev => {
              const newHistory = [...prev, sensorData].slice(-7); // 최근 7개만 유지
              console.log("📈 히스토리 업데이트:", newHistory.length, "개 항목");
              return newHistory;
            });
            setLastRecordTime(currentTime);
          }
        }
     });

    socket.on("disconnect", () => {
      setIsConnected(false);
    });

    return () => {
      if (socket) {
        socket.off("connect");
        socket.off("factorydata");
        socket.off("disconnect");
        socket.disconnect();
      }
    };

  }, []);



  return (
    <div className="space-y-6">
        {/* Real-time Environment Monitoring */}
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <Activity className="w-10 h-10 text-green-400" />
              실시간 환경 상태 모니터링
            </h2>
            <div className="flex items-center gap-2 bg-[#0D1117]/50 backdrop-blur-sm rounded-lg border border-[#30363D] px-3 py-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
              <span className={`text-sm font-medium ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
                {isConnected ? '실시간 연결됨' : '연결 해제됨'}
              </span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {useMemo(() => {
              // 실시간 데이터 안전성 검사 및 최신 데이터 추출
              const isValidData = Array.isArray(factoryEnvData) && factoryEnvData.length > 0;
              
              let latestData: FactoryEnvData | null = null;
              
              // 데이터 구조에 맞는 최신 데이터 추출
              if (isValidData) {
                const firstElement = factoryEnvData[0];
                
                // 중첩된 데이터 구조 처리
                if (firstElement?.data?.data && Array.isArray(firstElement.data.data) && firstElement.data.data.length > 0) {
                  latestData = firstElement.data.data[0]; // 실제 센서 데이터 (한 단계 더 깊이)
                } else if (firstElement?.data && Array.isArray(firstElement.data) && firstElement.data.length > 0) {
                  latestData = firstElement.data[0]; // 기존 구조
                }
              }
              
              // 실제 히스토리 데이터를 기반으로 트렌드 생성
              const getTrendData = (property: keyof FactoryEnvData) => {
                console.log(`🔍 ${property} 트렌드 생성 - 히스토리 길이:`, dataHistory.length);
                if (dataHistory.length > 0) {
                  const trendData = dataHistory.slice(-5).map(data => data[property] as number);
                  console.log(`📊 ${property} 실제 트렌드:`, trendData);
                  return trendData;
                }
                // 히스토리가 없으면 현재 값을 기반으로 임시 트렌드 생성
                if (latestData) {
                  const currentValue = latestData[property] as number;
                  const tempTrend = Array.from({ length: 5 }, (_, i) => {
                    const variation = (Math.random() - 0.5) * 0.1 * (i + 1);
                    return Math.max(0, currentValue * (1 + variation));
                  });
                  console.log(`🔧 ${property} 임시 트렌드:`, tempTrend);
                  return tempTrend;
                }
                console.log(`❌ ${property} 트렌드 없음`);
                return [];
              };
              
              // 각 센서별 실제 트렌드 데이터
              const tempTrend = getTrendData('temperature_c');
              const humidityTrend = getTrendData('humidity_percent');
              const pm25Trend = getTrendData('pm25_ug_m3');
              const pm10Trend = getTrendData('pm10_ug_m3');
              const co2Trend = getTrendData('co2_ppm');
              
              return (
                <>
                  <EnvironmentCard
                    title="온도"
                    value={latestData?.temperature_c ?? 0}
                    unit="℃"
                    status={latestData ? (latestData.temperature_c >= 18 && latestData.temperature_c <= 25 ? "normal" : "warning") : "normal"}
                    trend={tempTrend}
                    icon={Thermometer}
                    threshold="18-25℃"
                  />
                  <EnvironmentCard
                    title="습도"
                    value={latestData?.humidity_percent ?? 0}
                    unit="%"
                    status={latestData ? (latestData.humidity_percent < 70 ? "normal" : "warning") : "normal"}
                    trend={humidityTrend}
                    icon={Droplets}
                    threshold="< 70%"
                  />
                  <EnvironmentCard
                    title="PM2.5"
                    value={latestData?.pm25_ug_m3 ?? 0}
                    unit="㎍/m³"
                    status={latestData ? (latestData.pm25_ug_m3 < 50 ? "normal" : "warning") : "normal"}
                    trend={pm25Trend}
                    icon={Wind}
                    threshold="< 50㎍/m³"
                  />
                  <EnvironmentCard
                    title="PM10"
                    value={latestData?.pm10_ug_m3 ?? 0}
                    unit="㎍/m³"
                    status={latestData ? (latestData.pm10_ug_m3 < 100 ? "normal" : "warning") : "normal"}
                    trend={pm10Trend}
                    icon={Wind}
                    threshold="< 100㎍/m³"
                  />
                  <EnvironmentCard
                    title="CO₂"
                    value={latestData?.co2_ppm ?? 0}
                    unit="ppm"
                    status={latestData ? (latestData.co2_ppm < 1000 ? "normal" : "warning") : "normal"}
                    trend={co2Trend}
                    icon={Activity}
                    threshold="< 1000ppm"
                  />
                </>
              );
            }, [factoryEnvData, dataHistory])}
          </div>
        </div>

        {/* Moisture Sensitive Materials & Environment Data History */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Moisture Sensitive Materials */}
          <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
            <CardHeader>
              <CardTitle className="text-white text-xl flex items-center gap-2">
                <Droplets className="w-5 h-5 text-blue-400" />
                습도 민감 자재 모니터링
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {moistureSensitiveMaterials.map((material) => (
                <MaterialCard key={material.name} material={material} />
              ))}
            </CardContent>
          </Card>

                     {/* Environment Data History Table */}
           {useMemo(() => {
             // 실시간 데이터 안전성 검사 및 최신 데이터 추출
             const isValidData = Array.isArray(factoryEnvData) && factoryEnvData.length > 0;
             
             let latestData: FactoryEnvData | null = null;
             
             // 데이터 구조에 맞는 최신 데이터 추출
             if (isValidData) {
               const firstElement = factoryEnvData[0];
               
               // 중첩된 데이터 구조 처리
               if (firstElement?.data?.data && Array.isArray(firstElement.data.data) && firstElement.data.data.length > 0) {
                 latestData = firstElement.data.data[0]; // 실제 센서 데이터 (한 단계 더 깊이)
               } else if (firstElement?.data && Array.isArray(firstElement.data) && firstElement.data.length > 0) {
                 latestData = firstElement.data[0]; // 기존 구조
               }
             }
             
                           // 히스토리 데이터를 시간순으로 정렬하여 표시 (최신 7개)
              const displayData = [];
              
              // 히스토리 데이터를 시간순으로 정렬하여 추가 (최신 7개)
              const sortedHistory = [...dataHistory]
                .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                .slice(0, 7);
              
              sortedHistory.forEach((data, index) => {
                // 현재 시간을 기준으로 1초씩 이전으로 설정
                const currentTime = new Date();
                const dataTime = new Date(currentTime.getTime() - (index * 1000)); // 1초씩 이전
                
                const timeString = dataTime.toLocaleTimeString('ko-KR', { 
                  hour: '2-digit', 
                  minute: '2-digit',
                  second: '2-digit',
                  hour12: false 
                });
                
                displayData.push({
                  time: timeString,
                  temp: data.temperature_c,
                  humidity: data.humidity_percent,
                  pm25: data.pm25_ug_m3,
                  pm10: data.pm10_ug_m3,
                  co2: data.co2_ppm,
                  sensors: "정상"
                });
              });
               
                               // 데이터가 없으면 기본 데이터 표시 (7개)
                if (displayData.length === 0) {
                  const now = new Date();
                  for (let i = 0; i < 7; i++) {
                    const timeOffset = i * 1000; // 1초씩 이전
                    const dataTime = new Date(now.getTime() - timeOffset);
                    const timeString = dataTime.toLocaleTimeString('ko-KR', { 
                      hour: '2-digit', 
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: false 
                    });
                    
                    displayData.push({
                      time: timeString,
                      temp: 23.5 + (Math.random() - 0.5) * 2,
                      humidity: 65.2 + (Math.random() - 0.5) * 5,
                      pm25: 12.3 + (Math.random() - 0.5) * 2,
                      pm10: 18.7 + (Math.random() - 0.5) * 3,
                      co2: 420 + Math.floor((Math.random() - 0.5) * 10),
                      sensors: "정상"
                    });
                  }
                }
             
             return (
               <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
                 <CardHeader>
                   <div className="flex items-center justify-between">
                     <CardTitle className="text-white text-xl flex items-center gap-2">
                       <Clock className="w-5 h-5 text-cyan-400" />
                       환경 데이터 이력
                     </CardTitle>
                     <div className="flex items-center gap-2">
                       <Button
                         size="sm"
                         className="bg-blue-500/20 border-blue-500/30 text-blue-400 hover:bg-blue-600/30"
                       >
                         <Filter className="w-4 h-4 mr-2" />
                         필터
                       </Button>
                       <Button
                         size="sm"
                         className="bg-blue-500/20 border-blue-500/30 text-blue-400 hover:bg-blue-600/30"
                       >
                         <Download className="w-4 h-4 mr-2" />
                         CSV 내보내기
                       </Button>
                     </div>
                   </div>
                 </CardHeader>
                 <CardContent>
                   <div className="overflow-x-auto">
                     <table className="w-full text-base">
                                               <thead className="border-b border-[#30363D]">
                          <tr>
                            <th className="text-left p-3 text-gray-300 font-medium">시간</th>
                            <th className="text-left p-3 text-gray-300 font-medium">온도(℃)</th>
                            <th className="text-left p-3 text-gray-300 font-medium">습도(%)</th>
                            <th className="text-left p-3 text-gray-300 font-medium">PM2.5</th>
                            <th className="text-left p-3 text-gray-300 font-medium">CO₂(ppm)</th>
                            <th className="text-left p-3 text-gray-300 font-medium">센서 상태</th>
                          </tr>
                        </thead>
                       <tbody>
                                                   {displayData.map((row, index) => (
                            <tr key={index} className="border-b border-[#30363D]/50 hover:bg-[#21262D]/30 transition-colors">
                              <td className="p-3 text-white font-mono text-sm">{row.time}</td>
                              <td className="p-3 text-gray-300">{row.temp.toFixed(1)}</td>
                              <td className={`p-3 ${row.humidity > 70 ? "text-yellow-400 font-bold" : "text-gray-300"}`}>
                                {row.humidity.toFixed(1)}
                              </td>
                              <td className="p-3 text-gray-300">{row.pm25.toFixed(1)}</td>
                              <td className="p-3 text-gray-300">{row.co2}</td>
                              <td className="p-3">
                                <Badge className={`text-xs ${
                                  row.sensors === "정상" 
                                    ? "bg-green-500/20 text-green-400 border-green-500/30"
                                    : "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                                }`}>
                                  {row.sensors}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                       </tbody>
                     </table>
                   </div>
                 </CardContent>
               </Card>
             );
           }, [factoryEnvData, dataHistory])}
        </div>
    </div>
  )
}
