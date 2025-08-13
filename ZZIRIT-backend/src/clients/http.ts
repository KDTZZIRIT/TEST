import axios from "axios";

export const http = axios.create({
  timeout: 60_000,
  maxBodyLength: 10 * 1024 * 1024,
  headers: { "Content-Type": "application/json" },
  // keep-alive
  httpAgent: new (require("http").Agent)({ keepAlive: true }),
  httpsAgent: new (require("https").Agent)({ keepAlive: true }),
});
