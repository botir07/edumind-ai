/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["next-intl"],
  experimental: {},
  async rewrites() {
    return []
  },
}

module.exports = nextConfig
