import { Router } from 'express';
import { listPcbImages } from '../controllers/firebaseController';
import { visionAI } from '../controllers/visionController';
import { listPcbParts, addPart } from '../controllers/partController';
import { generatePcbSummary } from '../controllers/pcbDataController';
import { consumeParts } from '../controllers/consumeController';
import { PcbDefect } from '../controllers/pcbdefectController';
import { handleInspectionClick } from '../controllers/inspectionController';
import { factoryenv } from '../controllers/factoryenvController';





//현수 뒤져라

// 라우터 설정
const router = Router();

//정현수가 만든거
router.get('/upload', listPcbImages);
router.post('/visionAI', visionAI);
router.get('/pcb-defect', PcbDefect);
router.get('/factoryenv', factoryenv);


//김창회가 만든거
router.get('/pcb-parts', listPcbParts);
router.post('/add', addPart); 
router.get('/pcb-summary', generatePcbSummary);
router.post('/consume', consumeParts);

//검사 버튼 클릭 처리
router.post('/inspection', handleInspectionClick);

export default router;
