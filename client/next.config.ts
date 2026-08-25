import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "10.180.5.241",
    "localhost",
    "127.0.0.1",
  ],

  async rewrites() {
    return [
      {
        source: "/api-backend/:path*",
        destination: "http://127.0.0.1:8000/:path*",
      },
    ];
  },
};

export default nextConfig;