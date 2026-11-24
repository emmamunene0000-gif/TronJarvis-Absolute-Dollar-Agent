import type { NextConfig } from "next";

const backend = process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8080";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/api/backend/:path*", destination: `${backend}/api/:path*` },
    ];
  },
};

export default nextConfig;
