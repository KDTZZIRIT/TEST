// 기판 번호 → 기판명 매핑 유틸 함수
// 숫자형 기판 번호를 문자열 기판 이름으로 변환


export function getPcbInfo(number: number) {
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
  }