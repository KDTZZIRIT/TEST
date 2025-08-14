import express from "express";
import cors from 'cors';
import userRoute from './routes/userRoute';
// 기존 import들 밑에 추가 - 박세진
import modelRoutes from './routes/model.routes';   
import healthRoutes from './routes/health.routes';
// 환경변수 로드 - 박세진
import dotenv from 'dotenv';
dotenv.config(); // 추가

const app = express();
const port = 5000;

//추가
app.use(express.json()); // JSON 파싱 미들웨어 추가
app.use(cors());
app.use('/api/user', userRoute); // 라우터 설정
app.use('/api/health', healthRoutes);  // 헬스체크 라우터(박세진)
app.use('/api/model', modelRoutes);    // 모델 예측 라우터(박세진)
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});