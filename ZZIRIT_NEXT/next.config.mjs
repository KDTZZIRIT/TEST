/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  experimental: {
    allowedDevOrigins: [
      'http://192.168.32.179:3001',
      'http://192.168.45.4:3000',
      'http://192.168.45.4:3001'
    ], // 외부에서 접속할 수 있도록 허용
  },
}



export default nextConfig
