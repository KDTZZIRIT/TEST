//검사하기 버튼 클릭하면 part_id, count 전송
//계산까지
import { Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { pcbPartsMap } from '../utils/pcbPartsInfo';
import { getPcbInfo } from '../utils/getPcbInfo';
import pLimit from "p-limit";

const prisma = new PrismaClient();

interface InspectionData {
  pcb_id: string;
  count: number;
}

export const handleInspectionClick = async (req: Request, res: Response) => {
  try {
    const { pcb_id, count }: InspectionData = req.body;

    // pcb_id에서 _ 앞의 숫자만 추출
    const extractedPcbId = pcb_id.split('_')[0];

    // 검사 정보 로깅
    console.log({ pcb_id: extractedPcbId, count });

    // 숫자 ID를 PCB 이름으로 변환
    const pcbNumber = parseInt(extractedPcbId);
    const pcbInfo = getPcbInfo(pcbNumber);
    
    if (pcbInfo.name === "알 수 없음") {
      console.warn(`⚠️ No mapping found for pcb_id: ${extractedPcbId}`);
      return res.status(400).json({ 
        success: false, 
        message: `PCB ID ${extractedPcbId}에 대한 부품 정보를 찾을 수 없습니다.` 
      });
    }

    // 부품 감소 로직
    const limit = pLimit(5);
    const failedParts: number[] = [];

    const parts = pcbPartsMap[pcbInfo.name];
    if (!parts) {
      console.warn(`⚠️ No parts found for pcbName: ${pcbInfo.name}`);
      return res.status(400).json({ 
        success: false, 
        message: `PCB ${pcbInfo.name}의 부품 정보를 찾을 수 없습니다.` 
      });
    }

    // 부품 차감량 계산
    const partUsageMap = new Map<number, number>();
    for (const part of parts) {
      const totalAmount = part.amount * count;
      partUsageMap.set(part.partId, (partUsageMap.get(part.partId) || 0) + totalAmount);
    }

    // 병렬 차감
    const tasks = Array.from(partUsageMap.entries()).map(([partId, totalAmount]) =>
      limit(async () => {
        try {
          await prisma.pcb_parts.update({
            where: { part_id: partId },
            data: {
              quantity: {
                decrement: totalAmount,
              },
            },
          });
          console.log(`✅ 부품 ${partId} 차감 완료: ${totalAmount}개`);
        } catch (err: any) {
          console.error(`❗ 부품 ${partId} 차감 실패:`, err.message);
          failedParts.push(partId);
        }
      })
    );

    await Promise.all(tasks);

    // 결과 응답
    if (failedParts.length > 0) {
      return res.status(207).json({
        success: false,
        message: "⚠️ 일부 부품 차감 실패",
        failedParts: [...new Set(failedParts)],
        pcb_id: extractedPcbId,
        pcb_name: pcbInfo.name,
        count: count
      });
    }

    return res.status(200).json({
      success: true,
      message: "✅ 부품 차감 완료",
      pcb_id: extractedPcbId,
      pcb_name: pcbInfo.name,
      count: count
    });

  } catch (error) {
    console.error('검사 처리 중 오류:', error);
    res.status(500).json({ success: false });
  }
};
