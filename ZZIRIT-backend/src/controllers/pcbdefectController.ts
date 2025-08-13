import { Request, Response } from 'express';
import { PrismaClient, Prisma } from '@prisma/client';
import { getPcbInfo } from '../utils/getPcbInfo';


// MariaDB에서 데이터 가져와서 불량관리 대시보드로 전송
export const PcbDefect = async (req: Request, res: Response) => {

    const prisma = new PrismaClient()
    
    try {
        const defect_info = await prisma.vision_result.findMany({
            include: {
                defect_result: true
            }
        });

        console.log('Sample result:', JSON.stringify(defect_info.slice(0, 1), null, 2));

        //console.log(defect_info);
        return res.json(defect_info);
        
    } catch (error) {
        //console.log(error);
        return res.status(500).json({ error: 'Failed to fetch defect' });
    }
}


