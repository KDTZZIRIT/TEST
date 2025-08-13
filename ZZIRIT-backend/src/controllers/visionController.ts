import { Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';
import axios from 'axios';


export const visionAI = async (req: Request, res: Response) => {

    const { pcb_id, imageUrl } = req.body;
    const prisma = new PrismaClient();
    console.log("받은 이미지 URL:", imageUrl);

    // Flask 서버로 전송
    try {
        // Flask 서버로 POST 요청 전송
        const response = await axios.post(
          "http://127.0.0.1:5000/ai/pcb",
          { pcb_id, imageUrl },  // JSON 형식으로 전송
          {
            headers: { "Content-Type": "application/json" },
          }
        );
        // console.log("Flask 응답:", response.data);

        //데이터 가공 및 통합
        interface DefectBBox {
          x1: number;
          y1: number;
          x2: number;
          y2: number;
          width: number;
          height: number;
        }
        interface DefectItem {
          label: string;
          class_index: number;
          score: number;
          bbox: DefectBBox;
        }
        interface FlaskResponseType {
          pcb_id: string;
          image_url: string;
          status: string;
          message: string;
          defect_count: number;
          max_confidence: number;
          defects: DefectItem[];
        }
        const flaskResponse = response.data as FlaskResponseType;
        // console.log(JSON.stringify(flaskResponse, null, 2));

        
        // MariaDB에 저장
        const createdResult = await prisma.vision_result.create({
          data: {
            pcb_id: flaskResponse.pcb_id,
            image_url: flaskResponse.image_url,
            status: flaskResponse.status,
            defect_count: flaskResponse.defect_count,
            max_confidence: flaskResponse.max_confidence,

            // 2. defects 배열 저장 (DefectResult 테이블에)
            defect_result: {
              create: flaskResponse.defects.map((defect) => ({
                label: defect.label,
                class_index: defect.class_index,
                score: defect.score,
                x1: defect.bbox.x1,
                y1: defect.bbox.y1,
                x2: defect.bbox.x2,
                y2: defect.bbox.y2,
                width: defect.bbox.width,
                height: defect.bbox.height,
              })),
            },
          },
        });

        console.log("저장 완료:", createdResult);
        // 비전 검사 결과 전송(프론트)
        return res.json(flaskResponse);



      } catch (err) {
        console.error("Flask 전송 실패:", err);
        return res.status(500).json({ error: "Flask 전송 실패" });
      }

    
};
