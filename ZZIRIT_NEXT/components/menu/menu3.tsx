import React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Eye,
  Search,
  X,
} from "lucide-react"


interface Menu3Props {
  // Props removed - no longer needed
}

// 불량 상세 정보 타입
interface DefectResult {
  id: number;
  inspection_id: number;
  label: string;
  class_index: number;
  score: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
}

// PCB 검사 데이터 타입 정의 (Express API 형태)
interface PCBInspectionData {
  id: number;
  pcb_id: string;
  status: "합격" | "불합격";
  defect_count: number;
  max_confidence: number;
  image_url: string;
  defect_result: DefectResult[];
}

// 컴포넌트에서 사용할 처리된 PCB 데이터 타입
interface PCBData {
  id: string;
  pcb_id: string;
  name: string;
  status: "합격" | "불합격";
  defectRate: string;
  image: string;
  defects: Array<{
    id: number;
    type: string;
    confidence: number;
    x1?: number;
    y1?: number;
    x2?: number;
    y2?: number;
    width?: number;
    height?: number;
  }>;
  totalDefects: number;
  defect_count: number; // 불량 PCB 기판 개수
  avgDefectRate: number;
  inspectionsCompleted: number;
  targetRate: number;
  monthlyData: Array<{ month: string; rate: number }>;
  defectTypes: Array<{ type: string; count: number; percentage: number; color: string }>;
  // PCB 상세 정보
  size: string;
  substrate: string;
  smt: string;
  // 이메일 전송을 위한 추가 속성들
  totalInspections?: number; // 총 검사 횟수
  confidence?: number; // 신뢰도
  completionRate?: number; // 완료율
  qualityGrade?: string; // 품질 등급
}



const Menu3 = ({}: Menu3Props) => {
  // 선택된 PCB 상태
  const [selectedPCB, setSelectedPCB] = React.useState<PCBData | null>(null);
  const [showPopup, setShowPopup] = React.useState(false);
  const [pcbDefectData, setPcbDefectData] = React.useState<PCBInspectionData[] | null>(null);
  
  // 검색 기능 상태
  const [searchTerm, setSearchTerm] = React.useState("");
  
  // 히트맵 이미지 갤러리 상태
  const [currentImageIndex, setCurrentImageIndex] = React.useState(0);
  const [currentPCBImages, setCurrentPCBImages] = React.useState<{image: string, pcbId: string, defects: any[]}[]>([]);
  const [imageLoaded, setImageLoaded] = React.useState(false);

  // express 백앤드에서 데이터 가져오기(mariaDB저장데이터임)
  React.useEffect(() => {
    const fetchPcbDefectData = async () => {
      try {
        const res = await fetch("http://localhost:5000/api/user/pcb-defect");
        const data = await res.json();
        setPcbDefectData(data);
        console.log("PCB 불량 데이터:", data);

      } catch (error) {
        console.error("PCB 불량 데이터 가져오기 실패:", error);
        // API 실패 시 빈 배열 설정
        setPcbDefectData([]);
      }
    };

    fetchPcbDefectData();
  }, []);


  // 결함 타입별 색상 매핑 (영어 라벨로 통일)
  const defectTypeColors: { [key: string]: string } = {
    "Missing_hole": "#64748b",
    "Short": "#3b82f6", 
    "Open_circuit": "#10b981",
    "Spur": "#f59e0b",
    "Mouse_bite": "#8b5cf6",
    "Spurious_copper": "#6b7280",
    "기타": "#6b7280"
  };

  // 결함 타입 정규화 함수 (소문자를 대문자로 변환)
  const normalizeDefectType = (label: string): string => {
    if (!label) return "기타";
    
    const normalized = label.toLowerCase().trim();
    console.log(`Normalizing defect type: "${label}" -> "${normalized}"`);
    
    switch (normalized) {
      case "missing_hole":
      case "missing hole":
      case "hole_missing":
        return "Missing_hole";
      case "short":
      case "short_circuit":
      case "단락":
        return "Short";
      case "open_circuit":
      case "open circuit":
      case "circuit_open":
      case "개방 회로":
        return "Open_circuit";
      case "spur":
      case "spur_defect":
      case "스퍼":
        return "Spur";
      case "mouse_bite":
      case "mouse bite":
      case "bite_mouse":
      case "마우스 바이트":
        return "Mouse_bite";
      case "spurious_copper":
      case "spurious copper":
      case "copper_spurious":
      case "불량 구리":
        return "Spurious_copper";
      default:
        console.log(`Unknown defect type: "${label}", using as-is`);
        return label;
    }
  };

  // PCB ID 번호에 따른 실제 PCB 정보 매핑
  const getPCBInfo = (pcbId: string) => {
    // pcb_id에서 앞쪽 숫자 추출 (예: "11_1" -> 11)
    const numberMatch = pcbId.match(/^(\d+)/);
    const number = numberMatch ? parseInt(numberMatch[1]) : 0;
    
    switch (number) {
      case 1: return { name: "SM-S901A", size: "60×40", substrate: "FR-4", smt: "Low (~10%)" };
      case 4: return { name: "SM-G992N", size: "80×60", substrate: "FR-4", smt: "Medium" };
      case 5: return { name: "LM-G820K", size: "100×70", substrate: "CEM-3", smt: "Medium" };
      case 6: return { name: "XT2315-2", size: "120×80", substrate: "Aluminum", smt: "Medium" };
      case 7: return { name: "CPH2341", size: "100×100", substrate: "FR-4", smt: "Medium~High" };
      case 8: return { name: "CPH2451", size: "130×90", substrate: "Aluminum", smt: "High (~40%)" };
      case 9: return { name: "V2312DA", size: "150×100", substrate: "Ceramic", smt: "Ultra-High" };
      case 10: return { name: "Pixel-8Pro", size: "140×90", substrate: "FR-4", smt: "Ultra-High" };
      case 11: return { name: "XQ-AT52", size: "80×50", substrate: "CEM-1", smt: "Low (~10%)" };
      case 12: return { name: "A3101", size: "60×60", substrate: "FR-4", smt: "Medium" };
      default: return { name: "알 수 없음", size: "-", substrate: "-", smt: "-" };
    }
  };

  // API 데이터를 컴포넌트에서 사용할 형태로 변환
  const processApiData = (apiData: PCBInspectionData[]): PCBData[] => {
    if (!apiData || !Array.isArray(apiData)) return [];
    
    // PCB ID별로 그룹화
    const groupedData: { [key: string]: PCBInspectionData[] } = {};
    apiData.forEach(item => {
      if (!groupedData[item.pcb_id]) {
        groupedData[item.pcb_id] = [];
      }
      groupedData[item.pcb_id].push(item);
    });

    // PCB데이터 정의
    return Object.entries(groupedData).map(([pcbId, inspections]): PCBData => {
      const defectInspections = inspections.filter(inspection => inspection.status === "불합격");
      const totalInspections = inspections.length;
      const defectCount = defectInspections.length;
      const defectRate = totalInspections > 0 ? ((defectCount / totalInspections) * 100) : 0;
      
      // 모든 불량 정보를 수집 (defect_result 배열에서)
      const allDefects: Array<{
        id: number;
        type: string;
        confidence: number;
        x1: number;
        y1: number;
        x2: number;
        y2: number;
        width: number;
        height: number;
      }> = [];

      defectInspections.forEach(inspection => {
        console.log(`Processing inspection ${inspection.id} for PCB ${pcbId}:`, inspection.defect_result);
        if (inspection.defect_result && Array.isArray(inspection.defect_result)) {
          inspection.defect_result.forEach(defect => {
            const normalizedType = normalizeDefectType(defect.label);
            console.log(`Defect ${defect.id}: original label="${defect.label}", normalized="${normalizedType}"`);
            allDefects.push({
              id: defect.id,
              type: normalizedType || defect.label || "기타",
              confidence: Math.round(defect.score * 100),
              x1: defect.x1,
              y1: defect.y1,
              x2: defect.x2,
              y2: defect.y2,
              width: defect.width,
              height: defect.height
            });
          });
        }
      });

      console.log(`Total defects found for PCB ${pcbId}:`, allDefects.length, allDefects);

      // 결함 타입별 통계
      const defectTypeCounts: { [key: string]: number } = {};
      allDefects.forEach(defect => {
        defectTypeCounts[defect.type] = (defectTypeCounts[defect.type] || 0) + 1;
      });

      console.log(`Defect type counts for PCB ${pcbId}:`, defectTypeCounts);

      let defectTypes = Object.entries(defectTypeCounts).map(([type, count]) => {
        const percentage = allDefects.length > 0 ? (count / allDefects.length) * 100 : 0;
        return {
          type,
          count,
          percentage: Math.round(percentage * 100) / 100, // 소수점 2자리까지 정확히 계산
          color: defectTypeColors[type] || defectTypeColors["기타"]
        };
      });

      // 총 불량 수와 개별 불량 수의 합계 검증
      const totalCountFromTypes = defectTypes.reduce((sum, type) => sum + type.count, 0);
      const totalPercentageFromTypes = defectTypes.reduce((sum, type) => sum + type.percentage, 0);
      
      console.log(`PCB ${pcbId} verification:`);
      console.log(`- Total defects: ${allDefects.length}`);
      console.log(`- Sum of individual counts: ${totalCountFromTypes}`);
      console.log(`- Sum of percentages: ${totalPercentageFromTypes.toFixed(2)}%`);
      console.log(`- Difference in count: ${allDefects.length - totalCountFromTypes}`);
      console.log(`- Difference in percentage: ${(100 - totalPercentageFromTypes).toFixed(2)}%`);
      
      // 누락된 불량이 있으면 "기타" 카테고리로 추가
      if (totalCountFromTypes < allDefects.length) {
        const missingCount = allDefects.length - totalCountFromTypes;
        const missingPercentage = Math.round((missingCount / allDefects.length) * 100 * 100) / 100;
        
        console.log(`Adding missing defects to "기타" category: ${missingCount} defects (${missingPercentage}%)`);
        
        defectTypes.push({
          type: "기타",
          count: missingCount,
          percentage: missingPercentage,
          color: defectTypeColors["기타"]
        });
      }
      
      if (totalCountFromTypes !== allDefects.length) {
        console.warn(`⚠️ Count mismatch for PCB ${pcbId}: total=${allDefects.length}, sum=${totalCountFromTypes}`);
      }
      if (Math.abs(totalPercentageFromTypes - 100) > 0.01) {
        console.warn(`⚠️ Percentage mismatch for PCB ${pcbId}: sum=${totalPercentageFromTypes.toFixed(2)}%`);
      }

      console.log(`Final defect types for PCB ${pcbId}:`, defectTypes);

      // 월별 데이터 (임시 - 실제로는 API에서 제공해야 함)
      const monthlyData = [
        { month: "2월", rate: 8.2 },
        { month: "3월", rate: 13.0 },
        { month: "4월", rate: 7.8 },
        { month: "5월", rate: 9.1 },
        { month: "6월", rate: 6.5 },
        { month: "7월", rate: 8.9 },
        { month: "8월", rate: 7.3 }
      ];

      const firstInspection = inspections[0];
      const pcbInfo = getPCBInfo(pcbId);
      
      const defect_count = defectCount > 0 ? defectCount : 0;
      
      return {
        id: pcbId,
        pcb_id: pcbId,
        name: pcbInfo.name,
        status: defectCount > 0 ? "불합격" : "합격",
        defect_count: defect_count,
        defectRate: `${defectRate.toFixed(1)}%`,
        image: firstInspection.image_url || "/images/pcb-defect-sample.jpg",
        defects: allDefects, // 모든 불량 정보 포함
        totalDefects: allDefects.length, // 실제 불량 개수
        avgDefectRate: Number(defectRate.toFixed(1)),
        inspectionsCompleted: totalInspections,
        targetRate: 10.0, // 기본 목표값
        monthlyData,
        defectTypes,
        // PCB 상세 정보 추가
        size: pcbInfo.size,
        substrate: pcbInfo.substrate,
        smt: pcbInfo.smt
      };
    });
  };

  // API 데이터 또는 빈 배열 사용
  const pcbList = React.useMemo(() => {
    if (pcbDefectData) {
      const processedData = processApiData(pcbDefectData);
      console.log("처리된 PCB 데이터:", processedData);
      return processedData;
    }
    return [];
  }, [pcbDefectData]);

  // 검색 필터링된 PCB 리스트
  const filteredPcbList = React.useMemo(() => {
    if (!searchTerm.trim()) {
      return pcbList;
    }
    
    const searchLower = searchTerm.toLowerCase();
    return pcbList.filter(pcb => 
      pcb.pcb_id.toLowerCase().includes(searchLower) ||
      pcb.name.toLowerCase().includes(searchLower)
    );
  }, [pcbList, searchTerm]);

  // 로딩 상태
  const isLoading = pcbDefectData === null;



  // API 데이터 기반 기본 통계 계산
  const defaultData = React.useMemo(() => {
    if (!pcbList || pcbList.length === 0) {
      return {
        totalDefects: 0,
        defect_count: 0,
        avgDefectRate: 0,
        inspectionsCompleted: 0,
        targetRate: 10, // 목표율을 10%로 설정
        monthlyData: [],
        defectTypes: [],
      };
    }

    const totalDefects = pcbList.reduce((sum, pcb) => sum + (pcb.totalDefects || 0), 0);
    const totalDefectCount = pcbList.reduce((sum, pcb) => sum + (pcb.defect_count || 0), 0);
    const totalInspections = pcbList.reduce((sum, pcb) => sum + (pcb.inspectionsCompleted || 0), 0);
    const avgDefectRate = pcbList.length > 0 
      ? pcbList.reduce((sum, pcb) => sum + (pcb.avgDefectRate || 0), 0) / pcbList.length 
      : 0;
    const avgTargetRate = 10; // 목표율을 10%로 고정

    return {
      totalDefects,
      defect_count: totalDefectCount,
      avgDefectRate: Number(avgDefectRate.toFixed(1)),
      inspectionsCompleted: totalInspections,
      targetRate: avgTargetRate,
      monthlyData: pcbList[0]?.monthlyData || [],
      defectTypes: pcbList[0]?.defectTypes || [],
      // 기본값으로 설정
      size: "-",
      substrate: "-",
      smt: "-"
    };
  }, [pcbList]);

  // 현재 표시할 데이터 (선택된 PCB가 있으면 해당 데이터, 없으면 기본 데이터)
  const currentData = selectedPCB || defaultData;

  // 불량률 기준 알림 로직
  const defectRateAlerts = React.useMemo(() => {
    if (!pcbList || pcbList.length === 0) return [];

    return pcbList
      .map(pcb => {
        const currentRate = pcb.avgDefectRate;
        
        // 심각도 분류 (불량률 기준)
        let severity: "high" | "medium" | "low";
        if (currentRate >= 15.0) {
          severity = "high";  // 15% 이상: 빨간불
        } else if (currentRate >= 10.0) {
          severity = "medium";  // 10% 이상: 주황불
        } else {
          severity = "low";  // 그 밑: 파란불
        }
        
        return {
          id: pcb.pcb_id,
          name: pcb.name,
          defectRate: currentRate,
          severity,
          pcbData: pcb
        };
      })
      .sort((a, b) => b.defectRate - a.defectRate) // 불량률 기준 내림차순 정렬
      .slice(0, 6); // 상위 6개만 표시
  }, [pcbList]);

  const handlePCBClick = (pcb: PCBData) => {
    setSelectedPCB(pcb);
    setShowPopup(true);
  };

  const handleDetailView = (pcb: PCBData) => {
    setSelectedPCB(pcb);
    setShowPopup(true);
    
    // 선택된 PCB의 모든 이미지와 불량 데이터 수집
    if (pcbDefectData) {
      const pcbInspections = pcbDefectData.filter(inspection => inspection.pcb_id === pcb.pcb_id);
      const imagesWithDefects = pcbInspections.map(inspection => ({
        image: inspection.image_url,
        pcbId: inspection.pcb_id,
        defects: inspection.defect_result || []
      }));
      setCurrentPCBImages(imagesWithDefects);
      setCurrentImageIndex(0);
      setImageLoaded(false);
    }
  };

  // 이메일 발송 기능
  const [emailStatus, setEmailStatus] = React.useState<{ success: boolean; message: string; ai_generated?: boolean } | null>(null);

  const handleSendEmail = async (pcb?: PCBData) => {
    try {
      setEmailStatus(null);
      
            const res = await fetch("http://43.201.249.204:5000/api/send-email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
              pcbData: pcb ? {
                name: pcb.name,
                id: pcb.id,
                defectRate: pcb.defectRate,
                totalDefects: pcb.totalDefects,
                avgDefectRate: pcb.avgDefectRate,
                totalInspections: pcb.totalInspections || Math.round(pcb.totalDefects / (parseFloat(pcb.defectRate.replace('%', '')) / 100)),
                confidence: pcb.confidence || 95, // 기본 신뢰도 95%
                completionRate: pcb.completionRate || 100, // 기본 완료율 100%
                qualityGrade: pcb.qualityGrade || (parseFloat(pcb.defectRate.replace('%', '')) < 5 ? 'A' : parseFloat(pcb.defectRate.replace('%', '')) < 10 ? 'B' : parseFloat(pcb.defectRate.replace('%', '')) < 20 ? 'C' : 'D')
          } : null
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setEmailStatus({ 
          success: true, 
          message: data.message || "이메일 발송 성공!",
          ai_generated: data.ai_generated || false
        });
      } else {
        setEmailStatus({ success: false, message: data.error || "이메일 발송 실패" });
      }
    } catch (err) {
      console.error("이메일 발송 오류:", err);
      setEmailStatus({ success: false, message: "서버 오류로 메일을 보내지 못했습니다." });
    }
  };



  // 로딩 상태 UI
  if (isLoading) {
    return (
      <div className="space-y-6">


        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-white text-lg">PCB 불량 데이터를 가져오는 중...</p>
            <p className="text-gray-400 text-sm mt-2">잠시만 기다려주세요</p>
          </div>
        </div>
      </div>
    );
  }

  // 데이터가 없을 때 UI
  if (!pcbList || pcbList.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">PCB 불량품 관리</h1>
            </div>
          </div>

        </div>

        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <AlertTriangle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
            <p className="text-white text-lg">PCB 불량 데이터가 없습니다</p>
            <p className="text-gray-400 text-sm mt-2">API 서버에서 데이터를 가져올 수 없습니다</p>
            <Button 
              onClick={() => window.location.reload()} 
              className="mt-4 bg-blue-500 hover:bg-blue-600"
            >
              새로고침
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-red-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">PCB 불량품 관리</h1>
          </div>
        </div>
      </div>


      {/* 추가 통계 카드들 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* 기판별 불량 기판 개수 (Top 3) */}
        <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
          <CardHeader>
            <CardTitle className="text-white text-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-blue-400" />
              기판별 불량 기판 개수 (Top 3)
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="space-y-5">
              {pcbList
                .sort((a, b) => b.defect_count - a.defect_count)
                .slice(0, 3)
                .map((pcb, index) => {
                  const maxDefectCount = Math.max(...pcbList.map(p => p.defect_count));
                  const percentage = maxDefectCount > 0 ? (pcb.defect_count / maxDefectCount) * 100 : 0;
                  
                  return (
                    <div key={pcb.id} className="space-y-3 p-3 bg-[#0D1117]/20 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center text-base font-bold ${
                            index === 0 ? 'bg-blue-500/20 text-blue-400' :
                            index === 1 ? 'bg-blue-400/20 text-blue-300' :
                            'bg-blue-300/20 text-blue-200'
                          }`}>
                            {index + 1}
                          </div>
                          <div>
                            <p className="text-white font-semibold text-base leading-tight">{pcb.name}</p>
                            <p className="text-gray-400 text-sm leading-tight">PCB{pcb.id}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`font-bold text-lg leading-tight ${
                            pcb.defect_count >= 15 ? 'text-red-400' :
                            pcb.defect_count >= 10 ? 'text-orange-400' :
                            pcb.defect_count >= 5 ? 'text-yellow-400' :
                            pcb.defect_count >= 2 ? 'text-blue-400' :
                            'text-green-400'
                          }`}>{pcb.defect_count}개</p>
                          <p className={`text-sm leading-tight ${
                            pcb.defect_count >= 15 ? 'text-red-300' :
                            pcb.defect_count >= 10 ? 'text-orange-300' :
                            pcb.defect_count >= 5 ? 'text-yellow-300' :
                            pcb.defect_count >= 2 ? 'text-blue-300' :
                            'text-green-300'
                          }`}>{pcb.defectRate}</p>
                        </div>
                      </div>
                      
                      {/* 수평 막대 그래프 */}
                      <div className="w-full bg-[#0D1117]/50 rounded-full h-3 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-1000 ease-out ${
                            index === 0 ? 'bg-gradient-to-r from-blue-500 to-blue-600' :
                            index === 1 ? 'bg-gradient-to-r from-blue-300 to-blue-400' :
                            'bg-gradient-to-r from-blue-200 to-blue-300'
                          }`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </CardContent>
        </Card>

        {/* 일별 불량률 추이 미니 차트 */}
        <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
          <CardHeader>
            <CardTitle className="text-white text-lg flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              일별 불량률 추이
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="space-y-5">
              <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
                <span>최근 7일</span>
                <span>목표: {currentData.targetRate}%</span>
              </div>
              
                             {/* 일별 더미 데이터 */}
               {(() => {
                 const dailyData = [
                   { day: '월', rate: 0.5 },
                   { day: '화', rate: 6.8 },
                   { day: '수', rate: 0.2 },
                   { day: '목', rate: 8.5 },
                   { day: '금', rate: 1.9 },
                   { day: '토', rate: 7.2 },
                   { day: '일', rate: 0.8 }
                 ];
                 
                 return (
                   <>
                  {/* 스파크라인 차트 */}
                 <div className="relative h-44 bg-[#0D1117]/30 rounded-lg p-4">
                   <svg width="100%" height="100%" className="absolute inset-0">
                     {/* 목표선 */}
                     <line 
                       x1="0" y1={`${44 - (currentData.targetRate * 1.2)}%`} 
                       x2="100%" y2={`${44 - (currentData.targetRate * 1.2)}%`} 
                       stroke="#374151" strokeWidth="2" strokeDasharray="5,5"
                     />
                     
                     {/* 데이터 포인트와 라인 */}
                     {dailyData.map((data, index) => {
                       let x = (index / (dailyData.length - 1)) * 100;
                       // 첫 번째 데이터 포인트는 +10%, 마지막 데이터 포인트는 -10% 조정
                       if (index === 0) {
                         x = Math.min(x + 4, 100);
                       } else if (index === dailyData.length - 1) {
                         x = Math.max(x - 4, 0);
                       }
                       const y = 65 - (data.rate * 3.5);
                       const nextData = dailyData[index + 1];
                       
                       if (nextData) {
                         let nextX = ((index + 1) / (dailyData.length - 1)) * 100;
                         // 다음 데이터 포인트도 조정 (마지막 데이터 포인트인 경우)
                         if (index + 1 === dailyData.length - 1) {
                           nextX = Math.max(nextX - 4, 0);
                         }
                         const nextY = 65 - (nextData.rate * 3.5);
                         
                         return (
                           <g key={index}>
                             <line 
                               x1={`${x}%`} y1={`${y}%`} 
                               x2={`${nextX}%`} y2={`${nextY}%`} 
                               stroke={data.rate > currentData.targetRate ? "#f59e0b" : "#10b981"} 
                               strokeWidth="3"
                             />
                             <circle 
                               cx={`${x}%`} cy={`${y}%`} r="4" 
                               fill={data.rate > currentData.targetRate ? "#f59e0b" : "#10b981"}
                             />
                             {/* 값 표시 - 월요일과 일요일 잘림 방지 */}
                             <text 
                               x={`${x}%`} y={`${Math.max(y - 12, 12)}%`} 
                               textAnchor="middle" 
                               className="text-xs font-medium"
                               fill={data.rate > currentData.targetRate ? "#f59e0b" : "#10b981"}
                             >
                               {data.rate}%
                             </text>
                           </g>
                         );
                       }
                       return (
                         <g key={index}>
                           <circle 
                             cx={`${x}%`} cy={`${y}%`} r="4" 
                             fill={data.rate > currentData.targetRate ? "#f59e0b" : "#10b981"}
                           />
                           {/* 값 표시 - 월요일과 일요일 잘림 방지 */}
                           <text 
                             x={`${x}%`} y={`${Math.max(y - 12, 12)}%`} 
                             textAnchor="middle" 
                             className="text-xs font-medium"
                             fill={data.rate > currentData.targetRate ? "#f59e0b" : "#10b981"}
                           >
                             {data.rate}%
                           </text>
                         </g>
                       );
                     })}
                   </svg>
                       
                       {/* 일별 라벨 */}
                       <div className="absolute bottom-0 left-2 right-2 flex justify-between text-sm text-gray-400">
                         {dailyData.map((data, index) => (
                           <span key={index}>{data.day}</span>
                         ))}
                       </div>
                     </div>
                    
                    {/* 통계 요약 */}
                    <div className="grid grid-cols-3 gap-4 text-center p-3 bg-[#0D1117]/20 rounded-lg">
                      <div>
                        <p className="text-gray-400 text-sm mb-1">최고</p>
                        <p className="text-red-400 font-bold text-lg">{Math.max(...dailyData.map(d => d.rate))}%</p>
                      </div>
                      <div>
                        <p className="text-gray-400 text-sm mb-1">평균</p>
                        <p className="text-blue-400 font-bold text-lg">{(dailyData.reduce((sum, d) => sum + d.rate, 0) / dailyData.length).toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-gray-400 text-sm mb-1">최저</p>
                        <p className="text-green-400 font-bold text-lg">{Math.min(...dailyData.map(d => d.rate))}%</p>
                      </div>
                    </div>
                  </>
                );
              })()}
            </div>
          </CardContent>
        </Card>

        {/* 불량률 상태 알림 */}
        <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] hover:shadow-lg transition-all duration-300">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-400" />
                <CardTitle className="text-white text-lg font-medium">
                  불량률 상태 알림
                  {defectRateAlerts.length > 0 && (
                    <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-xs ml-2">
                      {defectRateAlerts.length}건
                    </Badge>
                  )}
                </CardTitle>
              </div>
              
              {/* 불량률 기준 - 제목 오른쪽으로 이동 */}
              <div className="flex items-center gap-3 text-xs">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                  <span className="text-gray-300">위험</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-amber-400 rounded-full"></div>
                  <span className="text-gray-300">주의</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span className="text-gray-300">양호</span>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="space-y-4 max-h-72 overflow-y-auto overflow-x-hidden [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-[#0D1117]/30 [&::-webkit-scrollbar-thumb]:bg-[#374151]/50 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-[#4B5563]/70 [&::-webkit-scrollbar-thumb]:transition-all [&::-webkit-scrollbar-thumb]:duration-300">
              {defectRateAlerts.length > 0 ? (
                defectRateAlerts.slice(0, 3).map((item, index) => (
                  <div
                    key={item.id}
                    className={`flex items-center justify-between p-4 rounded-lg border transition-all duration-200 hover:scale-[1.02] cursor-pointer ${
                      item.severity === "high"
                        ? "bg-red-500/10 border-red-500/30 hover:bg-red-500/20"
                        : item.severity === "medium"
                          ? "bg-amber-500/10 border-amber-500/30 hover:bg-amber-500/20"
                          : "bg-blue-500/10 border-blue-500/30 hover:bg-blue-500/20"
                    }`}
                    onClick={() => handleDetailView(item.pcbData)}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-4 h-4 rounded-full ${
                          item.severity === "high"
                            ? "bg-red-400"
                            : item.severity === "medium"
                              ? "bg-amber-400"
                              : "bg-blue-400"
                        }`}
                      />
                      <div>
                        <p className="text-white font-semibold text-base">{item.name}</p>
                        <div className="flex items-center gap-2">
                          <p className="text-gray-400 text-sm">PCB{item.id}</p>
                        </div>
                        <p className="text-gray-400 text-sm">
                          현재 불량률: {item.defectRate.toFixed(1)}%
                        </p>
                        <p className="text-gray-400 text-sm">
                          불량률 목표: {item.pcbData.targetRate}% 
                          {item.defectRate > item.pcbData.targetRate && (
                            <span className="text-red-400 ml-1">
                              (초과 +{(item.defectRate - item.pcbData.targetRate).toFixed(1)}%p)
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-bold text-lg ${
                          item.severity === "high"
                            ? "text-red-400"
                            : item.severity === "medium"
                              ? "text-amber-400"
                              : "text-blue-400"
                        }`}
                      >
                        {item.defectRate.toFixed(1)}%
                      </span>
                      <AlertCircle className={`w-5 h-5 ${
                        item.severity === "high"
                          ? "text-red-400"
                          : item.severity === "medium"
                            ? "text-amber-400"
                            : "text-blue-400"
                      }`} />
                    </div>
                  </div>
                ))
                               ) : (
                   <div className="flex items-center justify-center h-40">
                     <div className="text-center">
                       <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mb-4 mx-auto">
                         <TrendingDown className="w-6 h-6 text-green-400" />
                       </div>
                       <p className="text-green-400 text-base font-medium">모든 PCB 양호</p>
                       <p className="text-gray-400 text-sm mt-2">안정적인 상태입니다</p>
                     </div>
                   </div>
                 )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* PCB 불량품 리스트 - 전체 너비 */}
      <Card className="bg-[#161B22]/50 backdrop-blur-sm border-[#30363D] shadow-xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <CardTitle className="text-white text-xl flex items-center gap-2">
                PCB 불량품 리스트
              </CardTitle>
            </div>

            <div className="flex items-center gap-3">
              {/* Search Input */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-4 h-4" />
                <Input
                  placeholder="PCB ID 또는 이름 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 w-56 bg-[#0D1117] border-[#30363D] text-white text-base focus:ring-2 focus:ring-blue-500/50"
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm("")}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* 검색 결과 표시 */}
          {searchTerm && (
            <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <p className="text-blue-300 text-sm">
                검색 결과: <span className="font-bold">{filteredPcbList.length}</span>개의 PCB 기판을 찾았습니다.
                {filteredPcbList.length === 0 && (
                  <span className="text-gray-400 ml-2">검색어를 변경해보세요.</span>
                )}
              </p>
            </div>
          )}
          <div className="flex gap-4 overflow-x-auto pb-4 [&::-webkit-scrollbar]:h-2 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-[#374151]/30 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-[#4B5563]/50 [&::-webkit-scrollbar-thumb]:transition-all [&::-webkit-scrollbar-thumb]:duration-300 scroll-smooth"
               onWheel={(e) => {
                 e.preventDefault();
                 const container = e.currentTarget;
                 const cardWidth = 384; // w-96 = 384px
                 const gap = 16; // gap-4 = 16px
                 
                 // 현재 스크롤 위치에서 가장 가까운 1개 단위로 스냅
                 const currentScroll = container.scrollLeft;
                 const totalCardWidth = cardWidth + gap;
                 const currentGroup = Math.round(currentScroll / totalCardWidth);
                 const targetScroll = currentGroup * totalCardWidth;
                 
                 // 스크롤 방향에 따라 다음/이전 카드로 이동
                 const newTargetScroll = e.deltaY > 0 
                   ? targetScroll + totalCardWidth
                   : targetScroll - totalCardWidth;
                 
                 // 최대 스크롤 범위 제한
                 const maxScroll = container.scrollWidth - container.clientWidth;
                 const clampedScroll = Math.max(0, Math.min(newTargetScroll, maxScroll));
                 
                 container.scrollTo({
                   left: clampedScroll,
                   behavior: 'smooth'
                 });
               }}>
            {filteredPcbList.length === 0 ? (
              <div className="flex items-center justify-center w-full py-12">
                <div className="text-center">
                  <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-400 text-lg font-medium mb-2">검색 결과가 없습니다</p>
                  <p className="text-gray-500 text-sm">다른 검색어를 입력해보세요.</p>
                </div>
              </div>
            ) : (
              filteredPcbList.map((pcb) => (
                <Card
                  key={pcb.id}
                  className={`bg-[#0D1117]/60 border border-[#30363D] text-white hover:shadow-md transition-transform hover:scale-[1.02] flex-shrink-0 w-96 ${selectedPCB?.id === pcb.id ? 'ring-2 ring-blue-400' : ''}`}
                >
                <CardContent className="p-6 space-y-3">
                  <div className="w-full h-40 bg-[#0D1117] rounded flex items-center justify-center">
                    <img 
                      src={pcb.image} 
                      alt="defect" 
                      className="rounded w-full h-full object-cover"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        target.parentElement!.innerHTML = `
                          <div class="flex items-center justify-center w-full h-full">
                            <div class="text-center">
                              <div class="w-12 h-12 bg-[#30363D] rounded-lg flex items-center justify-center mb-2">
                                <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                </svg>
                              </div>
                              <p class="text-gray-400 text-xs">PCB 이미지</p>
                            </div>
                          </div>
                        `;
                      }}
                    />
                  </div>
                  <h3 className="font-bold text-xl">{pcb.name}</h3>
                  <p className="text-base text-gray-400">PCB{pcb.pcb_id}</p>
                  <div className="flex items-center gap-2 mb-2">
                    <p className={`font-bold text-lg ${pcb.status === "합격" ? "text-green-400" : "text-amber-400"}`}>
                      불량률: {pcb.defectRate}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 mb-2">
                    <p className="text-gray-400 text-sm">
                      불량 기판: <span className="text-red-400 font-bold">{pcb.defect_count}</span>개
                    </p>
                  </div>
                  
                  {/* PCB 상세 스펙 정보 */}
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">크기:</span>
                      <span className="text-gray-300">{pcb.size}mm</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">기판:</span>
                      <span className="text-gray-300">{pcb.substrate}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">SMT 밀도:</span>
                      <span className="text-gray-300">{pcb.smt}</span>
                    </div>
                  </div>
                  
                  {/* 세부사항 보기 버튼 */}
                  <div className="pt-2">
                    <Button
                      size="sm"
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white text-sm py-2"
                      onClick={() => handleDetailView(pcb)}
                    >
                      세부사항 보기
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
            )}
          </div>
        </CardContent>
      </Card>

      

      {/* PCB 상세 정보 팝업 모달 */}
      {showPopup && selectedPCB && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0D1117] border border-[#30363D] rounded-xl shadow-2xl w-full max-w-7xl max-h-[95vh] overflow-hidden">
            {/* 개선된 헤더 */}
            <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 p-6 border-b border-[#30363D]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                  <div className="relative">
                    <img src={selectedPCB.image} alt="PCB" className="w-20 h-20 rounded-lg object-cover border-2 border-blue-500/30" />
                    <div className="absolute -top-2 -right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs font-bold">PCB</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h2 className="text-3xl font-bold text-white">{selectedPCB.name}</h2>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full">{selectedPCB.id}</span>
                      <span className={`px-3 py-1 rounded-full font-medium ${
                        selectedPCB.avgDefectRate > selectedPCB.targetRate 
                          ? 'bg-red-500/20 text-red-300' 
                          : 'bg-green-500/20 text-green-300'
                      }`}>
                        불량률: {selectedPCB.defectRate}
                      </span>
                    </div>
                    <div className="flex items-center gap-6 text-sm text-gray-400">
                      <span>총 검사: {selectedPCB.inspectionsCompleted.toLocaleString()}개</span>
                      <span>불량 기판: {selectedPCB.defect_count}개</span>
                      <span>목표: {selectedPCB.targetRate}%</span>
                    </div>
                    <div className="flex items-center gap-6 text-sm text-gray-400 mt-1">
                      <span>크기: {selectedPCB.size}mm</span>
                      <span>기판: {selectedPCB.substrate}</span>
                      <span>SMT 밀도: {selectedPCB.smt}</span>
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-gray-400 hover:text-white hover:bg-red-500/20"
                  onClick={() => setShowPopup(false)}
                >
                  <X className="w-6 h-6" />
                </Button>
              </div>
            </div>

            {/* 개선된 내용 */}
            <div className="p-6 space-y-8 overflow-y-auto max-h-[calc(95vh-200px)] [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-[#374151]/30 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:hover:bg-[#4B5563]/50">
              
              {/* 기본 정보 요약 카드들 */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-[#161B22]/60 border border-[#30363D]">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <p className="text-gray-400 text-sm font-medium">전체 검사 PCB 기판 개수</p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-2xl font-bold text-white">{selectedPCB.inspectionsCompleted.toLocaleString()}</p>
                      <div className="flex items-center gap-2 text-xs">
                        <TrendingUp className="w-3 h-3 text-green-400" />
                        <span className="text-green-400">+8.3%</span>
                        <span className="text-gray-500">전월 대비</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#161B22]/60 border border-[#30363D]">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <p className="text-gray-400 text-sm font-medium">불량 PCB 기판 개수</p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-2xl font-bold text-red-400">{selectedPCB.defect_count}</p>
                      <div className="flex items-center gap-2 text-xs">
                        <TrendingDown className="w-3 h-3 text-green-400" />
                        <span className="text-green-400">-12.5%</span>
                        <span className="text-gray-500">전월 대비</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#161B22]/60 border border-[#30363D]">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
                      <p className="text-gray-400 text-sm font-medium">불량률</p>
                    </div>
                    <div className="space-y-2">
                      <p className={`text-2xl font-bold ${selectedPCB.avgDefectRate > selectedPCB.targetRate ? 'text-amber-400' : 'text-green-400'}`}>
                        {selectedPCB.avgDefectRate}%
                      </p>
                      <div className="flex items-center gap-2 text-xs">
                        {selectedPCB.avgDefectRate > selectedPCB.targetRate ? (
                          <AlertCircle className="w-3 h-3 text-red-400" />
                        ) : (
                          <TrendingDown className="w-3 h-3 text-green-400" />
                        )}
                        <span className={selectedPCB.avgDefectRate > selectedPCB.targetRate ? 'text-red-400' : 'text-green-400'}>
                          {selectedPCB.avgDefectRate > selectedPCB.targetRate ? '목표 초과' : '목표 달성'}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#161B22]/60 border border-[#30363D]">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <p className="text-gray-400 text-sm font-medium">신뢰도</p>
                    </div>
                    <div className="space-y-2">
                      <p className="text-2xl font-bold text-green-400">95.2%</p>
                      <div className="w-full bg-gray-700 rounded-full h-1.5">
                        <div className="bg-green-400 h-1.5 rounded-full transition-all duration-1000" style={{ width: '95.2%' }}></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* 추가 시각화 구성 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 불량 위치 히트맵 */}
                <Card className="bg-[#161B22]/60 border border-[#30363D]">
                  <CardHeader>
                    <CardTitle className="text-white text-lg font-medium flex items-center gap-2">
                      불량 위치 히트맵
                      {currentPCBImages.length > 1 && (
                        <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30 text-xs">
                          {currentImageIndex + 1} / {currentPCBImages.length}
                        </Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="relative w-full h-64 bg-[#0D1117] rounded-lg border border-[#30363D] overflow-hidden">
                      {/* 좌우 네비게이션 버튼 */}
                      {currentPCBImages.length > 1 && (
                        <>
                          <button
                            onClick={() => {
                              setCurrentImageIndex(prev => prev > 0 ? prev - 1 : currentPCBImages.length - 1);
                              setImageLoaded(false);
                            }}
                            className="absolute left-2 top-1/2 transform -translate-y-1/2 z-10 bg-black/60 hover:bg-black/80 text-white p-2 rounded-full transition-all duration-200 hover:scale-110"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                            </svg>
                          </button>
                          <button
                            onClick={() => {
                              setCurrentImageIndex(prev => prev < currentPCBImages.length - 1 ? prev + 1 : 0);
                              setImageLoaded(false);
                            }}
                            className="absolute right-2 top-1/2 transform -translate-y-1/2 z-10 bg-black/60 hover:bg-black/80 text-white p-2 rounded-full transition-all duration-200 hover:scale-110"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </button>
                        </>
                      )}
                      
                      {/* PCB 이미지 배경 */}
                      <div className="relative w-full h-full">
                        {currentPCBImages.length > 0 ? (
                          <img 
                            src={currentPCBImages[currentImageIndex]?.image} 
                            alt="PCB 기판" 
                            className="w-full h-full object-contain bg-gray-900 transition-all duration-300"
                            onLoad={() => setImageLoaded(true)}
                            onError={(e) => {
                              // 이미지 로딩 실패 시 기본 PCB 패턴으로 대체
                              const target = e.target as HTMLImageElement;
                              target.style.display = 'none';
                              const parent = target.parentElement;
                              if (parent) {
                                parent.innerHTML = `
                                  <div class="w-full h-full bg-gradient-to-br from-green-900/20 to-blue-900/20 flex items-center justify-center">
                                    <svg class="w-full h-full opacity-30" viewBox="0 0 300 200">
                                      <rect x="10" y="10" width="280" height="180" fill="none" stroke="#22c55e" stroke-width="1" rx="5"/>
                                      <g stroke="#22c55e" stroke-width="0.5" fill="none">
                                        <line x1="30" y1="30" x2="270" y2="30" />
                                        <line x1="30" y1="50" x2="270" y2="50" />
                                        <line x1="30" y1="70" x2="270" y2="70" />
                                        <line x1="30" y1="90" x2="270" y2="90" />
                                        <line x1="30" y1="110" x2="270" y2="110" />
                                        <line x1="30" y1="130" x2="270" y2="130" />
                                        <line x1="30" y1="150" x2="270" y2="150" />
                                        <line x1="30" y1="170" x2="270" y2="170" />
                                        <line x1="50" y1="20" x2="50" y2="180" />
                                        <line x1="100" y1="20" x2="100" y2="180" />
                                        <line x1="150" y1="20" x2="150" y2="180" />
                                        <line x1="200" y1="20" x2="200" y2="180" />
                                        <line x1="250" y1="20" x2="250" y2="180" />
                                      </g>
                                    </svg>
                                    <div class="absolute inset-0 flex items-center justify-center">
                                      <div class="text-center">
                                        <div class="w-12 h-12 bg-gray-600 rounded-lg flex items-center justify-center mb-2">
                                          <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                          </svg>
                                        </div>
                                        <p class="text-gray-400 text-xs">PCB 이미지</p>
                                      </div>
                                    </div>
                                  </div>
                                `;
                              }
                            }}
                          />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-br from-green-900/20 to-blue-900/20 flex items-center justify-center">
                            <div className="text-center">
                              <div className="w-12 h-12 bg-gray-600 rounded-lg flex items-center justify-center mb-2">
                                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                </svg>
                              </div>
                              <p className="text-gray-400 text-xs">PCB 이미지 없음</p>
                            </div>
                          </div>
                        )}
                        
                        {/* 현재 이미지의 불량 위치 좌표 표시 */}
                        <div className="absolute inset-0">
                          {currentPCBImages.length > 0 && currentPCBImages[currentImageIndex]?.defects?.length > 0 && imageLoaded ? (
                            currentPCBImages[currentImageIndex].defects.map((defect: any, index: number) => {
                              // 실제 이미지 요소를 참조하여 정확한 좌표 계산
                              const imageElement = document.querySelector(`img[src="${currentPCBImages[currentImageIndex]?.image}"]`) as HTMLImageElement;
                              
                              if (!imageElement || !imageElement.naturalWidth || !imageElement.naturalHeight) return null;
                              
                              // 이미지의 실제 표시 크기와 원본 크기
                              const naturalWidth = imageElement.naturalWidth;
                              const naturalHeight = imageElement.naturalHeight;
                              
                              // 컨테이너 크기 (이미지의 부모 요소)
                              const containerWidth = imageElement.parentElement?.offsetWidth || 256; // h-64 = 256px
                              const containerHeight = imageElement.parentElement?.offsetHeight || 256;
                              
                              // object-contain으로 인한 이미지 실제 표시 영역 계산
                              const scale = Math.min(containerWidth / naturalWidth, containerHeight / naturalHeight);
                              const scaledWidth = naturalWidth * scale;
                              const scaledHeight = naturalHeight * scale;
                              
                              // 이미지가 중앙에 배치되므로 여백 계산
                              const offsetX = (containerWidth - scaledWidth) / 2;
                              const offsetY = (containerHeight - scaledHeight) / 2;
                              
                              // 불량 위치를 실제 표시 좌표로 변환
                              const x1 = (defect.x1 / naturalWidth) * scaledWidth + offsetX;
                              const y1 = (defect.y1 / naturalHeight) * scaledHeight + offsetY;
                              const x2 = (defect.x2 / naturalWidth) * scaledWidth + offsetX;
                              const y2 = (defect.y2 / naturalHeight) * scaledHeight + offsetY;
                              
                              // 퍼센트로 변환
                              const xPercent = (x1 / containerWidth) * 100;
                              const yPercent = (y1 / containerHeight) * 100;
                              const widthPercent = ((x2 - x1) / containerWidth) * 100;
                              const heightPercent = ((y2 - y1) / containerHeight) * 100;
                              
                              return (
                                <div
                                  key={defect.id}
                                  className="absolute border-2 border-red-500 bg-red-500/20 animate-pulse cursor-pointer group"
                                  style={{
                                    left: `${Math.max(0, Math.min(95, xPercent))}%`,
                                    top: `${Math.max(0, Math.min(95, yPercent))}%`,
                                    width: `${Math.max(1, Math.min(30, widthPercent))}%`,
                                    height: `${Math.max(1, Math.min(30, heightPercent))}%`,
                                  }}
                                  title={`${normalizeDefectType(defect.label)} (신뢰도: ${Math.round(defect.score * 100)}%)`}
                                >
                                  {/* 불량 번호 라벨 */}
                                  <div className="absolute -top-6 -left-1 bg-red-500 text-white text-xs px-1 py-0.5 rounded font-bold">
                                    {index + 1}
                                  </div>
                                  
                                  {/* 호버 시 상세 정보 */}
                                  <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block bg-black/80 text-white text-xs p-2 rounded whitespace-nowrap z-10">
                                    <div>유형: {normalizeDefectType(defect.label)}</div>
                                    <div>신뢰도: {Math.round(defect.score * 100)}%</div>
                                    <div>위치: ({defect.x1}, {defect.y1})</div>
                                    <div>크기: {defect.width} × {defect.height}</div>
                                  </div>
                                </div>
                              );
                            })
                          ) : currentPCBImages.length > 0 ? (
                            <div className="absolute inset-0 flex items-center justify-center">
                              <div className="bg-green-500/20 border-2 border-green-500 rounded-lg p-4">
                                <p className="text-green-400 text-sm font-medium">✅ 불량 없음 (합격)</p>
                              </div>
                            </div>
                          ) : null}
                        </div>
                      </div>
                      
                      {/* 이미지 인디케이터 */}
                      {currentPCBImages.length > 1 && (
                        <div className="absolute bottom-3 left-1/2 transform -translate-x-1/2 flex gap-2">
                          {currentPCBImages.map((_, index) => (
                            <button
                              key={index}
                              onClick={() => {
                                setCurrentImageIndex(index);
                                setImageLoaded(false);
                              }}
                              className={`w-2 h-2 rounded-full transition-all duration-200 ${
                                index === currentImageIndex 
                                  ? 'bg-blue-500 scale-125' 
                                  : 'bg-gray-500 hover:bg-gray-400'
                              }`}
                            />
                          ))}
                        </div>
                      )}
                      
                      {/* 범례 */}
                      <div className="absolute bottom-3 right-3 bg-black/80 backdrop-blur-sm rounded-lg p-2">
                        <div className="text-xs text-white space-y-1">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 border border-red-500 bg-red-500/20"></div>
                            <span>불량 위치</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-red-500 text-white text-xs flex items-center justify-center font-bold rounded">1</div>
                            <span>불량 번호</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* 현재 이미지의 불량 위치 상세 목록 */}
                    <div className="mt-4 space-y-2">
                      <h4 className="text-white font-medium text-sm mb-3">
                        불량 위치 상세 정보 ({currentPCBImages.length > 0 ? currentPCBImages[currentImageIndex]?.defects?.length || 0 : 0}개)
                      </h4>
                      <div className="grid grid-cols-1 gap-2 max-h-80 overflow-y-auto [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-[#374151]/50 [&::-webkit-scrollbar-thumb]:rounded">
                        {currentPCBImages.length > 0 && currentPCBImages[currentImageIndex]?.defects?.length > 0 ? (
                          currentPCBImages[currentImageIndex].defects.map((defect: any, index: number) => (
                            <div key={defect.id} className="flex items-center justify-between p-2 bg-[#0D1117]/60 rounded border border-[#30363D] hover:border-red-500/30 transition-all">
                              <div className="flex items-center gap-3">
                                <div className="w-6 h-6 bg-red-500 text-white text-xs flex items-center justify-center font-bold rounded">
                                  {index + 1}
                                </div>
                                <div>
                                  <p className="text-white text-sm font-medium">{normalizeDefectType(defect.label)}</p>
                                  <p className="text-gray-400 text-xs">
                                    위치: ({defect.x1}, {defect.y1}) 크기: {defect.width}×{defect.height}
                                  </p>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="text-white text-sm font-bold">{Math.round(defect.score * 100)}%</p>
                                <p className="text-gray-400 text-xs">신뢰도</p>
                              </div>
                            </div>
                          ))
                        ) : currentPCBImages.length > 0 ? (
                          <div className="flex items-center justify-center p-4 bg-green-500/10 rounded border border-green-500/30">
                            <div className="text-center">
                              <p className="text-green-400 text-sm font-medium">✅ 불량이 발견되지 않았습니다</p>
                              <p className="text-gray-400 text-xs mt-1">합격 상태입니다</p>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center p-4 bg-gray-500/10 rounded border border-gray-500/30">
                            <div className="text-center">
                              <p className="text-gray-400 text-sm font-medium">이미지를 선택해주세요</p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* 불량 유형 분포 차트 (파이차트 + 막대그래프) */}
                <Card className="bg-[#161B22]/60 border border-[#30363D]">
                  <CardHeader>
                    <CardTitle className="text-white text-lg font-medium flex items-center gap-2">
                      불량 유형 분포 차트
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {/* 수직 막대그래프 */}
                      <div className="flex items-end justify-center gap-6 h-64">
                        {(() => {
                          const sortedTypes = selectedPCB.defectTypes.sort((a, b) => b.count - a.count);
                          const maxCount = Math.max(...sortedTypes.map(type => type.count));
                          console.log('Sorted types:', sortedTypes);
                          console.log('Max count:', maxCount);
                          
                          return sortedTypes.map((item, index) => {
                            // 고정 높이를 사용하여 명확한 차이를 보이도록 함
                            const heightPercent = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
                            const heightPx = maxCount > 0 ? (item.count / maxCount) * 200 : 8; // 최대 200px 높이
                            console.log(`Bar ${item.type}: count=${item.count}, maxCount=${maxCount}, height=${heightPercent}%, heightPx=${heightPx}px`);
                            
                            return (
                              <div key={item.type} className="flex flex-col items-center">
                                <div className="text-center mb-3">
                                  <div className="text-white text-lg font-bold">{item.count}</div>
                                </div>
                                <div 
                                  className="w-16 rounded-t-lg transition-all duration-1000 ease-out relative group shadow-lg"
                                  style={{
                                    height: `${heightPx}px`,
                                    backgroundColor: item.color,
                                    minHeight: '8px'
                                  }}
                                >
                                  <div className="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-black/90 text-white text-xs px-3 py-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                                    {item.type}
                                  </div>
                                </div>
                                <div className="text-gray-300 text-sm mt-3 text-center max-w-20 font-medium">
                                  {item.type}
                                </div>
                              </div>
                            );
                          });
                        })()}
                      </div>
                      
                      {/* 총 불량 표시 */}
                      <div className="text-center">
                        <div className="text-2xl font-bold text-white">{selectedPCB.totalDefects}</div>
                        <div className="text-sm text-gray-400">총 불량</div>
                      </div>
                      
                      {/* 수평 막대그래프 */}
                      <div className="space-y-3">
                        {selectedPCB.defectTypes
                          .sort((a, b) => b.count - a.count) // 불량 개수 기준으로 내림차순 정렬
                          .map((item) => (
                          <div key={item.type} className="space-y-2">
                            <div className="flex justify-between items-center">
                              <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                                <span className="text-gray-300 text-sm font-medium">{item.type}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-white text-sm font-bold">{item.count}개</span>
                              </div>
                            </div>
                            <div className="w-full bg-[#0D1117] rounded-full h-2 overflow-hidden">
                              <div
                                className="h-full rounded-full transition-all duration-1000 ease-out"
                                style={{
                                  width: `${item.percentage}%`,
                                  backgroundColor: item.color,
                                }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* 불량률 트렌드 (전체 너비) */}
              <div className="grid grid-cols-1 gap-6">
                {/* 불량률 트렌드 */}
                <Card className="bg-[#161B22]/60 border border-[#30363D]">
                  <CardHeader>
                    <CardTitle className="text-white text-lg font-medium flex items-center gap-2">
                      불량률 트렌드 (월별)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {/* 개선된 불량률 트렌드 차트 */}
                      <div className="h-96 w-full relative bg-[#0D1117] rounded-lg p-4">
                        <svg viewBox="0 0 500 240" className="w-full h-full">
                          <defs>
                            <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.3"/>
                              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.05"/>
                            </linearGradient>
                            <filter id="glow">
                              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                              <feMerge> 
                                <feMergeNode in="coloredBlur"/>
                                <feMergeNode in="SourceGraphic"/>
                              </feMerge>
                            </filter>
                          </defs>
                          
                          {/* 그리드 라인 */}
                          <g stroke="#374151" strokeWidth="0.5" opacity="0.3">
                            {[40, 80, 120, 160, 200].map(y => (
                              <line key={y} x1="110" y1={y} x2="460" y2={y} />
                            ))}
                            {selectedPCB.monthlyData.map((_, i) => {
                              const x = 110 + (i * 350) / (selectedPCB.monthlyData.length - 1);
                              return <line key={i} x1={x} y1="40" x2={x} y2="200" />;
                            })}
                          </g>
                          
                          {/* Y축 레이블 */}
                          {[0, 5, 10, 15, 20].map((value, i) => (
                            <text
                              key={value}
                              x="95"
                              y={200 - (i * 40)}
                              fontSize="14"
                              fill="#9ca3af"
                              textAnchor="end"
                              alignmentBaseline="middle"
                              fontWeight="500"
                            >
                              {value}%
                            </text>
                          ))}
                          
                          {/* 목표선 */}
                          <line
                            x1="110"
                            y1={200 - (selectedPCB.targetRate * 8)}
                            x2="460"
                            y2={200 - (selectedPCB.targetRate * 8)}
                            stroke="#10b981"
                            strokeWidth="2"
                            strokeDasharray="8,4"
                            opacity="0.8"
                          />
                          
                          {/* 면적 차트 */}
                          <path
                            d={`M 110,200 ${selectedPCB.monthlyData.map((data, i) => {
                              const x = 110 + (i * 350) / (selectedPCB.monthlyData.length - 1);
                              const y = 200 - (data.rate * 8);
                              return `L ${x},${y}`;
                            }).join(' ')} L 460,200 Z`}
                            fill="url(#areaGradient)"
                          />
                          
                          {/* 불량률 라인 */}
                          <path
                            d={selectedPCB.monthlyData.map((data, i) => {
                              const x = 110 + (i * 350) / (selectedPCB.monthlyData.length - 1);
                              const y = 200 - (data.rate * 8);
                              return `${i === 0 ? 'M' : 'L'} ${x},${y}`;
                            }).join(' ')}
                            fill="none"
                            stroke="#f59e0b"
                            strokeWidth="3"
                            filter="url(#glow)"
                          />
                          
                          {/* 데이터 포인트 */}
                          {selectedPCB.monthlyData.map((data, i) => {
                            const x = 110 + (i * 350) / (selectedPCB.monthlyData.length - 1);
                            const y = 200 - (data.rate * 8);
                            const isAboveTarget = data.rate > selectedPCB.targetRate;
                            
                            return (
                              <g key={i}>
                                <circle
                                  cx={x}
                                  cy={y}
                                  r="4"
                                  fill={isAboveTarget ? "#ef4444" : "#10b981"}
                                  stroke="#ffffff"
                                  strokeWidth="2"
                                />
                                <text
                                  x={x}
                                  y={y - 15}
                                  fontSize="11"
                                  fill="#ffffff"
                                  textAnchor="middle"
                                  className="font-bold"
                                >
                                  {data.rate}%
                                </text>
                              </g>
                            );
                          })}
                          
                          {/* X축 레이블 */}
                          {selectedPCB.monthlyData.map((data, i) => {
                            const x = 110 + (i * 350) / (selectedPCB.monthlyData.length - 1);
                            return (
                              <text
                                key={i}
                                x={x}
                                y="220"
                                fontSize="12"
                                fill="#9ca3af"
                                textAnchor="middle"
                                fontWeight="500"
                              >
                                {data.month}
                              </text>
                            );
                          })}
                        </svg>
                        
                        {/* 범례 */}
                        <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-sm rounded-lg p-3 space-y-2">
                          <div className="flex items-center gap-2 text-xs">
                            <div className="w-4 h-1 bg-amber-500 rounded"></div>
                            <span className="text-gray-300">실제 불량률</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            <div className="w-4 h-0.5 bg-green-500 border-dashed border-t-2 border-green-500"></div>
                            <span className="text-gray-300">목표 ({selectedPCB.targetRate}%)</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                            <span className="text-gray-300">목표 초과</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                            <span className="text-gray-300">목표 달성</span>
                          </div>
                        </div>
                      </div>
                      
                      {/* 불량률 변화 추이 통계 */}
                      <div className="grid grid-cols-4 gap-4 text-center">
                        <div>
                          <p className="text-red-400 font-bold text-lg">{Math.max(...selectedPCB.monthlyData.map(d => d.rate))}%</p>
                          <p className="text-gray-400 text-xs">최고 불량률</p>
                        </div>
                        <div>
                          <p className="text-green-400 font-bold text-lg">{Math.min(...selectedPCB.monthlyData.map(d => d.rate))}%</p>
                          <p className="text-gray-400 text-xs">최저 불량률</p>
                        </div>
                        <div>
                          <p className="text-blue-400 font-bold text-lg">{(selectedPCB.monthlyData.reduce((sum, d) => sum + d.rate, 0) / selectedPCB.monthlyData.length).toFixed(1)}%</p>
                          <p className="text-gray-400 text-xs">평균 불량률</p>
                        </div>
                        <div>
                          <p className={`font-bold text-lg ${selectedPCB.monthlyData.filter(d => d.rate > selectedPCB.targetRate).length > selectedPCB.monthlyData.length / 2 ? 'text-red-400' : 'text-green-400'}`}>
                            {selectedPCB.monthlyData.filter(d => d.rate > selectedPCB.targetRate).length}/{selectedPCB.monthlyData.length}
                          </p>
                          <p className="text-gray-400 text-xs">목표 초과 월</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

              </div>

              {/* 이메일 발송 기능 */}
              <Card className="bg-[#0D1117]/60 border border-[#30363D]">
                <CardHeader>
                  <CardTitle className="text-white text-lg font-medium">
                    📧 담당자 메일 발송
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg">
                    <p className="text-white text-sm font-medium mb-2">선택된 PCB 정보:</p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <p className="text-gray-400">모델명:</p>
                        <p className="text-gray-300">{selectedPCB.name}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">ID:</p>
                        <p className="text-gray-300">{selectedPCB.pcb_id}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">크기:</p>
                        <p className="text-gray-300">{selectedPCB.size}mm</p>
                      </div>
                      <div>
                        <p className="text-gray-400">기판:</p>
                        <p className="text-gray-300">{selectedPCB.substrate}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">불량률:</p>
                        <p className="text-gray-300">{selectedPCB.defectRate}</p>
                      </div>
                      <div>
                        <p className="text-gray-400">불량 기판:</p>
                        <p className="text-gray-300">{selectedPCB.defect_count}개</p>
                      </div>
                    </div>
                  </div>
                  <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg">
                    <p className="text-white text-sm font-medium mb-1">발송 대상:</p>
                    <p className="text-blue-400 text-sm font-medium">bigdata5us@gmail.com</p>
                  </div>
                  <Button
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-lg"
                    onClick={() => handleSendEmail(selectedPCB)}
                  >
                    메일 보내기
                  </Button>
                    {emailStatus && (
                    <div className="mt-2">
                    <p className={`text-sm ${emailStatus?.success ? "text-green-500" : "text-red-500"}`}>
                      {emailStatus?.message}
                    </p>
                      {emailStatus?.success && emailStatus?.ai_generated && (
                    <p className="text-xs text-blue-500 mt-1">
                      🤖 AI가 분석하여 작성한 전문 보고서입니다
                    </p>
                      )}
                    </div>
                    )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Menu3