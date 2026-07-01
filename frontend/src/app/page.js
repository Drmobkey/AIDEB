'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, FileText, LogOut, ShieldCheck, User, FolderHeart, AlertCircle, CheckCircle, Download, X, Activity, Cpu } from 'lucide-react';
import { API_BASE_URL } from '@/config';

export default function DashboardPage() {
  const router = useRouter();

  // 1. State Keamanan & Form Pasien
  const [authorized, setAuthorized] = useState(false);
  const [noRm, setNoRm] = useState('');
  const [namaPasien, setNamaPasien] = useState('');

  // 2. State File Gambar & Previews
  const [selectedFile, setSelectedFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  // 3. State Hasil Analisis AI Backend
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  // --- PROTEKSI HALAMAN (SOP Keamanan Modul 1) ---
  useEffect(() => {
    const aidebToken = localStorage.getItem('aideb_token');
    const detujiToken = localStorage.getItem('detuji_token');
    console.log("=== AIDEB DASHBOARD PROTECT ===");
    console.log("aideb_token:", aidebToken);
    console.log("detuji_token:", detujiToken);

    const token = aidebToken || detujiToken;
    if (!token) {
      console.log("Token tidak ditemukan! Melempar kembali ke /login...");
      router.push('/login');
    } else {
      console.log("Token ditemukan! Mengizinkan akses dashboard...");
      setAuthorized(true);
    }
  }, [router]);

  // Fungsi Logout Admin
  const handleLogout = () => {
    localStorage.removeItem('aideb_token');
    localStorage.removeItem('detuji_token');
    router.push('/login');
  };

  // Handler untuk menghapus file yang dipilih
  const handleRemoveFile = () => {
    setSelectedFile(null);
    setImagePreview(null);
    setAnalysisResult(null);
    setError('');
  };

  // Handler saat user memilih file gambar dari komputer
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const allowedExtensions = ['png', 'jpg', 'jpeg', 'dcm'];
      const fileExtension = file.name.split('.').pop().toLowerCase();

      if (!allowedExtensions.includes(fileExtension)) {
        setError(`Format berkas tidak diizinkan! Hanya menerima format: ${allowedExtensions.join(', ').toUpperCase()}`);
        setSelectedFile(null);
        setImagePreview(null);
        setAnalysisResult(null);
        e.target.value = ''; // Reset input agar bisa pilih ulang file yang sama jika diinginkan
        return;
      }

      setSelectedFile(file);
      // Membuat URL temporer agar gambar bisa dipratinjau langsung di UI Next.js
      setImagePreview(URL.createObjectURL(file));
      // Reset hasil analisis lama jika user mengganti gambar baru
      setAnalysisResult(null);
      setError('');
    }
  };

  // --- SUBMIT DATA KE BACKEND FLASK ---
  const handleAnalyse = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Silakan pilih berkas gambar MRI terlebih dahulu!');
      return;
    }

    setError('');
    setLoading(true);
    setAnalysisResult(null);

    // 1. Membungkus data ke FormData
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('nama_pasien', namaPasien.trim() || 'Anonim');
    formData.append('no_rm', noRm.trim() || '-');

    try {
      const res = await fetch(`${API_BASE_URL}/api/predict`, {
        method: 'POST',
        body: formData,
      });

      const result = await res.json();

      if (res.ok) {
        const finalData = result.data ? result.data : result;

        setAnalysisResult({
          analysis_id: finalData.analysis_id || `AIDEB-${Math.random().toString(36).substr(2, 9).toUpperCase()}`,
          nama_pasien: finalData.nama_pasien || namaPasien || 'Anonim',
          no_rm: finalData.no_rm || noRm || '-',
          filename: finalData.saved_filename || finalData.filename || 'file_scan.png',
          prediction: finalData.prediction || 'Normal',
          confidence: finalData.confidence !== undefined ? finalData.confidence : 100.0,
          timestamp: finalData.timestamp || new Date().toLocaleString(),
          message: finalData.message
        });
      } else {
        setError(result.error || result.message || 'Gagal memproses gambar MRI.');
      }
    } catch (err) {
      setError('Tidak dapat terhubung dengan mesin AI di server backend.');
    } finally {
      setLoading(false);
    }
  };

  // --- UNDUH LAPORAN PDF ---
  const handleDownloadPDF = async () => {
    if (!analysisResult) return;
    setDownloadingPdf(true);

    try {
      const defaultFilename = `Hasil_Analisis_${analysisResult.no_rm}_${analysisResult.nama_pasien.replace(/ /g, '_')}.pdf`;

      const res = await fetch(`${API_BASE_URL}/api/download-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          analysis_id: analysisResult.analysis_id,
          nama_pasien: analysisResult.nama_pasien,
          no_rm: analysisResult.no_rm,
          saved_filename: analysisResult.filename, // Memastikan key sesuai blueprint route PDF
          prediction: analysisResult.prediction,
          confidence: analysisResult.confidence,
          timestamp: analysisResult.timestamp
        }),
      });

      if (res.ok) {
        const blob = await res.blob();

        // 1. Coba gunakan File System Access API (showSaveFilePicker) jika tersedia di browser
        if (typeof window !== 'undefined' && 'showSaveFilePicker' in window) {
          try {
            const fileHandle = await window.showSaveFilePicker({
              suggestedName: defaultFilename,
              types: [
                {
                  description: 'PDF Document',
                  accept: {
                    'application/pdf': ['.pdf'],
                  },
                },
              ],
            });
            const writable = await fileHandle.createWritable();
            await writable.write(blob);
            await writable.close();
            return; // Berhasil menyimpan menggunakan Dialog Simpan Bawaan OS
          } catch (err) {
            if (err.name === 'AbortError') {
              return;
            }
            console.error('showSaveFilePicker failed, falling back to standard download:', err);
          }
        }

        // 2. Fallback: Gunakan browser prompt klasik untuk merename file, lalu unduh biasa
        const customName = prompt('Simpan laporan dengan nama file:', defaultFilename);
        if (customName === null) {
          return;
        }

        let finalFilename = customName.trim();
        if (!finalFilename) {
          finalFilename = defaultFilename;
        } else if (!finalFilename.toLowerCase().endsWith('.pdf')) {
          finalFilename += '.pdf';
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = finalFilename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        alert('Gagal mengunduh dokumen laporan PDF dari server.');
      }
    } catch (err) {
      alert('Terjadi kesalahan koneksi saat mengunduh PDF.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (!authorized) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center font-sans">
        <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin mb-4" />
        <p className="text-cyan-400 text-xs font-bold tracking-widest uppercase animate-pulse">
          Memverifikasi Otorisasi Sesi...
        </p>
      </div>
    );
  }

  const isEpilepsi = analysisResult?.prediction?.toLowerCase().includes('epilepsi');
  const isLowConfidence = analysisResult?.confidence < 70;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 flex flex-col font-sans relative">

      {/* Ambient background decorations */}
      <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-light-medis/30 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="fixed bottom-0 left-0 w-[400px] h-[400px] bg-primary-medis/5 rounded-full blur-[100px] pointer-events-none z-0" />

      {/* ======================= NAVBAR UTAMA ======================= */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-slate-200/60 sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-medis to-secondary-medis flex items-center justify-center shadow-md shadow-primary-medis/15">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <span className="text-lg font-black text-dark-medis tracking-tight">
            AIDEB<span className="text-primary-medis">.AI</span>
          </span>
          <span className="text-[10px] text-slate-400 font-semibold bg-slate-50 px-2.5 py-1 rounded-md hidden md:inline border border-slate-100">
            Sistem Deteksi Epilepsi
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold px-3 py-1.5 rounded-full border border-emerald-200/80">
            <ShieldCheck className="w-3.5 h-3.5" />
            AI Model Aktif
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-[10px] font-bold text-red-500 hover:bg-red-50 px-3 py-2 rounded-xl border border-red-100 transition-all hover:shadow-sm"
          >
            <LogOut className="w-3.5 h-3.5" />
            Keluar
          </button>
        </div>
      </header>

      {/* ======================= BODY DASHBOARD ======================= */}
      <main className={`flex-1 p-5 md:p-6 w-full mx-auto relative z-10 ${analysisResult
        ? 'max-w-7xl grid grid-cols-1 lg:grid-cols-2 gap-5'
        : 'max-w-2xl'
        } items-start`}>

        {/* SISI KIRI: INPUT FORM DATA PASIEN & UNGGAH BERKAS */}
        <section className="bg-white p-6 rounded-2xl border border-slate-200/70 shadow-sm shadow-slate-100 space-y-5 animate-fade-in">
          <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-medis/10 to-secondary-medis/10 flex items-center justify-center border border-primary-medis/10">
              <FolderHeart className="w-4.5 h-4.5 text-primary-medis" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-dark-medis">Data Pasien & Citra MRI</h2>
              <p className="text-slate-400 text-[11px]">Isi formulir berikut sebelum mengeksekusi analisis komputer</p>
            </div>
          </div>

          <form onSubmit={handleAnalyse} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* No Rekam Medis */}
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5 tracking-wider">
                  Rekam Medis
                </label>
                <input
                  type="text"
                  placeholder="Contoh: RM-12345"
                  value={noRm}
                  onChange={(e) => setNoRm(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-50/80 border border-slate-200 rounded-xl text-sm text-dark-medis focus:outline-none focus:border-primary-medis focus:ring-4 focus:ring-primary-medis/8 focus:bg-white transition-all duration-300 input-depth placeholder:text-slate-400"
                />
              </div>
              {/* Nama Pasien */}
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5 tracking-wider">
                  Nama Pasien
                </label>
                <input
                  type="text"
                  placeholder="Nama Lengkap"
                  value={namaPasien}
                  onChange={(e) => setNamaPasien(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-50/80 border border-slate-200 rounded-xl text-sm text-dark-medis focus:outline-none focus:border-primary-medis focus:ring-4 focus:ring-primary-medis/8 focus:bg-white transition-all duration-300 input-depth placeholder:text-slate-400"
                />
              </div>
            </div>

            {/* AREA BOX UPLOAD GAMBAR */}
            <div>
              <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5 tracking-wider">
                Unggah Citra MRI Otak
              </label>
              <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-slate-300/70 rounded-2xl bg-gradient-to-b from-slate-50/50 to-slate-50 hover:from-primary-medis/[0.02] hover:to-secondary-medis/[0.03] hover:border-primary-medis/30 cursor-pointer group transition-all duration-300 overflow-hidden relative">

                {imagePreview ? (
                  selectedFile?.name?.toLowerCase().endsWith('.dcm') ? (
                    <div className="flex flex-col items-center justify-center p-6 text-center h-full w-full animate-fade-in">
                      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-50 to-teal-100 text-teal-600 flex items-center justify-center mb-3 border border-teal-200/80 shadow-sm">
                        <FileText className="w-7 h-7" />
                      </div>
                      <p className="text-sm font-bold text-dark-medis max-w-[90%] truncate">{selectedFile?.name}</p>
                      <p className="text-[11px] text-slate-400 mt-1">Berkas Medis DICOM (Pratinjau visual tidak didukung oleh browser)</p>
                      <p className="text-[10px] text-primary-medis bg-teal-50 border border-teal-100 px-2.5 py-1 rounded-full mt-2.5 font-bold uppercase shadow-sm">
                        Format DICOM Terdeteksi
                      </p>
                    </div>
                  ) : (
                    <picture className="animate-fade-in">
                      <img src={imagePreview} alt="Preview MRI" className="w-full h-full object-contain p-2" />
                    </picture>
                  )
                ) : (
                  <div className="flex flex-col items-center justify-center p-6 text-center">
                    <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 group-hover:bg-primary-medis/10 group-hover:text-primary-medis transition-all duration-300 mb-3 group-hover:scale-105">
                      <Upload className="w-5 h-5" />
                    </div>
                    <p className="text-sm font-bold text-dark-medis">Pilih Berkas Citra MRI</p>
                    <p className="text-[11px] text-slate-400 mt-1">Mendukung format PNG, JPG, JPEG, atau DICOM (.dcm)</p>
                  </div>
                )}
                {imagePreview && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      handleRemoveFile();
                    }}
                    className="absolute top-3 right-3 bg-red-500 hover:bg-red-600 text-white rounded-full p-1.5 transition-all z-20 shadow-md flex items-center justify-center border border-red-400 active:scale-90 hover:shadow-lg"
                    title="Hapus file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}

                {/* SCANNING OVERLAY ANIMATION */}
                {loading && (
                  <div className="absolute inset-0 bg-dark-medis/85 flex flex-col items-center justify-center z-30">
                    {/* Laser Scan Line */}
                    <div className="absolute left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_20px_#22d3ee,0_0_40px_rgba(34,211,238,0.3)] animate-scan-line" />

                    {/* Glowing Scanner Grid / Radar Effect */}
                    <div className="w-16 h-16 rounded-full border border-cyan-400/20 flex items-center justify-center animate-ping-slow mb-4 relative">
                      <div className="w-12 h-12 rounded-full border border-cyan-400/40 flex items-center justify-center animate-spin">
                        <div className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_12px_#22d3ee]" />
                      </div>
                    </div>

                    <div className="text-cyan-400 text-[10px] font-black tracking-[0.15em] uppercase flex flex-col items-center gap-1.5">
                      <span className="flex items-center gap-2 animate-pulse">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                        Memindai Citra Otak...
                      </span>
                      <span className="text-[9px] text-cyan-400/50 font-bold tracking-wider">Deep Learning AI Analysis</span>
                    </div>
                  </div>
                )}

                <input type="file" accept=".png,.jpg,.jpeg,.dcm" onChange={handleFileChange} className="hidden" />
              </label>
            </div>

            {/* Error Alert khusus internal form/server */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200/80 text-red-600 text-xs font-semibold rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            {/* Tombol trigger analisis AI */}
            <button
              type="submit"
              disabled={loading || !selectedFile}
              className="w-full py-3.5 bg-gradient-to-r from-primary-medis to-secondary-medis hover:brightness-110 active:scale-[0.99] text-white rounded-xl font-bold text-sm transition-all duration-300 transform shadow-lg shadow-primary-medis/15 disabled:opacity-40 disabled:scale-100 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Sedang Memproses Pemindaian AI...
                </>
              ) : (
                <>
                  <Cpu className="w-4 h-4" />
                  Mulai Analisis Medis
                </>
              )}
            </button>
          </form>
        </section>

        {/* SISI KANAN: PANEL HASIL DIAGNOSIS AI & UNDUH PDF */}
        {analysisResult && (
          <section className="bg-white p-6 rounded-2xl border border-slate-200/70 shadow-sm shadow-slate-100 space-y-5 min-h-[460px] flex flex-col justify-between animate-slide-in-right w-full">
            <div>
              <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-medis/10 to-secondary-medis/10 flex items-center justify-center border border-primary-medis/10">
                  <FileText className="w-4.5 h-4.5 text-primary-medis" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-dark-medis">Hasil Analisis AI</h2>
                  <p className="text-slate-400 text-[11px]">Diproses secara komputasi menggunakan arsitektur deep learning</p>
                </div>
              </div>

              {/* PANEL HASIL SCAN AI */}
              <div className="mt-5 space-y-4 animate-fade-in">

                {/* Kotak Besar Status Diagnosis Penyakit */}
                <div className={`p-5 rounded-2xl border flex flex-col items-center justify-center text-center ${isEpilepsi
                  ? 'bg-gradient-to-br from-red-50 to-red-50/50 border-red-200/70 text-red-900'
                  : 'bg-gradient-to-br from-emerald-50 to-green-50/50 border-green-200/70 text-green-900'
                  }`}>
                  <span className="text-[9px] uppercase font-black tracking-[0.15em] text-slate-400 mb-1.5">
                    Diagnosis Sementara
                  </span>
                  <div className="flex items-center gap-2.5 text-2xl font-black">
                    {isEpilepsi ? (
                      <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                        <AlertCircle className="w-5 h-5 text-red-600" />
                      </div>
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      </div>
                    )}
                    {analysisResult.prediction.toUpperCase()}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2.5 max-w-xs leading-relaxed">
                    {isEpilepsi ? (
                      <>
                        Terdeteksi adanya pola gelombang/aktivitas anomali yang mengindikasikan epilepsi pada citra MRI otak.
                        <span className="block mt-2 font-bold text-red-500 text-[10px]">
                          *Catatan: Segera konsultasikan hasil analisis ini dengan Dokter Spesialis Neurologi untuk pemeriksaan klinis lebih lanjut.
                        </span>
                      </>
                    ) : (
                      'Struktur jaringan sel dan anatomi otak normal, bersih dari indikasi epilepsi.'
                    )}
                  </p>
                </div>

                {/* AREA PERINGATAN BILA AKURASI RENDAH / MODEL AI RAGU-RAGU */}
                {isLowConfidence && (
                  <div className="p-4 bg-gradient-to-br from-amber-50 to-orange-50/50 border border-amber-200/70 text-amber-900 rounded-2xl flex flex-col items-center justify-center text-center gap-1.5">
                    <span className="text-[9px] uppercase font-black tracking-[0.15em] text-amber-600">
                      Peringatan AI Ragu-Ragu
                    </span>
                    <div className="flex items-center gap-2 text-amber-700 font-bold text-sm">
                      <AlertCircle className="w-4.5 h-4.5 shrink-0 text-amber-600" />
                      Tingkat Kepercayaan Rendah ({analysisResult.confidence.toString().replace('.', ',')}%)
                    </div>
                    <p className="text-[11px] text-amber-700/80 max-w-xs leading-relaxed">
                      {analysisResult.message || "Model AI ragu-ragu. Struktur anatomi gambar tidak dikenali sebagai MRI Otak yang valid."}
                    </p>
                  </div>
                )}

                {/* Progress Bar Akurasi Tingkat Kepercayaan */}
                {/* <div className="space-y-2 p-4 bg-slate-50/60 rounded-xl border border-slate-100">
                  <div className="flex items-center justify-between text-xs font-bold">
                    <span className="text-slate-400 uppercase tracking-wider text-[10px]">Tingkat Kepercayaan AI</span>
                    <span className="text-primary-medis text-sm font-black">{analysisResult.confidence.toString().replace('.', ',')}%</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-200/60 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full animate-progress-glow ${isLowConfidence
                        ? 'bg-gradient-to-r from-amber-400 to-amber-500'
                        : isEpilepsi
                          ? 'bg-gradient-to-r from-red-400 to-red-500'
                          : 'bg-gradient-to-r from-emerald-400 to-green-500'
                        }`}
                      style={{ width: `${analysisResult.confidence}%`, transition: 'width 1.2s cubic-bezier(0.16, 1, 0.3, 1)' }}
                    />
                  </div>
                </div> */}

                {/* Tabel Informasi Ringkasan Metadata Berkas Pasien */}
                <div className="grid grid-cols-2 gap-3 pt-1">
                  {[
                    { label: 'Nama Pasien', value: analysisResult.nama_pasien, truncate: true },
                    { label: 'No Rekam Medis', value: analysisResult.no_rm },
                    { label: 'ID Laporan Medis', value: analysisResult.analysis_id, mono: true },
                    { label: 'Waktu Analisis', value: analysisResult.timestamp },
                  ].map((item, i) => (
                    <div key={i} className="bg-slate-50/80 p-3 rounded-xl border border-slate-100 hover:border-slate-200 transition-colors">
                      <span className="block text-[9px] text-slate-400 font-bold uppercase tracking-wider">{item.label}</span>
                      <span className={`text-xs font-bold text-dark-medis block mt-0.5 ${item.truncate ? 'truncate' : ''} ${item.mono ? 'font-mono' : ''}`}>
                        {item.value}
                      </span>
                    </div>
                  ))}
                </div>

              </div>
            </div>

            {/* TOMBOL UNDUH PDF */}
            <button
              onClick={handleDownloadPDF}
              disabled={downloadingPdf}
              className="w-full py-3 bg-gradient-to-r from-dark-medis to-primary-medis hover:brightness-110 text-white rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-md shadow-dark-medis/10 disabled:opacity-50 active:scale-[0.99]"
            >
              {downloadingPdf ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Sedang Mengunduh Laporan...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Unduh Berkas Hasil Radiologi (PDF)
                </>
              )}
            </button>

          </section>
        )}
      </main>
    </div>
  );
}