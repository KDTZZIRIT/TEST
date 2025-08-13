const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const axios = require('axios');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
  },
});

const PORT = process.env.PORT || 3100;

app.get('/', (req, res) => {
  res.send('Socket.IO server is running');
});


io.on('connection', (socket) => {
  console.log('a user connected', socket.id);

  socket.on('factorydata', (data) => {
    console.log(' factorydata 요청 시작:', socket.id, data);
    let index = 0; // 각 소켓별 index 값
  
    // 1초 간격으로 axios 호출 & 프론트 전송
    const intervalId = setInterval(async () => {
      try {
        const res = await axios.get('http://localhost:5000/api/user/factoryenv', {
          params: { index },
          timeout: 5000,
          
        });
  
        console.log('express 응답:', res.status, res.data);
        io.emit('factorydata', { from: 'express', data: res.data });

        index += 1;

  
      } catch (err) {
        const status = err.response?.status;
        const resp = err.response?.data;
        console.error(' express 요청 실패:', err.message, status ?? '', resp ?? '');
        socket.emit('factorydata_error', { message: err.message, status, resp });
      }
    }, 1000); // 1초 간격
  

    // 필요하면 종료 로직
    socket.on('stop_factorydata', () => {
      clearInterval(intervalId);
      console.log(' 데이터 전송 종료:', socket.id);
    });

    socket.on('disconnect', (reason) => {
      clearInterval(intervalId);
      console.log('user disconnected', socket.id, 'reason:', reason);
    });
  });
});

server.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});


