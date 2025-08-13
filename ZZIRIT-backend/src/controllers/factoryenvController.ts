import { Request, Response } from "express";
import { PrismaClient } from "@prisma/client";
import { Server } from "socket.io";

const prisma = new PrismaClient();

export const factoryenv = async (req: Request, res: Response) => {
    try {
        const index = Number(req.query.index ?? 0); // 0부터 시작
        if (Number.isNaN(index) || index < 0) return res.status(400).json({ error: 'invalid index' });
    
        const row = await prisma.factory_env.findMany({
          orderBy: { id: 'asc' }, // 1번, 2번, 3번... 순서대로
          skip: index,
          take: 1,
        });
    
        return res.json({
          from: 'express',
          data: row,            // [] 또는 [하나]
          index,                // 이번에 준 인덱스
        });
      } catch (error) {
        console.error('Error fetching factoryenv:', error);
        res.status(500).json({ error: 'Internal server error' });
      }
};







