import { Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { getPcbSummary } from '../utils/generatePcbSummary';
import { pcbPartsMap } from '../utils/pcbPartsInfo';
import pLimit from "p-limit";

const prisma = new PrismaClient();

export const consumeParts = async (req: Request, res: Response) => {
  try {
    const pcbArray = await getPcbSummary();

    if (!Array.isArray(pcbArray) || pcbArray.length === 0) {
      return res.status(400).json({ error: "pcb-summary returned empty or invalid result" });
    }

    const limit = pLimit(5);
    const failedParts: number[] = [];

    const partConsumptionMap = new Map<number, number>(); // ✅ partId → 총 소비량
    const pcbSummaryOutput: { pcbName: string, count: number }[] = []; // ✅ pcbName & count 목록

    for (const pcb of pcbArray) {
      const { pcbName, count } = pcb;

      if (!pcbName || typeof count !== "number" || count <= 0) {
        console.warn(`❌ Invalid pcbName or count in entry:`, pcb);
        continue;
      }

      const parts = pcbPartsMap[pcbName];
      if (!parts) {
        console.warn(`⚠️ No mapping found for pcbName: ${pcbName}`);
        continue;
      }

      pcbSummaryOutput.push({ pcbName, count }); // ✅ 기록

      // 누적 차감량 계산
      const partUsageMap = new Map<number, number>();
      for (const part of parts) {
        const totalAmount = part.amount * count;

        partUsageMap.set(part.partId, (partUsageMap.get(part.partId) || 0) + totalAmount);
        partConsumptionMap.set(part.partId, (partConsumptionMap.get(part.partId) || 0) + totalAmount);
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
          } catch (err: any) {
            console.error(`❗ 부품 ${partId} 차감 실패 (${pcbName}):`, err.message);
            failedParts.push(partId);
          }
        })
      );

      await Promise.all(tasks);
    }

    // 출력용 배열 변환
    const partSummaryOutput = Array.from(partConsumptionMap.entries()).map(([partId, consumed]) => ({
      partId,
      consumed,
    }));

    if (failedParts.length > 0) {
      return res.status(207).json({
        message: "⚠️ 일부 부품 차감 실패",
        failedParts: [...new Set(failedParts)],
        pcbSummary: pcbSummaryOutput,
        partSummary: partSummaryOutput,
      });
    }

    return res.status(200).json({
      message: "✅ PCB 소비 자동 처리 완료",
      pcbSummary: pcbSummaryOutput,
      partSummary: partSummaryOutput,
    });
  } catch (error: any) {
    console.error("❌ 소비 처리 실패:", error.message);
    return res.status(500).json({ error: "PCB 소비 중 내부 오류 발생" });
  }
};
