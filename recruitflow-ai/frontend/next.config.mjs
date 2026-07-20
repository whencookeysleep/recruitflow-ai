/** @type {import('next').NextConfig} */
const backendProxyTarget = process.env.BACKEND_PROXY_TARGET || "http://127.0.0.1:8000";

const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/backend/:path*",
        destination: `${backendProxyTarget}/:path*`,
      },
    ];
  },
};

export default nextConfig;
