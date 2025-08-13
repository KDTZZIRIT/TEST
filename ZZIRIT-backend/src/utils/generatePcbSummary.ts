// Firebase 이미지 파일명 분석 유틸
// 업로드된 파일명을 분석해 기판 번호별 수량 요약 데이터를 생성

import axios from 'axios';
import { getPcbInfo } from './getPcbInfo';

export const getPcbSummary = async () => {
  const response = await axios.get<{ files: { name: string; url: string; }[] }>('http://localhost:5000/api/user/upload');
  const files = response.data.files;

  const pcbCountMap = new Map<number, { count: number; manufactureDate: string }>();
  const pcbUrlMap = new Map<number, string[]>();


  for (const file of files) {
    const match = file.name.match(/pcb-data\/(\d{8})\/(OK|NG)_(\d+)_/);
    const pcbNumber = match ? parseInt(match[3]) : 0;
    const manufactureDate = match ? match[1] : '';
    if (pcbNumber === 0) continue;

    const current = pcbCountMap.get(pcbNumber); // 객체 or undefined
    const count = current ? current.count + 1 : 1;
    pcbCountMap.set(pcbNumber, { count, manufactureDate });

    if (!pcbUrlMap.has(pcbNumber)) {
      pcbUrlMap.set(pcbNumber, []);
    }
    pcbUrlMap.get(pcbNumber)!.push(file.url);
  }

  const summary = Array.from(pcbCountMap.entries()).map(([pcbNumber, { count, manufactureDate }], index) => {
    const info = getPcbInfo(pcbNumber);
    const urls = pcbUrlMap.get(pcbNumber) || []; 
    return {
      // 여기는 1번만 출력
      pcbNumber,
      pcb_id: `${pcbNumber}_${index}`,
      pcbName: info.name,
      size: info.size,
      substrate: info.substrate,
      smt: info.smt,
      count,
      manufactureDate,
      // (pcbNumber 별로 이미지 url 리스트임)
      urls 
    };
  });

  // 요약 데이터 리턴
  return summary;
};
