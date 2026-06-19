// Konfigurasi dinamis untuk URL Base API Backend
// Jika variabel lingkungan NEXT_PUBLIC_API_URL kosong saat build,
// lakukan deteksi domain otomatis (fallback) di browser secara cerdas.
export const API_BASE_URL = 
  (process.env.NEXT_PUBLIC_API_URL && process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '')) || 
  (typeof window !== 'undefined' && (window.location.hostname === 'aideb.online' || window.location.hostname.endsWith('.aideb.online'))
    ? 'https://aideb.online/api-aideb' 
    : 'http://localhost:5003');
