import express from "express";
import cors from 'cors';
import userRoute from './routes/userRoute';

const app = express();
const port = 5000;

//추가
app.use(express.json()); // JSON 파싱 미들웨어 추가
app.use(cors());
app.use('/api/user', userRoute); // 라우터 설정

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});