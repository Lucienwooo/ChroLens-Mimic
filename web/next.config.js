/** @type {import('next').NextConfig} */

const isProd = process.env.NODE_ENV === 'production';

const nextConfig = {
  output: 'export',
  // basePath 只在生產環境（GitHub Pages）使用
  basePath: isProd ? '/ChroLens-Mimic' : '',
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig
