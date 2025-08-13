// 부품 정보 관리 컨트롤러
// 부품 목록 조회 및 신규 부품 등록 기능을 제공

import { Request, Response } from 'express';
import { PrismaClient, Prisma } from '@prisma/client';

const prisma = new PrismaClient();

// 기판 부품 목록 조회
export const listPcbParts = async (req: Request, res: Response) => {
    try {
      const parts = await prisma.pcb_parts.findMany();
  
      const transformed = parts.map((row: typeof parts[0]) => {
        const moistureAbsorption = row.is_humidity_sensitive === true;        // 흡습여부
        const needsHumidityControl = row.needs_humidity_control === true;     // 흡습필요자재
  
        const moistureMaterials = (!moistureAbsorption && needsHumidityControl) ? "필요" : "불필요";
  
        return {
          id: row.part_id,
          partId: row.part_id,
          product: row.part_number,
          type: row.category,
          size: row.size,
          receivedDate: row.received_date,
          moistureAbsorption,
          moistureMaterials,
          actionRequired: (!moistureAbsorption && needsHumidityControl) ? "필요" : "-",
          manufacturer: row.manufacturer,
          quantity: row.quantity,
          minimumStock: row.min_stock,
          orderRequired: (row.quantity ?? 0) < (row.min_stock ?? 0) ? "필요" : "-",
        };
      });
  
      res.status(200).json(transformed);
    } catch (error) {
      console.error("🚨 부품 리스트 불러오기 실패:", error);
      res.status(500).json({ error: "부품 조회 실패" });
    }
  };


//새 부품 추가
export const addPart = async (req: Request, res: Response) => {
    try {
      const {
        product,
        type,
        size,
        receivedDate,
        moistureAbsorption,
        moistureMaterials,
        manufacturer,
        quantity,
        minimumStock,
      } = req.body;
      
      if (isNaN(Number(quantity)) || isNaN(Number(minimumStock))) {
        return res.status(400).json({
          message: "Quantity and MinimumStock must be valid numbers.",
        });
      }
  
      const newPart = await prisma.pcb_parts.create({
        data: {
          part_number: product,
          category: type,
          size: size,
          received_date: new Date(receivedDate),
          is_humidity_sensitive: moistureAbsorption,
          needs_humidity_control: moistureMaterials === "필요",
          manufacturer: manufacturer,
          quantity: Number(quantity),
          min_stock: Number(minimumStock),
        },
      });
  
      res.status(201).json({ message: 'Part added successfully.', part: newPart });
    } catch (err) {
      console.error('Error while adding part:', err);
      res.status(500).json({ message: 'Internal server error.', error: err });
    }
  };