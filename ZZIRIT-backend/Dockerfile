# Dockerfile

# Node.js 베이스 이미지 사용
FROM node:20

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치 (package.json과 package-lock.json 복사)
COPY package*.json ./

# node_modules 설치 (컨테이너 내부에서)
RUN npm install

# 앱 소스 코드 복사
COPY . .

# TypeScript 컴파일 추가
RUN npm run build

# Prisma client 생성
RUN npx prisma generate

# 포트 개방 (Express 서버 포트)
EXPOSE 5000

# 서버 실행
CMD ["npm", "run", "start"]
