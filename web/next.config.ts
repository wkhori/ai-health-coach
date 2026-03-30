import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  transpilePackages: ["remotion", "@remotion/player"],
};

export default nextConfig;
