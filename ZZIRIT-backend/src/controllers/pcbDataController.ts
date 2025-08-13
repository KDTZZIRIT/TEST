// 기판 요약 데이터 API 컨트롤러
// getPcbSummary()를 호출해 기판명/수량 데이터를 생성하고 응답으로 반환

import { Request, Response } from "express";
import { getPcbSummary } from "../utils/generatePcbSummary";  // 새로 만든 함수 import

export const generatePcbSummary = async (req: Request, res: Response) => {
  try {
    const result = await getPcbSummary();

    // 프론트 api 요청 받을 시 응답
    res.json(result);
  } catch (error) {
    console.error("PCB Summary Error:", error);
    res.status(500).json({ error: "Failed to generate PCB summary" });
  }
};