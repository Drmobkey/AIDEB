/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // Konfigurasi untuk Docker standalone build
  // basePath dan assetPrefix dihapus agar aplikasi diakses langsung pada root URL (/)
  // baik lokal (http://localhost:3000) maupun di VPS (http://<IP_VPS>:3001)
};

export default nextConfig;
